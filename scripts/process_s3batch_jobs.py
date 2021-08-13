
import sys
import uuid
import argparse
import json

from typing import List, Dict, Optional
from pydantic import BaseModel

# import pydantic
import boto3
from botocore.exceptions import ClientError

s3 = boto3.resource('s3')
s3client = boto3.client('s3')
lambdaclient = boto3.client('lambda')
s3control = boto3.client('s3control')
sts = boto3.client("sts")


def create_s3batch_job_from_json(config):
    response = s3control.create_job(**config)
    print(f'jobID: {response}')


class Tag(BaseModel):
    Key: str
    Value: str


class ReportConfig(BaseModel):
    Bucket: str
    Format: str
    Enabled: bool
    Prefix: str
    ReportScope: str


class ManifestSpec(BaseModel):
    Format: str
    Fields: List[str] = ["Bucket", "Key"]


class ManifestLoc(BaseModel):
    ObjectArn: str
    ObjectVersionId: Optional[str]
    ETag: str


class ManifestConfig(BaseModel):
    Spec: ManifestSpec
    Location: ManifestLoc


class LambdaOperation(BaseModel):
    LambdaInvoke: Dict[str, str]


class S3BatchJob(BaseModel):
    AccountId: str  # Set a default
    ConfirmationRequired: bool = True  # Set a default
    Description: str
    Priority: Optional[int] = 10
    ClientRequestToken: str = uuid.uuid1()  # Optional
    Operation: LambdaOperation
    Report: ReportConfig
    Manifest: ManifestConfig
    RoleArn: str
    Tags: List[Tag] = []


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Utility: process s3batch job file")
    parser.add_argument('jobs', nargs=1, help='S3Batch Jobs JSON')
    args = parser.parse_args()
    jobs_file = args.jobs[0]

    with open(jobs_file) as file:
        data = json.load(file)
        jobs: List[S3BatchJob] = [S3BatchJob(**item) for item in data]
        # print(jobs[0])
        for job in jobs:
            print(job.dict(exclude_unset=True))
            create_s3batch_job_from_json(job.dict(exclude_unset=True))
