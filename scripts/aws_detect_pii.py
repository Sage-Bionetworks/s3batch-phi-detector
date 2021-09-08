import sys
import argparse
import io
import logging
import json
from typing import List, Optional

from tifffile import TiffFile
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# Default logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_format = '%(asctime)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)


def configure_logger(log_level=logging.INFO):
    # StreamHandler
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    sh.setLevel(log_level)
    logger.addHandler(sh)

    # FileHanlder
    fh = logging.FileHandler('logs.log')
    fh.setFormatter(formatter)
    fh.setLevel(log_level)
    logger.addHandler(fh)



# Clients/Resources
session = boto3.Session()  # Set AWS_PROFILE=<profile_name>
s3 = session.client('s3')
s3_paginator = s3.get_paginator('list_objects_v2')
s3_resource = boto3.resource('s3')
comprehend = boto3.client('comprehend')

# AWS ALL ENTITY TYPES
entity_types = [
    'BANK_ACCOUNT_NUMBER',
    'BANK_ROUTING',
    'CREDIT_DEBIT_NUMBER',
    'CREDIT_DEBIT_CVV',
    'CREDIT_DEBIT_EXPIRY',
    'PIN',
    'EMAIL',
    'ADDRESS',
    'NAME',
    'PHONE',
    'SSN',
    'DATE_TIME',
    'PASSPORT_NUMBER',
    'DRIVER_ID',
    'URL',
    'AGE',
    'USERNAME',
    'PASSWORD',
    'AWS_ACCESS_KEY',
    'AWS_SECRET_KEY',
    'IP_ADDRESS',
    'MAC_ADDRESS',
    'LICENSE_PLATE',
    'VEHICLE_IDENTIFICATION_NUMBER',
    'UK_NATIONAL_INSURANCE_NUMBER',
    'CA_SOCIAL_INSURANCE_NUMBER',
    'US_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER',
    'UK_UNIQUE_TAXPAYER_REFERENCE_NUMBER',
    'IN_PERMANENT_ACCOUNT_NUMBER',
    'IN_NREGA',
    'INTERNATIONAL_BANK_ACCOUNT_NUMBER',
    'SWIFT_CODE',
    'UK_NATIONAL_HEALTH_SERVICE_NUMBER',
    'CA_HEALTH_NUMBER',
    'IN_AADHAAR',
    'UK_VOTER_NUMBER',
    'IN_VOTER_NUMBER',
    'ALL'
]
pii_entity_types = {
    'ADDRESS': """A physical address, such as "100 Main Street, Anytown, USA" or "Suite #12, Building 123". An address can include a street, building, location, city, state, country, county, zip, precinct, neighborhood, and more.""",
    'AGE': """An individual's age, including the quantity and unit of time. For example, in the phrase "I am 40 years old," Amazon Comprehend recognizes "40 years" as an age.""",
    'AWS_ACCESS_KEY': """A unique identifier that's associated with a secret access key; the access key ID and secret access key are used together to sign programmatic AWS requests cryptographically.""",
    'AWS_SECRET_KEY': """A unique identifier that's associated with an access key; the access key ID and secret access key are used together to sign programmatic AWS requests cryptographically.""",
    'BANK_ACCOUNT_NUMBER': """A US bank account number. These are typically between 10 - 12 digits long, but Amazon Comprehend also recognizes bank account numbers when only the last 4 digits are present.""",
    'BANK_ROUTING': """A US bank account routing number. These are typically 9 digits long, but Amazon Comprehend also recognizes routing numbers when only the last 4 digits are present.""",
    'CREDIT_DEBIT_CVV': """A 3-digit card verification code (CVV) that is present on VISA, MasterCard, and Discover credit and debit cards. In American Express credit or debit cards, it is a 4-digit numeric code.""",
    'CREDIT_DEBIT_EXPIRY': """The expiration date for a credit or debit card. This number is usually 4 digits long and formatted as month/year or MM/YY. For example, Amazon Comprehend can recognize expiration dates such as 01/21, 01/2021, and Jan 2021.""",
    'CREDIT_DEBIT_NUMBER': """The number for a credit or debit card. These numbers can vary from 13 to 16 digits in length, but Amazon Comprehend also recognizes credit or debit card numbers when only the last 4 digits are present.""",
    'DATE_TIME': """A date can include a year, month, day, day of week, or time of day. For example, Amazon Comprehend recognizes "January 19, 2020" or "11 am" as dates. Amazon Comprehend will recognize partial dates, date ranges, and date intervals. It will also recognize decades, such as "the 1990s".""",
    'DRIVER_ID': """The number assigned to a driver's license, which is an official document permitting an individual to operate one or more motorized vehicles on a public road. A driver's license number consists of alphanumeric characters.""",
    'EMAIL': """An email address, such as marymajor@email.com.""",
    'IP_ADDRESS': """An IPv4 address, such as 198.51.100.0.""",
    'MAC_ADDRESS': """A media access control (MAC) address is a unique identifier assigned to a network interface controller (NIC).""",
    'NAME': """An individual's name. This entity type does not include titles, such as Mr., Mrs., Miss, or Dr. Amazon Comprehend does not apply this entity type to names that are part of organizations or addresses. For example, Amazon Comprehend recognizes the "John Doe Organization" as an organization, and it recognizes "Jane Doe Street" as an address.""",
    'PASSPORT_NUMBER': """A US passport number. Passport numbers range from 6 - 9 alphanumeric characters.""",
    'PASSWORD': """An alphanumeric string that is used as a password, such as "*very20special#pass*".""",
    'PHONE': """A phone number. This entity type also includes fax and pager numbers.""",
    'PIN': """A 4-digit personal identification number (PIN) that allows someone to access their bank account information.""",
    'SSN': """A Social Security Number (SSN) is a 9-digit number that is issued to US citizens, permanent residents, and temporary working residents. Amazon Comprehend also recognizes Social Security Numbers when only the last 4 digits are present.""",
    'URL': """A web address, such as www.example.com.""",
    'USERNAME': """A user name that identifies an account, such as a login name, screen name, nick name, or handle.""",
}


# Utils
class S3File(io.RawIOBase):
    """https://alexwlchan.net/2019/02/working-with-large-s3-objects/"""

    def __init__(self, s3_object):
        self.s3_object = s3_object
        self.position = 0

    def __repr__(self):
        return "<%s s3_object=%r>" % (type(self).__name__, self.s3_object)

    @property
    def size(self):
        return self.s3_object.content_length

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self.position = offset
        elif whence == io.SEEK_CUR:
            self.position += offset
        elif whence == io.SEEK_END:
            self.position = self.size + offset
        else:
            raise ValueError("invalid whence (%r, should be %d, %d, %d)" % (
                whence, io.SEEK_SET, io.SEEK_CUR, io.SEEK_END
            ))

        return self.position

    def seekable(self):
        return True

    def read(self, size=-1):
        if size == -1:
            # Read to the end of the file
            range_header = "bytes=%d-" % self.position
            self.seek(offset=0, whence=io.SEEK_END)
        else:
            new_position = self.position + size

            # If we're going to read beyond the end of the object, return
            # the entire object.
            if new_position >= self.size:
                return self.read()

            range_header = "bytes=%d-%d" % (self.position, new_position - 1)
            self.seek(offset=size, whence=io.SEEK_CUR)

        return self.s3_object.get(Range=range_header)["Body"].read()

    def readable(self):
        return True


def chunk_split(data: str, chunk_size: int = 4096) -> List[str]:
    """
    This is good enough for now if everything is in English.
    Keep in mind, str position != byte_size of characters.
    TODO:
        Turn this into a generator
    Args:
        data (str): data
        chunk_size:

    Returns:
        List[str]:
    """

    chunks = []
    if utf8len(data) > chunk_size:
        for index in range(0, len(data), chunk_size):
            chunks.append(data[index:index + chunk_size])
    else:
        chunks.append(data)

    return chunks


def utf8len(s: str) -> int:
    try:
        return len(s.encode('utf-8'))
    except AttributeError as e:
        logger.debug(s, e)
        raise e


def detect_pii(data: str, chunk_size: int = 4096) -> List[str]:
    # AWS Comprehend 5000 byte limit
    CHUNK_SIZE = chunk_size
    split_data = chunk_split(data, chunk_size=CHUNK_SIZE)

    results = []
    for i, chunk in enumerate(split_data):
        pii_results = comprehend.detect_pii_entities(Text=chunk, LanguageCode='en')
        entities = pii_results.get('Entities', None)
        if not entities:
            continue

        for entity in entities:
            begin = entity['BeginOffset']
            end = entity['EndOffset']
            #e['InputStr'] = chunk
            entity['ChunkNumber'] = i
            entity['BeginTotalOffset'] = CHUNK_SIZE * i + begin
            entity['EndTotalOffset'] = CHUNK_SIZE * i + end
            entity['Result'] = chunk[begin:end]
            # print(f'Chunk:{i}\t {entity}')
            results.append(tuple((i, entity)))

    stats = {
        'data_len': utf8len(data),
        'chunk_num': len(split_data),
        'result_num': len(results)
    }

    return results, (utf8len(data), len(split_data), len(results))


# Utils
def keys(bucket_name, prefix='/', delimiter='/', start_after=''):
    prefix = prefix[1:] if prefix.startswith(delimiter) else prefix
    start_after = (start_after or prefix) if prefix.endswith(delimiter) else start_after
    for page in s3_paginator.paginate(Bucket=bucket_name, Prefix=prefix, StartAfter=start_after):
        for content in page.get('Contents', ()):
            yield content['Key']


def get_tags(s3_file, output_path):
    with TiffFile(s3_file) as tif:
        tif_tags = {}
        for pages in tif.pages:
            for tag in pages.tags.values():
                name, value = tag.name, tag.value
                tif_tags[name] = value

    with open(output_path, 'w') as f:
        json.dump(tif_tags, f)

def process_args():
    parser = argparse.ArgumentParser(description='Generate a s3batch bucket manifest file')
    parser.add_argument('bucket_name', nargs=1, help='Bucket name')
    # parser.add_argument('-o', '--outfile')
    parser.add_argument('-pr', '--prefix', default='/')
    parser.add_argument('-i', '--ignore', default='/')
    parser.add_argument('-r', '--regex', default='/')
    parser.add_argument('-l', '--log-level', default=logging.INFO)
    # parser.add_argument('-p', '--profile', default='default')
    # parser.add_argument('-arn', '--role-arn')
    # parser.add_argument('-r', '--region')  # Required for s3 style

    return parser.parse_args()


def main():
    # Process CLI args
    args = process_args()
    bucket_name = args.bucket_name[0]
    prefix = args.prefix
    # outfile = args.outfile

    # Init logger
    configure_logger(args.log_level)

    # Iterate over S3 Objects
    for key in keys(bucket_name, prefix=prefix):
        logger.info(f'Working: {bucket_name},{key}')
        s3Key = key
        s3Bucket = bucket_name

        # Use A
        plaintext_types = ['.txt', '.csv', '.tsv']
        image_types_1 = ['.ome.tiff', '.ome.tif', '.tif']
        image_types_2 = ['.png', '.jpg']
        other_types = ['.svs', '.story.json']  # SVS WashU H&E staining

        # Use Content-Types

        # Currently placing assumption on S3key names
        try:
            if s3Key.endswith('.txt') or s3Key.endswith('.csv'):
                obj = s3.get_object(Bucket=s3Bucket, Key=s3Key)
                logger.info(f"Retrieved: {s3Bucket},{s3Key}")
                data = obj['Body'].read().decode('utf-8')

                # Call detect
                logger.info(f'Inspecting: {s3Key}')
                pii_entities, stats = detect_pii(data)

                # Write out each line
                for entity in pii_entities:
                    result = json.dumps(entity[1])
                    print(f'{s3Bucket}\t {s3Key}\t NoTag\t {result}')

            elif s3Key.endswith('.ome.tiff') or s3Key.endswith('.ome.tif') or s3Key.endswith('.tif'):
                obj = s3_resource.Object(bucket_name=s3Bucket, key=s3Key)
                logger.info(f"Retrieved: {s3Bucket},{s3Key}")
                logger.debug(obj)
                logger.info(f'Inspecting: {s3Key}')
                with TiffFile(S3File(obj)) as tif:
                    tags = tif.pages[0].tags
                    # Call detect per image tag
                    for tag in tags.values():
                        pii_entities, stats = detect_pii(str(tag.value))
                        logger.info("Size/Chunks/Entities:{}".format(stats))
                        # Write out each line
                        for entity in pii_entities:
                            result = json.dumps(entity[1])
                            print(f'{s3Bucket}\t {s3Key}\t {tag.name}\t {result}')

            else:
                logger.info(f"Skipping: {s3Key}")
                continue
        except ClientError:
            logger.exception(f"Unable to retrieve {s3Bucket},{s3Key}")
            raise
        except NotImplementedError as e:
            logger.info(f'Skipping: {s3Key} due to tif NotImplementedError')


if __name__ == '__main__':
    main()
