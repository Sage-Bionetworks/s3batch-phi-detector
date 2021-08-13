
# Reference
"""
    response = client.create_job(
    AccountId='string',
    ConfirmationRequired=True|False,
    Operation={
        'LambdaInvoke': {
            'FunctionArn': 'string'
        },
        'S3PutObjectCopy': {
            'TargetResource': 'string',
            'CannedAccessControlList': 'private'|'public-read'|'public-read-write'|'aws-exec-read'|'authenticated-read'|'bucket-owner-read'|'bucket-owner-full-control',
            'AccessControlGrants': [
                {
                    'Grantee': {
                        'TypeIdentifier': 'id'|'emailAddress'|'uri',
                        'Identifier': 'string',
                        'DisplayName': 'string'
                    },
                    'Permission': 'FULL_CONTROL'|'READ'|'WRITE'|'READ_ACP'|'WRITE_ACP'
                },
            ],
            'MetadataDirective': 'COPY'|'REPLACE',
            'ModifiedSinceConstraint': datetime(2015, 1, 1),
            'NewObjectMetadata': {
                'CacheControl': 'string',
                'ContentDisposition': 'string',
                'ContentEncoding': 'string',
                'ContentLanguage': 'string',
                'UserMetadata': {
                    'string': 'string'
                },
                'ContentLength': 123,
                'ContentMD5': 'string',
                'ContentType': 'string',
                'HttpExpiresDate': datetime(2015, 1, 1),
                'RequesterCharged': True|False,
                'SSEAlgorithm': 'AES256'|'KMS'
            },
            'NewObjectTagging': [
                {
                    'Key': 'string',
                    'Value': 'string'
                },
            ],
            'RedirectLocation': 'string',
            'RequesterPays': True|False,
            'StorageClass': 'STANDARD'|'STANDARD_IA'|'ONEZONE_IA'|'GLACIER'|'INTELLIGENT_TIERING'|'DEEP_ARCHIVE',
            'UnModifiedSinceConstraint': datetime(2015, 1, 1),
            'SSEAwsKmsKeyId': 'string',
            'TargetKeyPrefix': 'string',
            'ObjectLockLegalHoldStatus': 'OFF'|'ON',
            'ObjectLockMode': 'COMPLIANCE'|'GOVERNANCE',
            'ObjectLockRetainUntilDate': datetime(2015, 1, 1),
            'BucketKeyEnabled': True|False
        },
        'S3PutObjectAcl': {
            'AccessControlPolicy': {
                'AccessControlList': {
                    'Owner': {
                        'ID': 'string',
                        'DisplayName': 'string'
                    },
                    'Grants': [
                        {
                            'Grantee': {
                                'TypeIdentifier': 'id'|'emailAddress'|'uri',
                                'Identifier': 'string',
                                'DisplayName': 'string'
                            },
                            'Permission': 'FULL_CONTROL'|'READ'|'WRITE'|'READ_ACP'|'WRITE_ACP'
                        },
                    ]
                },
                'CannedAccessControlList': 'private'|'public-read'|'public-read-write'|'aws-exec-read'|'authenticated-read'|'bucket-owner-read'|'bucket-owner-full-control'
            }
        },
        'S3PutObjectTagging': {
            'TagSet': [
                {
                    'Key': 'string',
                    'Value': 'string'
                },
            ]
        },
        'S3DeleteObjectTagging': {}
        ,
        'S3InitiateRestoreObject': {
            'ExpirationInDays': 123,
            'GlacierJobTier': 'BULK'|'STANDARD'
        },
        'S3PutObjectLegalHold': {
            'LegalHold': {
                'Status': 'OFF'|'ON'
            }
        },
        'S3PutObjectRetention': {
            'BypassGovernanceRetention': True|False,
            'Retention': {
                'RetainUntilDate': datetime(2015, 1, 1),
                'Mode': 'COMPLIANCE'|'GOVERNANCE'
            }
        }
    },
    Report={
        'Bucket': 'string',
        'Format': 'Report_CSV_20180820',
        'Enabled': True|False,
        'Prefix': 'string',
        'ReportScope': 'AllTasks'|'FailedTasksOnly'
    },
    ClientRequestToken='string',
    Manifest={
        'Spec': {
            'Format': 'S3BatchOperations_CSV_20180820'|'S3InventoryReport_CSV_20161130',
            'Fields': [
                'Ignore'|'Bucket'|'Key'|'VersionId',
            ]
        },
        'Location': {
            'ObjectArn': 'string',
            'ObjectVersionId': 'string',
            'ETag': 'string'
        }
    },
    Description='string',
    Priority=123,
    RoleArn='string',
    Tags=[
        {
            'Key': 'string',
            'Value': 'string'
        },
    ]
)
"""
