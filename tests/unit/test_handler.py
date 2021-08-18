import json

import pytest
from moto import mock_s3

from dcc_phi_reporter import app

MY_BUCKET = "my_bucket"
MY_PREFIX = "mock_folder"


@pytest.fixture()
def apigw_event():
    """ Generates API GW Event"""

    return {
        "body": '{ "test": "body"}',
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {"foo": "bar"},
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "POST",
        "stageVariables": {"baz": "qux"},
        "path": "/examplepath",
    }


@pytest.fixture()
def s3Batch_event():
    response = {
      "invocationSchemaVersion": "1.0",
      "invocationId": "YXNkbGZqYWRmaiBhc2RmdW9hZHNmZGpmaGFzbGtkaGZza2RmaAo",
      "job": {
        "id": "f3cc4f60-61f6-4a2b-8a21-d07600c373ce"
      },
      "tasks": [
        {
          "taskId": "dGFza2lkZ29lc2hlcmUK",
          "s3Key": "example_texts_1/text1.txt",
          "s3VersionId": "1",
          "s3BucketArn": "arn:aws:s3:::s3batch-dev-unmanaged"
        }
      ]
    }
    return response


# def test_lambda_handler(apigw_event, mocker):
def test_lambda_handler(s3Batch_event, mocker):
    # ret = app.lambda_handler(apigw_event, "")
    # data = json.loads(ret["body"])
    # assert ret["statusCode"] == 200
    # assert "message" in ret["body"]
    # assert data["message"] == "hello world"

    # Mock S3 resource
    # Pull S3 get_object from mocked S3 directory


    # Mock AWS comprehend API

    # ret = app.lambda_handler(s3Batch_event, "")
    pass

    # print(ret)
    # assert ret["invocationId"] == s3Batch_event["invocationId"]
    # assert ret["invocationSchemaVersion"] == s3Batch_event["invocationSchemaVersion"]
