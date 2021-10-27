
# SCRIPT (Method 1)
# aws_detect_pii.py functionality
deid: deid_ohsu deid_washu

# For targeting or ignore a specific prefix to identify use
# add --prefix <target_prefix>
# or add --ignore-prefix <h_and_e>
deid_ohsu:
	python scripts/aws_detect_pii.py \
		-b htan-dcc-ohsu \
		--bucket-type aws \
		--profile sandbox-developer \
		--comprehend_profile htan-dev-admin \
		> outputs/test_ohsu_output.tsv

deid_washu:
	python scripts/aws_detect_pii.py \
		-b htan-dcc-washu \
		--bucket-type gcs \
		--profile htan-gcs \
		--comprehend_profile htan-dev-admin \
		> outputs/test_washu_output.tsv



# LAMBDA & S3Batch prior work with deidentification functionality
# (Method 2), for posterity
deploy:
	sam deploy --profile htan-dev-admin --guided
process_s3batch:
	python scripts/process_s3batch_jobs.py batch_jobs.json
