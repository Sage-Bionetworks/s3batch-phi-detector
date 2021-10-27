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
"""
A Note on the boto3 lib:
    If your bucket is an S3 bucket, we can use the s3 client interface and
    paginate through list_objects_v2.
    If your bucket is NOT an S3 bucket (GCS bucket), the boto client will
    work expectedly with the s3 resource interface and NOT support
    pagination or list_objects_v2.
"""
# TLDR:
# Iterate through bucket items, CAN use paginate with list_objects_v2
# If google bucket, CANNOT use boto s3 paginate with list_objects_v2

# TODO: Use Content-Types
# plaintext_types = ['.txt', '.csv', '.tsv']
# image_types_1 = ['.ome.tiff', '.ome.tif', '.tif']
# image_types_2 = ['.png', '.jpg']
# other_types = ['.svs', '.story.json']  # SVS WashU H&E staining

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
pii_entity_types = [
    'ADDRESS',
    'AGE',
    'AWS_ACCESS_KEY',
    'AWS_SECRET_KEY',
    'BANK_ACCOUNT_NUMBER',
    'BANK_ROUTING',
    'CREDIT_DEBIT_CVV',
    'CREDIT_DEBIT_EXPIRY',
    'CREDIT_DEBIT_NUMBER',
    'DATE_TIME',
    'DRIVER_ID',
    'EMAIL',
    'IP_ADDRESS',
    'MAC_ADDRESS',
    'NAME',
    'PASSPORT_NUMBER',
    'PASSWORD',
    'PHONE',
    'PIN',
    'SSN',
    'URL',
    'USERNAME',
]


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


def detect_pii(session, data: str, chunk_size: int = 4096) -> List[str]:
    comprehend = session.client('comprehend')
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

    return results, (utf8len(data), len(split_data), len(results))


# Utils
def keys(session, bucket_name, bucket_type, prefix='/', delimiter='/', start_after=''):

    if bucket_type == 'aws':  # Pagination available for S3 Buckets
        s3 = session.client('s3')
        s3_paginator = s3.get_paginator('list_objects_v2')

        prefix = prefix[1:] if prefix.startswith(delimiter) else prefix
        start_after = (start_after or prefix) if prefix.endswith(delimiter) else start_after

        for page in s3_paginator.paginate(Bucket=bucket_name, Prefix=prefix, StartAfter=start_after):
            for content in page.get('Contents', ()):
                yield content['Key']

    else:  # Pagination NOT available for GCS buckets
        s3_resource = session.resource('s3', endpoint_url='https://storage.googleapis.com')
        bucket = s3_resource.Bucket(bucket_name)
        for f in bucket.objects.all():
            yield f.key


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
    parser = argparse.ArgumentParser(
        description='Generate a s3batch bucket manifest file')
    parser.add_argument('-b', '--bucket-name', required=True, help='Bucket name')
    parser.add_argument('-t', '--bucket-type', default='aws', const='aws', nargs='?', choices=['aws', 'gcs'], type=str, help='Bucket name')

    parser.add_argument('-p', '--profile', default='default', type=str, help='AWS profile to use')
    parser.add_argument('-cp', '--comprehend_profile', default='default', type=str, help='AWS profile to use for Comprehend API')
    parser.add_argument('-pr', '--prefix', default='/', help='If you do not supply a prefix, we will iterate through all bucket contents')
    parser.add_argument('-i', '--ignore-prefix', help='We will ignore keys that start with this prefix')
    parser.add_argument('-l', '--log-level', default=logging.INFO)
    return parser.parse_args()

def main():
    # Process CLI args
    args = process_args()
    bucket_name = args.bucket_name
    bucket_type = args.bucket_type
    profile = args.profile
    comprehend_profile = args.comprehend_profile
    prefix = args.prefix
    ignore_prefix = args.ignore_prefix

    # Init logger
    configure_logger(args.log_level)

    # Configure main boto3 session and a comprehend_session
    session = boto3.session.Session(profile_name=profile)
    comprehend_session = boto3.session.Session(profile_name=comprehend_profile)

    if bucket_type == 'aws':
        s3 = session.resource('s3')
    elif bucket_type == 'gcs':
        # This endpoint is urlencoding spaces into '+' signs prematurely
        s3 = session.resource('s3', endpoint_url='https://storage.googleapis.com')


    # Iterate over S3 Objects
    for key in keys(session, bucket_name, bucket_type, prefix=prefix):
        logger.info(f'Working: {bucket_name},{key}')
        s3Key = key
        s3Bucket = bucket_name


        if ignore_prefix and key.startswith(ignore_prefix):
            logger.info(f"Skipping: {s3Key}")
            continue


        try:
            if s3Key.endswith('.txt') or s3Key.endswith('.csv'):
                logger.info(f"Retrieved: {s3Bucket},{s3Key}")
                obj = s3.Object(bucket_name=s3Bucket, key=s3Key)
                data = obj.get()['Body'].read().decode('utf-8')

                # Call detect
                logger.info(f'Inspecting: {s3Key}')
                pii_entities, stats = detect_pii(comprehend_session, data)

                # Write out each line
                for entity in pii_entities:
                    result = json.dumps(entity[1])
                    print(f'{s3Bucket}\t {s3Key}\t NoTag\t {result}')

            elif s3Key.endswith('.ome.tiff') or s3Key.endswith('.ome.tif') or s3Key.endswith('.tif'):
                obj = s3.Object(bucket_name=s3Bucket, key=s3Key)
                logger.info(f"Retrieved: {s3Bucket},{s3Key}")
                logger.debug(obj)
                logger.info(f'Inspecting: {s3Key}')
                with TiffFile(S3File(obj)) as tif:
                    tags = tif.pages[0].tags
                    # Call detect per image tag
                    for tag in tags.values():
                        pii_entities, stats = detect_pii(comprehend_session, str(tag.value))
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
