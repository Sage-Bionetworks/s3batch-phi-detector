import sys
import argparse
import io
import logging

import boto3
from tifffile import TiffFile
from google.cloud import storage

s3 = boto3.resource('s3')

storage_client = storage.Client()


# Default logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_format = '%(asctime)s - %(levelname)s - %(message)s'
formatter = logging.Formatter(log_format)


def configure_logger(log_level=logging.INFO):
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    logger.addHandler(handler)

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


def process_args():
    parser = argparse.ArgumentParser(description='Generate a s3batch bucket manifest file')
    parser.add_argument('bucket_name', nargs=1, help='Bucket name')
    # parser.add_argument('-o', '--outfile')
    parser.add_argument('-pr', '--prefix', default='/')
    parser.add_argument('-i', '--ignore', default='/')
    parser.add_argument('-l', '--log-level', default=logging.INFO)
    # parser.add_argument('-p', '--profile', default='default')
    # parser.add_argument('-arn', '--role-arn')
    # parser.add_argument('-r', '--region')  # Required for s3 style

    return parser.parse_args()


# import io
# google_access_key_id="GOOG1EIxxMYKEYxxMQ"
# google_access_key_secret="QifDxxMYSECRETKEYxxVU1oad1b"
# gc_bucket_name="my_gc_bucket"
def list_gcs_buckets(google_access_key_id, google_access_key_secret):
    """Lists all GCS buckets using boto3 SDK"""
    # Create a new client and do the following:
    # 1. Change the endpoint URL to use the
    #    Google Cloud Storage XML API endpoint.
    # 2. Use Cloud Storage HMAC Credentials.
    client = boto3.client(
        "s3",
        region_name="auto",
        endpoint_url="https://storage.googleapis.com",
        aws_access_key_id=google_access_key_id,
        aws_secret_access_key=google_access_key_secret,
    )

    # Call GCS to list current buckets
    response = client.list_buckets()

    # Print bucket names
    print("Buckets:")
    for bucket in response["Buckets"]:
        print(bucket["Name"])


def get_gcs_objects(google_access_key_id, google_access_key_secret,
                     gc_bucket_name):
    """Gets GCS objects using boto3 SDK"""
    client = boto3.client("s3", region_name="auto",
                          endpoint_url="https://storage.googleapis.com",
                          aws_access_key_id=google_access_key_id,
                          aws_secret_access_key=google_access_key_secret)

    # Call GCS to list objects in gc_bucket_name
    response = client.list_objects(Bucket=gc_bucket_name)

    # Print object names
    print("Objects:")
    for blob in response["Contents"]:
        print(blob)

    # object = s3.Object('my_aws_s3_bucket', 'sample-data-s3.csv')
    # f = io.BytesIO()
    # client.download_fileobj(gc_bucket_name, "sample-data.csv", f)
    # object.put(Body=f.getvalue())

# def lambda_handler(event, context):
#     get_gcs_objects(google_access_key_id,google_access_key_secret,gc_bucket_name)

def list_blobs_with_prefix(bucket_name, prefix, delimiter=None):

    blobs = storage_client.list_blobs(bucket_name, prefix=prefix, delimiter=delimiter)
    print("Blobs:")
    for blob in blobs:
        print(blob.name)
        print(blob)
        # with TiffFile(S3File(blob)) as tif:
        #     print(tif)

    if delimiter:
        print("Prefixes:")
        for prefix in blobs.prefixes:
            print(prefix)

def main():
    args = process_args()
    bucket_name = args.bucket_name[0]
    prefix = args.prefix

    # google_access_key_id
    # google_access_key_secret
    # gc_bucket_name
    # get_gcs_objects(google_access_key_id, google_access_key_secret)

    # List buckets
    buckets = storage_client.list_buckets()

    # for bucket in buckets:
    #     print(bucket.name)

    # List Blobs
    if prefix != '/':
        list_blobs_with_prefix(bucket_name, prefix)
    else:
        blobs = storage_client.list_blobs(bucket_name)
        for blob in blobs:
            print(blob.name)
            # with TiffFile(S3File(blob)) as tif:
            #     print(tif)



if __name__ == '__main__':
    main()
