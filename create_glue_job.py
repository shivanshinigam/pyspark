import os, boto3
region = "us-east-1"
job_name = "glue-dynamic-sql-job"
script_path = "s3://pandalayer1/scripts/glue_sql_job.py"
role_arn = os.environ.get("GLUE_ROLE_ARN")

if not role_arn:
    raise SystemExit("Set GLUE_ROLE_ARN environment variable before running this script")

glue = boto3.client("glue", region_name=region)

try:
    glue.get_job(JobName=job_name)
    print("Job already exists:", job_name)
except glue.exceptions.EntityNotFoundException:
    response = glue.create_job(
        Name=job_name,
        Role=role_arn,
        Command={
            "Name": "glueetl",
            "ScriptLocation": script_path,
            "PythonVersion": "3"
        },
        GlueVersion="3.0",
        NumberOfWorkers=2,
        WorkerType="Standard"
    )
    print("Created job:", response["Name"])
