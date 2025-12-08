# glue_sql_job.py — fixed: write DataFrame output to JSON files and write a manifest using boto3
import sys, json, boto3
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession

# Glue expects arguments: JOB_NAME, sql, output_s3_prefix
args = getResolvedOptions(sys.argv, ["JOB_NAME", "sql", "output_s3_prefix"])
sql = args["sql"]
output_prefix = args["output_s3_prefix"].rstrip("/") + "/"

# create spark
spark = SparkSession.builder.appName("GlueDynamicSQL").getOrCreate()

# read input CSV from S3 (hard-coded path used earlier)
csv_path = "s3://pandalayer1/data/employees.csv"
df = spark.read.option("header","true").option("inferSchema","true").csv(csv_path)
df.createOrReplaceTempView("employees")

# run SQL
result_df = spark.sql(sql)

# write result as JSON parts (coalesce small result to single file if small)
out_path = output_prefix + "data/"
result_df.coalesce(1).write.mode("overwrite").json(out_path)

# collect rows (safe for small result sets; for big results consider streaming to S3)
rows = [r.asDict() for r in result_df.collect()]

# write manifest using boto3 (no Spark saveAsTextFile)
s3 = boto3.client("s3")
# output_prefix like s3://bucket/prefix/
parsed = output_prefix.replace("s3://", "").split("/", 1)
bucket = parsed[0]
prefix = parsed[1] if len(parsed) > 1 else ""

manifest_key = prefix.rstrip("/") + "/manifest.json"
s3.put_object(Bucket=bucket, Key=manifest_key, Body=json.dumps({"rows": rows}))

print("Wrote manifest to s3://%s/%s" % (bucket, manifest_key))
spark.stop()
