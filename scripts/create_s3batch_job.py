
import sys
import uuid
import argparse
import pprint as pp

# import pydantic
import boto3
from botocore.exceptions import ClientError

s3 = boto3.resource('s3')
s3client = boto3.client('s3')
lambdaclient = boto3.client('lambda')
s3control = boto3.client('s3control')
sts = boto3.client("sts")

# Utils
def get_available_buckets():
    return [bucket.name for bucket in s3.buckets.all()]


def create_s3batch_job(acct_id, confirm=True):
    response = s3control.create_job(
        AccountId=acct_id,
        ConfirmationRequired=True,
        Description='PHI Checking Batch Job',
        Priority=123,
        ClientRequestToken=uuid.uuid1(),
        Operation={
            'LambdaInvoke': {
                'FunctionArn': 'string'
            }
        },
        Report={
            'Bucket': 'string',
            'Format': 'Report_CSV_20180820',
            'Enabled': True,
            'Prefix': 'final-reports',
            'ReportScope': 'AllTasks'
        },
        Manifest={
            'Spec': {
                'Format': 'S3BatchOperations_CSV_20180820',
                'Fields': ['Bucket', 'Key']
            },
            'Location': {
                'ObjectArn': 'string',
                'ObjectVersionId': 'string',
                'ETag': 'string'
            }
        },
        RoleArn='batch-role',
        Tags=[
            {
                'Key': 'string',
                'Value': 'string'
            },
        ]
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Helper script to create s3batch job")
    parser.add_argument('bucket_name', nargs=1, help='Bucket name')
    parser.add_argument('--manifest-file', default='manifest.csv', help='Manifest object key')
    args = parser.parse_args()

    # with open('./data.json') as file:
    #     data = json.load(file)
        # jobs: List[S3BatchJob] = [S3BatchJob(**item) for item in data]

    # Organize args
    bucket_name = args.bucket_name[0]
    manifest_file = args.manifest_file

    acct_id = sts.get_caller_identity()["Account"]

    # Check available buckets
    available_buckets = get_available_buckets()
    if bucket_name in available_buckets:
        bucketARN = f'arn:aws:s3:::{bucket_name}'
    else:
        print("Available Buckets:")
        [print(f'\t{bucket}') for bucket in available_buckets]
        sys.exit(f'No bucket found with that name: {bucket_name}')


    # Check available manifest file
    # manifest_file_obj_arn = find_available_manifest_file()
    try:
        s3_resp = s3client.head_object(Bucket=bucket_name, Key=manifest_file)
        print(s3_resp.get('ETag'))
        print(s3_resp.get('ContentType'))
        print(s3_resp.get('ContentLength'))
        print(s3_resp.get('LastModified'))
    except ClientError as e:
        sys.exit(f'{manifest_file} not found')


    # List available lambda functions
    # response = lambdaclient.list_functions()
    # available_functions = response.get('Functions')
    # for f in available_functions:
    #     print(f['FunctionName'])
    #     print(f['FunctionArn'])
    #     print(f['Role'])


"""
aws s3control create-job \
    --region us-east-1 \
    --account-id 888810830951 \
    --operation '{"LambdaInvoke": { "FunctionArn": "arn:aws:lambda:us-east-1:888810830951:function:dcc-phi-checker-DetectPHI-HgOcKvXPkc6e"}}' \
    --manifest '{"Spec":{"Format":"S3BatchOperations_CSV_20180820","Fields":["Bucket","Key"]},"Location":{"ObjectArn":"arn:aws:s3:::s3batch-dev-unmanaged/manifest_1.csv","ETag":"94df2511f90e496f66b10e17018df899"}}' \
    --report '{"Bucket":"arn:aws:s3:::s3batch-dev-unmanaged","Prefix":"final-reports", "Format":"Report_CSV_20180820","Enabled":true,"ReportScope":"AllTasks"}' \
    --priority 42 \
    --role-arn arn:aws:iam::888810830951:role/dcc-phi-checker-BatchRole-GPU8191TJ4LT \
    --client-request-token $(uuidgen) \
    --description "awscli test" \
    # --no-confirmation-required
"""
