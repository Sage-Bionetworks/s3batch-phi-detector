# The manifest.csv file provides a list of bucket and object key values.
# The job applies the specified tags to objects identified in the manifest.
# The ETag is the ETag of the manifest.csv object, which you can get from the Amazon S3 console.
# The request specifies the no-confirmation-required parameter.
# Therefore, Amazon S3 makes the job eligible for execution without you having to confirm it using the udpate-job-status command.
ManifestObjectArn=arn:aws:s3:::s3batch-dev-unmanaged/manifest_1.csv
ManifestETag=94df2511f90e496f66b10e17018df899
ReportBucketArn=arn:aws:s3:::s3batch-dev-unmanaged

# Implicitly created Arns
BatchRoleArn=arn:aws:iam::888810830951:role/dcc-phi-checker-BatchRole-GPU8191TJ4LT
LambdaFNArn=arn:aws:lambda:us-east-1:888810830951:function:dcc-phi-checker-DetectPHI-HgOcKvXPkc6e

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
