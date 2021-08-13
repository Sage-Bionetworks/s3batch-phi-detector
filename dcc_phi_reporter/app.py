import sys
import zipfile
import io
import json
import urllib
import logging

from typing import List

from tifffile import TiffFile
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel('INFO')

result_codes = {
    'success': 'Succeeded',
    'tf': 'TemporaryFailure',
    'pf': 'PermanentFailure'
}

BYTE_MAX = 5000

# Instantiate boto client
comprehend = boto3.client('comprehend')
s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')


class S3File(io.RawIOBase):
    """
    https://alexwlchan.net/2019/02/working-with-large-s3-objects/
    """
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


def get_object(bucket, object_key):
    """
    Gets an object from a bucket.

    Usage is shown in usage_demo at the end of this module.

    :param bucket: The bucket that contains the object.
    :param object_key: The key of the object to retrieve.
    :return: The object data in bytes.
    """
    try:
        body = bucket.Object(object_key).get()['Body'].read()
        logger.info("Got object '%s' from bucket '%s'.", object_key, bucket.name)
    except ClientError:
        logger.exception(("Couldn't get object '%s' from bucket '%s'.",
                          object_key, bucket.name))
        raise
    else:
        return body


def extract_image_description(ometiff):
    with TiffFile(ometiff) as tif:
        tags = tif.pages[0].tags

    desc_tag = tags.get('ImageDescription', '')
    return desc_tag

def extract_ome_metadata():
    raise NotImplementedError

def detect_mimetype():
    # import mimetype
    raise NotImplementedError

def utf8len(s: str) -> int:
    return len(s.encode('utf-8'))


def chunk_split(data: str, chunk_size=5000) -> List[str]:
    """chunk_split.
    This is good enough for now if everything is in English. Keep in mind, str position != byte_size of characters.
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


def detect_pii(data):
    # If data byte size is greater than max text limit
    # Split data up

    # split_data = chunk_split(data, chunk_size=5000)
    split_data = chunk_split(data, chunk_size=2500)

    logger.info('Data size:{} '.format(utf8len(data)))
    logger.info('Chunks: {}'.format(len(split_data)))

    results = []
    for i, chunk in enumerate(split_data):
        pii_results = comprehend.detect_pii_entities(Text=chunk, LanguageCode='en')
        print(i, chunk)
        print(i, pii_results.get('Entities', []))
        next_entities = pii_results.get('Entities', [])
        if next_entities:
            # Offset obj BeginOffset/EngoffSet by the chunksum
            pass

        results += next_entities

    return results


def lambda_handler(event, context):
    # Job parameters from S3 Batch Operations Event
    jobId = event['job']['id']
    invocationId = event['invocationId']
    invocationSchemaVersion = event['invocationSchemaVersion']

    # AWS S3 Key, Key Version, and Bucket ARN
    taskId = event['tasks'][0]['taskId']
    s3Key = event['tasks'][0]['s3Key']
    s3VersionId = event['tasks'][0]['s3VersionId']
    s3BucketArn = event['tasks'][0]['s3BucketArn']
    s3Bucket = s3BucketArn.split(':::')[-1]

    # Get Object
    # Can read(), iter_lines(), iter_chunks(), returns byte
    try:
        if s3Key.endswith('.txt'):
            obj = s3.get_object(Bucket=s3Bucket, Key=s3Key)
            logger.info(f"Got '{s3Key}' from bucket '{s3Bucket}'")
            data = obj['Body'].read().decode('utf-8')
        elif s3Key.endswith('.ome.tiff') or s3Key.endswith('.ome.tif'):
            obj = s3_resource.Object(bucket_name=s3Bucket, key=s3Key)
            logger.info(f"Got '{s3Key}' from bucket '{s3Bucket}'")
            with TiffFile(S3File(obj)) as tif:
                tags = tif.pages[0].tags
                desc_tag = tags.get('ImageDescription', '')

            data = desc_tag.value
        # Handle .json/.story.json case
        # Handle jpg, png case
        # if data


        # sys.exit('BREAKPOINT')
    except ClientError:
        logger.exception(f"Couldn't get '{s3Key}' from '{s3Bucket}'")
        raise

    # Action
    logger.info(f'Detecting PII: {s3Key}')
    pii_entities = detect_pii(data)
    logger.info('Entities: {}'.format(len(pii_entities)))
    logger.info('PII detected:')
    for entity in pii_entities:
        print(entity)

    # Prepare results
    results = []
    # if pii_entities:
    results.append({
        "taskId": taskId,
        "resultCode": result_codes.get('success'),
        "resultString": str(pii_entities)
    })

    return {
        'invocationSchemaVersion': invocationSchemaVersion,
        'treatMissingKeyAs': result_codes.get('tf'),
        'invocationId': invocationId,
        'results': results
    }
