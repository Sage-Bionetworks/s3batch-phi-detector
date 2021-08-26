import sys
import argparse
import boto3
from botocore.client import Config

"""
Utility script to list s3 bucket objects and produce a template manifest file. If you require manifest files over 1000 objects please consider
using S3InventoryReports which are generated natively and asyncronously for a given S3Bucket

DESCRIPTION:
    Given a bucket, generate a S3Batch compatible manifest.csv file
    consisting of each object.

    Ignore/filter from results
    User-specified:
        prefixes
        file-extensions
"""

# Config(s3={'addressing_style': 'path'})
# my_session = boto3.session.Session()
session = boto3.Session(profile_name='sandbox')

# sts = session.client('sts')
# response = sts.assume_role(
#         RoleArn="arn:aws:sts::563295687221:assumed-role/AWSReservedSSO_Developer_baa6fed639faf5e7/jason.hwee@sagebase.org",
#     RoleSessionName='random-sts-session',
#     DurationSeconds=900
# )

# s3 = boto3.resource('s3')

# s3client = session.client(
#     's3',
#     aws_access_key_id=response['Credentials']['AccessKeyId'],
#     aws_secret_access_key=response['Credentials']['SecretAccessKey'],
#     aws_session_token=response['Credentials']['SessionToken'],
# )
# s3_paginator = boto3.client('s3').get_paginator('list_objects_v2')
s3client = session.client('s3')
s3_paginator = s3client.get_paginator('list_objects_v2')


# Utils
def get_available_buckets():
    return [bucket.name for bucket in s3.buckets.all()]

# https://gist.github.com/seansummers/b2bf57deb4a44956be21fe60209bfd80
def keys(bucket_name, prefix='/', delimiter='/', start_after=''):
    prefix = prefix[1:] if prefix.startswith(delimiter) else prefix
    start_after = (start_after or prefix) if prefix.endswith(delimiter) else start_after
    for page in s3_paginator.paginate(Bucket=bucket_name, Prefix=prefix, StartAfter=start_after):
        for content in page.get('Contents', ()):
            yield content['Key']


def list_objects_client(bucket_name):
    """Via boto3.client
    Low-level, more options & reflective of awscli
    """
    response = s3client.list_objects_v2(
        Bucket=bucket_name,
        EncodingType='url',
        MaxKeys=123,
        FetchOwner=True,
        # Prefix='string',
        # ContinuationToken='string',
        # Delimiter='string',
        # StartAfter='string',
        # RequestPayer='requester',
        # ExpectedBucketOwner='string'
    )
    print(response['Contents'])
    for item in response['Contents']:
        print(item)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a s3batch bucket manifest file')
    parser.add_argument('bucket_name', nargs=1, help='Bucket name')
    # parser.add_argument('-p', '--profile', default='default')
    parser.add_argument('-pr', '--prefix', default='/')
    # parser.add_argument('-arn', '--role-arn')

    # parser.add_argument('-i', '--ignore', default='/')
    # parser.add_argument('-r', '--region')  # Required for s3 style
    args = parser.parse_args()

    # Organize Args
    bucket_name = args.bucket_name[0]
    prefix = args.prefix

    # Get available buckets
    # available_buckets = get_available_buckets()
    # if bucket_name is None or bucket_name not in available_buckets:
    #     [print(bucket) for bucket in available_buckets]
    #     sys.exit(f'No bucket found with that name: {bucket_name}')

    # List objects using boto3.resource abstraction
    # bucket = s3.Bucket(bucket_name)
    # for obj in bucket.objects.all():
    #     print(f'{bucket.name},{obj.key}')

    # Via boto3.client abstraction
    for key in keys(bucket_name, prefix=prefix):
        print(f'{bucket_name},{key}')
