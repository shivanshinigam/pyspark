File to exact commands to run on terminal - https://drive.google.com/file/d/1G8sO6h76nfZkk3Wp8hBVHg8RM2RvPv8K/view?usp=drivesdk
# AWS Lambda — Three Staged Tasks Report

## 📌 Task 1 — Create a Hello-World AWS Lambda Function With a Dynamic Placeholder (Name Parameter)

### Objective

Create a Lambda function in Python that:

- Returns a Hello World response.
- Accepts a dynamic name parameter (e.g., `?name=Divya`)
- Is exposed publicly via a Lambda Function URL so it can be tested in a browser or via curl.

### 1. Steps Performed

#### Step 1 — Created Lambda Function

    Opened AWS Console → Lambda → Create function

Selected Author from scratch

    Runtime: Python 3.11
    
    Function name: hello_name

#### Step 2 — Wrote the Lambda Handler Code

The code accepts a query parameter and prints "Hello world from <name>".
    
    ``python
    import json
    
    def lambda_handler(event, context):
        params = event.get("queryStringParameters") or {}
        name = params.get("name", "world")
    
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Hello world from {name}"})
        }
Step 3 — Tested Function in AWS Console
Created a test event named api-test

Output:
<img width="1440" height="900" alt="1" src="https://github.com/user-attachments/assets/276a01a4-c787-46a0-9b57-cd259c6d98ed" />

json

    {"message": "Hello world from Divya"}

Step 4 — Deployed & Created Function URL
Went to Configuration → Function URL

Enabled NONE auth (public)

<img width="1440" height="900" alt="url1" src="https://github.com/user-attachments/assets/cc1da021-2b69-4bee-a8f8-f60666085c4d" />

Step 5 — Tested in Browser
Examples:

    https://<lambda-url>/?name=Divya
    https://<lambda-url>/?name=Shivanshi
    
Result
✔ Dynamic placeholder works

✔ Function URL works

<img width="855" height="484" alt="check1" src="https://github.com/user-attachments/assets/c9928a42-8031-455b-9343-863edcb3cf27" />


📌 Task 2 — Lambda + Pandas Layer + API Filter

Objective
Use Pandas inside Lambda (not available by default), and build an API that:

Loads a dataset inside the Lambda function

Uses pandas DataFrame to filter data using the name query parameter

Returns filtered results as JSON

2. Steps Performed
Step 1 — Built a Pandas Layer Using Docker
Since Pandas must match AWS Lambda Linux environment, we used Docker:

        mkdir lambda_pandas_layer
        cd lambda_pandas_layer

        echo "pandas==2.2.3" > requirements.txt
        echo "numpy==1.26.4" >> requirements.txt

        docker run --rm -v "$PWD":/var/task public.ecr.aws/sam/build-python3.11:latest \
          /bin/sh -c "pip install -r requirements.txt -t python && exit"

        zip -r pandas_layer.zip python
   
Step 2 — Uploaded Layer in AWS Lambda
AWS Console → Lambda → Layers → Create layer

Uploaded pandas_layer.zip
<img width="1440" height="900" alt="pandazip" src="https://github.com/user-attachments/assets/0e0ea3ce-1541-4001-83a7-e25bb10062d9" />

Selected Python 3.11 runtime

Step 3 — Created New Lambda Function
Name: pandas-api

Runtime: Python 3.11

Step 4 — Attached Pandas Layer to Function
Configuration → Layers → Add layer → Choose "pandas_layer"

Step 5 — Added Code

    import json
    import pandas as pd
    
    def lambda_handler(event, context):
        data = [
            {"id": 1, "name": "Divya", "dept": "Engineering", "salary": 90000},
            {"id": 2, "name": "Amit", "dept": "HR", "salary": 65000},
            {"id": 3, "name": "Priya", "dept": "Finance", "salary": 70000},
        ]

    df = pd.DataFrame(data)
    params = event.get("queryStringParameters") or {}
    name = params.get("name")

    if name:
        df = df[df["name"].str.lower() == name.lower()]

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"rows": df.to_dict(orient="records")})
    }
    
Step 6 — Created Function URL & Tested
<img width="1440" height="900" alt="url2" src="https://github.com/user-attachments/assets/d71f69be-0ab4-4680-9ac7-1fd6f6cac880" />


Examples:

    https://<lambda-url>/?name=Divya
    https://<lambda-url>/

<img width="856" height="490" alt="check2" src="https://github.com/user-attachments/assets/15eb0474-fb8f-4ecf-9a79-9b5b4df108b5" />

Result
✔ Pandas successfully runs inside Lambda

✔ Dynamic filtering works

✔ JSON results returned correctly

✔ Task 2 completed successfully

📌 Task 3 — Lambda + Pandas + S3 CSV Integration
Objective
Extend the Lambda + Pandas functionality to:

Load data from S3

Parse CSV using Pandas

Filter based on query parameter

Return JSON output through Function URL

3. Steps Performed
Step 1 — Created S3 Bucket and Uploaded CSV

<img width="1440" height="900" alt="s3bucket" src="https://github.com/user-attachments/assets/5ab01fda-c52a-4209-8262-e99ebfffbd78" />

Bucket name example:
        
        pandalayer1
   
CSV file:

    employees.csv
    
Sample content:

    id,name,dept,salary
    1,Divya,Engineering,90000
    2,Amit,HR,65000
    3,Priya,Finance,70000
    
Step 2 — Gave Lambda Permission to Read S3
Attached IAM policy to Lambda execution role:

json

      {
        "Effect": "Allow",
        "Action": ["s3:GetObject"],
        "Resource": "arn:aws:s3:::pandalayer1/*"
      }
      
Step 3 — Updated Lambda Code

    # lambda_function.py
    import json
    import os
    import boto3
    import pandas as pd
    from io import StringIO
    
    s3 = boto3.client("s3")
    EMPLOYEE_BUCKET = os.environ.get("EMPLOYEE_BUCKET")
    EMPLOYEE_KEY = os.environ.get("EMPLOYEE_KEY", "employees.csv")
    
    def read_csv_from_s3(bucket, key):
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj['Body'].read().decode('utf-8')
        return pd.read_csv(StringIO(body))
    
    def lambda_handler(event, context):
        # read CSV from S3 using pandas
        try:
            df = read_csv_from_s3(EMPLOYEE_BUCKET, EMPLOYEE_KEY)
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Failed to read S3 object: {str(e)}"})
            }
    
        # filter by query param
        params = event.get("queryStringParameters") or {}
        name = params.get("name")
        if name:
            filtered = df[df['name'].str.lower() == name.lower()]
        else:
            filtered = df
    
        rows = filtered.to_dict(orient='records')
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"rows": rows})
        }
<img width="1440" height="900" alt="s32panda" src="https://github.com/user-attachments/assets/e443afa7-eb55-43f5-8842-027338bdf3fb" />


<img width="1440" height="900" alt="s32panda" src="https://github.com/user-attachments/assets/1d07ad5f-54f4-4348-a884-634c2abcf3d5" />

Step 4 — Tested via Function URL

<img width="991" height="557" alt="url3" src="https://github.com/user-attachments/assets/5d011584-42b2-43f5-b641-2bf9bcf81ecc" />

Examples:

    https://<lambda-url>/ → returns all employees
    https://<lambda-url>/?name=Divya → returns only Divya
    
Result
✔ Lambda reading CSV from S3

✔ Pandas filtering working

✔ Output returned as JSON

✔ Task 3 completed successfully


# 📌 Task 4 — Run SQL Queries on PySpark Using AWS Glue + Lambda (with API Access)

## Objective

Build a system that allows anyone (your mentor) to run SQL queries like:

    SELECT * FROM employees WHERE name = 'Divya'

Through an HTTP API, but executed inside AWS Glue using PySpark, and results returned as JSON.

This system must use:

- ✅ AWS Glue (PySpark engine)  
- ✅ boto3 (to trigger Glue from Python)  
- ✅ Lambda (to expose API endpoint)  
- ✅ S3 (store input CSV + store output JSON)  


---

## 🧠 High-Level Architecture (Simple Explanation)

    Browser / curl
    ↓ (SQL via JSON)
    AWS Lambda (API layer)
    ↓ (boto3)
    AWS Glue Job (PySpark)
    ↓ (writes output)
    S3 (JSON result)
    ↓
    Lambda reads S3 → returns JSON to user


**Why this design?**

- Lambda cannot run PySpark → too heavy  
- Glue can run PySpark, but cannot provide API  
- So Lambda = API, Glue = compute engine

This is the exact architecture AWS recommends for PySpark queries.

---

## 🎯 What We Built (Summary)

    | Component | Purpose |
    |---|---|
    | GlueSparkRole | IAM role for Glue job to read from S3 + run PySpark |
    | LambdaGlueRunnerRole | IAM role for Lambda to start Glue jobs |
    | employees.csv | Input dataset stored in S3 (pandalayer1) |
    | glue_sql_job.py | PySpark job that loads CSV, runs SQL, writes output JSON |
    | create_glue_job.py | Script to create/update Glue job using boto3 |
    | lambda_trigger_glue.py | Lambda file that receives SQL and triggers Glue job |
    | Lambda Function URL | The public API for running SQL |

Everything is automated and fully working.

---

## 🧂 Step-by-Step Execution 

This section matches EXACTLY the steps we executed in Terminal.

### 1️⃣ Created IAM Roles

#### A. Glue Role — `GlueSparkRole`

This role allows Glue to:
- Assume role (sts:AssumeRole)
- Read/write S3
- Write logs

Command used:

      cat > /tmp/glue_trust.json <<'JSON'
      {
        "Version":"2012-10-17",
        "Statement":[
          {
            "Effect":"Allow",
            "Principal":{"Service":"glue.amazonaws.com"},
            "Action":"sts:AssumeRole"
          }
        ]
      }
    JSON
    
    aws iam create-role --role-name GlueSparkRole --assume-role-policy-document file:///tmp/glue_trust.json
    aws iam attach-role-policy --role-name GlueSparkRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole
    aws iam attach-role-policy --role-name GlueSparkRole --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

Result ARN:

    arn:aws:iam::780167008601:role/GlueSparkRole
    
B. Lambda Role — LambdaGlueRunnerRole
Purpose:

Start Glue jobs

Poll Glue jobs

Read job output from S3

Write Lambda logs

Created and auto-attached inline policy:

    aws iam create-role --role-name LambdaGlueRunnerRole \
    --assume-role-policy-document file:///tmp/lambda_trust.json

Permissions added:

    glue:StartJobRun
    
    glue:GetJobRun
    
    s3:GetObject
    
    logs:PutLogEvents
    
    AWSLambdaBasicExecutionRole

2️⃣ Created S3 Input Folder & Uploaded employees.csv
Bucket used:


    pandalayer1

CSV uploaded:

    employees.csv
    
Content:

    id,name,dept,salary
    1,Divya,Engineering,90000
    2,Amit,HR,65000
    3,Priya,Finance,70000

Glue will load this file every time.

3️⃣ Created the Glue PySpark Script — glue_sql_job.py
This script:

Loads CSV from S3

Registers DataFrame as SQL table

Runs SQL passed from Lambda

Writes results into S3 as JSON

Writes a manifest.json describing output

Final code we deployed:

    import sys
    import boto3
    import json
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder.appName("DynamicSQLJob").getOrCreate()
    
    # arguments passed from Lambda
    args = sys.argv
    sql = args[args.index("--sql") + 1]
    output_prefix = args[args.index("--output_s3_prefix") + 1]
    
    # Load employees.csv from S3
    df = spark.read.csv("s3://pandalayer1/employees.csv", header=True, inferSchema=True)
    df.createOrReplaceTempView("employees")
    
    # Run SQL
    result = spark.sql(sql)
    
    # Save results
    result.write.mode("overwrite").json(output_prefix + "/data")
    
    # Write manifest for Lambda to read
    manifest = {"rows": [row.asDict() for row in result.collect()]}
    s3 = boto3.client("s3")
    bucket = "pandalayer1"
    key = output_prefix.replace("s3://pandalayer1/", "") + "/manifest.json"
    
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(manifest))
    
    spark.stop()
    
4️⃣ Created the Glue Job Using create_glue_job.py

This file creates (or updates) the Glue Job using boto3.

Stored at:

    glue_sql_project/create_glue_job.py
    
Command executed:

    python3 create_glue_job.py
    
Output:

    Created job: glue-dynamic-sql-job
    
Glue job now points to:

    script_path = "s3://pandalayer1/scripts/glue_sql_job.py"

5️⃣ Created Lambda API Layer — lambda_trigger_glue.py
This file:

    Accepts JSON POST { "sql": "SELECT * FROM employees" }

Starts Glue job → waits until completion

Fetches manifest.json from S3

Returns the rows to the user

We deployed an updated version that fixes datetime serialization and manifest lookup.

6️⃣ Built & Deployed Lambda Function

Compressed Lambda:

    zip -r function.zip lambda_trigger_glue.py
    
Created/updated Lambda function:

    aws lambda create-function ...
    aws lambda update-function-code ...
    
Environment variables set:

    REGION=us-east-1
    JOB_NAME=glue-dynamic-sql-job
    OUTPUT_BUCKET=pandalayer1
    OUTPUT_PREFIX_ROOT=glue-output
    POLL_INTERVAL=5

7️⃣ Created Lambda Function URL (Public API)

    https://fk7pa3ljwyz3yb2u5zgox7jzhm0fijgp.lambda-url.us-east-1.on.aws/
    
Auth type: NONE (public for testing)

8️⃣ Tested Queries Successfully
Query 1 — All rows

    curl -s -X POST -H "Content-Type: application/json" \
    -d '{"sql":"SELECT * FROM employees"}' \
    "$FUNCTION_URL" | jq
Output

<img width="218" height="377" alt="Screenshot 2025-12-09 at 12 17 52 AM" src="https://github.com/user-attachments/assets/9c2baf0e-5ec2-4f1a-8b03-529cf299dc86" />

    [
      {"id":1,"name":"Divya","dept":"Engineering","salary":90000},
      {"id":2,"name":"Amit","dept":"HR","salary":65000},
      {"id":3,"name":"Priya","dept":"Finance","salary":70000}
    ]
    
Query 3 — Salary condition


    curl -s -X POST -H "Content-Type: application/json" \
    -d '{"sql":"SELECT name, salary FROM employees WHERE salary > 70000"}' \
    "$FUNCTION_URL" | jq

<img width="806" height="228" alt="Screenshot 2025-12-09 at 12 17 59 AM" src="https://github.com/user-attachments/assets/33e8692e-3441-4e40-9b3a-c3ed9ce711cf" />


Check example through — Postman

Method: POST

URL:

        https://fk7pa3ljwyz3yb2u5zgox7jzhm0fijgp.lambda-url.us-east-1.on.aws/


Body → Raw → JSON:

        {"sql": "SELECT * FROM employees"}

![WhatsApp Image 2025-12-09 at 00 55 10](https://github.com/user-attachments/assets/fc5f296c-00f9-457d-bbc2-24e1d6bad58b)
