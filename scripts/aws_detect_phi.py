
import sys
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


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


def list_objects(bucket, prefix=None):
    """
    Lists the objects in a bucket, optionally filtered by a prefix.

    Usage is shown in usage_demo at the end of this module.

    :param bucket: The bucket to query.
    :param prefix: When specified, only objects that start with this prefix are listed.
    :return: The list of objects.
    """
    try:
        if not prefix:
            objects = list(bucket.objects.all())
        else:
            objects = list(bucket.objects.filter(Prefix=prefix))
        logger.info("Got objects %s from bucket '%s'",
                    [o.key for o in objects], bucket.name)
    except ClientError:
        logger.exception("Couldn't get objects for bucket '%s'.", bucket.name)
        raise
    else:
        return objects

def example_lambda_handler(event, context):
    # TODO to implement
    import boto3

    s3 = boto3.client('s3')
    data = s3.get_object(Bucket='my_s3_bucket', Key='main.txt')

def js_lambda_handler():
    """
    var AWS = require('aws-sdk');
    var s3 = new AWS.S3();

    exports.handler = function(event, context, callback) {

        // Retrieve the bucket & key for the uploaded S3 object that
        // caused this Lambda function to be triggered
        var src_bkt = event.Records[0].s3.bucket.name;
        var src_key = event.Records[0].s3.object.key;

        // Retrieve the object
        s3.getObject({
            Bucket: src_bkt,
            Key: src_key
        }, function(err, data) {
            if (err) {
                console.log(err, err.stack);
                callback(err);
            } else {
                console.log("Raw text:\n" + data.Body.toString('ascii'));
                callback(null, null);
            }
        });
    };
    """
    pass


def detect_phi(data, client):
    return client.detect_pii_entities(Text=data, LanguageCode='en')


if __name__ == '__main__':
    file = sys.argv[1]
    s3 = boto3.client('s3')
    dlp = boto3.client('comprehend')

    response = s3.list_buckets()
    print('Existing Buckets:')
    for bucket in response['Buckets']:
        print(bucket)
    # bucket = s3.Bucket('nyxhome-test-bucket')
    # txt = get_object('nyxhome-test-bucket', 'example_texts/text1.txt')
    # print(txt)
    # objects = list_objects(bucket)


    # Detect pii entities
    response = None
    with open(file, 'r') as fh:
        data = fh.read()
        # response = detect_phi(data)

    if response:
        for i in response.get('Entities'):
            print(i)
