import os, json, time, boto3, re
from urllib.parse import urlparse

REGION = os.environ.get("REGION", "us-east-1")
JOB_NAME = os.environ.get("JOB_NAME", "glue-dynamic-sql-job")
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET", "pandalayer1")
OUTPUT_PREFIX_ROOT = os.environ.get("OUTPUT_PREFIX_ROOT", "glue-output")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "5"))

glue = boto3.client("glue", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

def start_glue_and_wait(sql):
    import uuid, datetime
    run_id = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + "-" + str(uuid.uuid4())[:8]
    output_prefix = f"s3://{OUTPUT_BUCKET}/{OUTPUT_PREFIX_ROOT}/{run_id}/"
    resp = glue.start_job_run(
        JobName=JOB_NAME,
        Arguments={
            "--sql": sql,
            "--output_s3_prefix": output_prefix
        }
    )
    job_run_id = resp["JobRunId"]
    while True:
        jr = glue.get_job_run(JobName=JOB_NAME, RunId=job_run_id)["JobRun"]
        state = jr["JobRunState"]
        if state in ("SUCCEEDED", "FAILED", "STOPPED", "TIMEOUT"):
            return state, jr, output_prefix
        time.sleep(POLL_INTERVAL)

def try_get_object_json(bucket, key):
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj['Body'].read().decode('utf-8')
        try:
            return json.loads(body)
        except:
            return {"raw": body}
    except s3.exceptions.NoSuchKey:
        return None
    except Exception as e:
        # other S3 errors, bubble up
        raise

def discover_latest_run_prefix():

    prefix = OUTPUT_PREFIX_ROOT.rstrip('/') + '/'
    resp = s3.list_objects_v2(Bucket=OUTPUT_BUCKET, Prefix=prefix, MaxKeys=1000)
    if 'Contents' not in resp:
        return None

    run_set = set()
    for o in resp['Contents']:
        k = o['Key']
        # expect keys like "glue-output/20251208T182529Z-xxxx/..."
        m = re.match(r'^' + re.escape(prefix) + r'([^/]+)/', k)
        if m:
            run_set.add(m.group(1))
    if not run_set:
        return None

    latest_run = sorted(run_set)[-1]
    return f"s3://{OUTPUT_BUCKET}/{prefix}{latest_run}/"

def read_manifest(output_prefix):

    p = output_prefix
    if p.startswith("s3://"):
        p = p[len("s3://"):]
    parts = p.split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""
    prefix = prefix.rstrip('/')

    candidates = [
        f"{prefix}/manifest.json",
        f"{prefix}/manifest.json/part-00000",
        f"{prefix}/data/part-00000",
        f"{prefix}/data/part-00000-00000.json"
    ]
    for key in candidates:
        res = try_get_object_json(bucket, key)
        if res is not None:
            return res

   
    discovered = discover_latest_run_prefix()
    if discovered:
        # try again using discovered prefix
        if discovered.startswith("s3://"):
            discovered_p = discovered[len("s3://"):]
        else:
            discovered_p = discovered
        parts = discovered_p.split("/", 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
        prefix = prefix.rstrip('/')
        for key_suffix in ["manifest.json", "manifest.json/part-00000", "data/part-00000"]:
            key = f"{prefix}/{key_suffix}"
            res = try_get_object_json(bucket, key)
            if res is not None:
                return res


    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1000)
    for o in resp.get('Contents', []):
        k = o['Key']
        if k.endswith('.json') or 'part-' in k:
            res = try_get_object_json(bucket, k)
            if res is not None:
                return res

    raise Exception(f"Manifest not found under s3://{bucket}/{prefix}")

def safe_json(o):
    from datetime import datetime, date
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    try:
        return str(o)
    except:
        return "UNSERIALIZABLE"

def lambda_handler(event, context):
    try:

        body = event.get("body")
        if body:
            payload = json.loads(body) if isinstance(body, str) else body
            sql = payload.get("sql")
        else:
            params = event.get("queryStringParameters") or {}
            sql = params.get("sql")
        if not sql:
            return {"statusCode": 400, "body": json.dumps({"error":"Provide 'sql' in POST body or ?sql= in query"})}

        state, jr, output_prefix = start_glue_and_wait(sql)
        if state != "SUCCEEDED":
            return {"statusCode": 500, "body": json.dumps({"status": state, "jobRun": jr}, default=safe_json)}

        manifest = read_manifest(output_prefix)
        return {"statusCode": 200, "headers":{"Content-Type":"application/json"}, "body": json.dumps(manifest, default=safe_json)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
