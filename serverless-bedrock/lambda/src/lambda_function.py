import json
import boto3
import csv
import io
import os
import re

# AWS Clients
s3_client = boto3.client("s3")
bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")
ssm_client = boto3.client("ssm")

# ✅ Fetch environment variables from SSM Parameter Store
def get_ssm_parameter(name):
    """Retrieve parameter from AWS Systems Manager (SSM)."""
    response = ssm_client.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]

BUCKET_NAME = get_ssm_parameter(os.environ["SSM_BUCKET_NAME"])
MODEL_ID = get_ssm_parameter(os.environ["SSM_MODEL_ID"])
STATIC_CDSi_KEY = get_ssm_parameter(os.environ["SSM_STATIC_CDSi_KEY"])

def load_static_cdsi():
    """Loads the static CSV file from S3 and returns its data."""
    cdsi_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=STATIC_CDSi_KEY)
    cdsi_data = cdsi_obj["Body"].read().decode("utf-8")

    csv_reader = csv.reader(io.StringIO(cdsi_data))
    headers = next(csv_reader) 
    data = [row for row in csv_reader]  
    
    return headers, data

def extract_conditions_section(text_data):
    """Extracts the CONDITIONS section from the text file."""
    lines = text_data.split("\n")
    extracting = False
    conditions_section = []

    for line in lines:
        if "CONDITIONS:" in line:
            extracting = True
            continue  

        if extracting:
            if re.match(r"^-{5,}$", line):  
                break
            conditions_section.append(line)

    return "\n".join(conditions_section)

def filter_disorder_conditions(conditions_text):
    """Filters the extracted CONDITIONS section."""
    lines = conditions_text.split("\n")
    filtered_lines = []

    for line in lines:
        if "disorder" in line.lower() or "finding" in line.lower():
            match = re.match(
                r"\s*\d{4}-\d{2}-\d{2} -\s*(\d{4}-\d{2}-\d{2})?", line)
            if match and not match.group(1):  # Keep only if there is no end date
                filtered_lines.append(line)

    return "\n".join(filtered_lines)

def call_bedrock(filtered_conditions, static_csv_headers, static_csv_data):
    """Calls AWS Bedrock `MODEL_ID` using the correct Messages API format."""
    prompt = f"""
Instructions:

List only the confirmed CSDi codes that directly match the patient's documented conditions. When analyzing matches:
- Check exact SNOMED clinical thresholds and criteria (e.g., severe obesity requires a specific BMI).
- Consider common medical terminology variations/synonyms.
- Distinguish between similarly-named conditions.

**Patient Data:**
Static Labels (Reference):
{", ".join(static_csv_headers)}
{static_csv_data}

**Current Conditions (Filtered for Clinical Review):**

{filtered_conditions}

**For each confirmed match, provide:**
1. CSDi Code:
2. Observation Title:
3. Supporting Reference from Patient Record:

Only include codes with explicit evidence in the patient's record. Exclude any uncertain or inferential codes. Ensure precise clinical matching while keeping the response concise and direct.
"""

    request_payload = {
        "anthropic_version": "bedrock-2023-05-31", 
        "max_tokens": 1024,
        "temperature": 0,  
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
    }

    request_body = json.dumps(request_payload)

    try:
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=request_body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read())
        return response_body

    except Exception as e:
        print(f"ERROR: Can't invoke '{MODEL_ID}'. Reason: {e}")
        return {"error": str(e)}

def lambda_handler(event, context):
    """Lambda function that processes input from API Gateway or S3 Event."""
    try:
        # Check if API Gateway triggered the Lambda
        if "httpMethod" not in event:  
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid trigger source. This function must be called via API Gateway."})}
        print("Triggered via API Gateway")
        body = json.loads(event["body"])
        text_file_key = body.get("file_key")

        if not text_file_key:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing 'file_key' parameter."})}

        # Log the file being processed
        print(f"Processing file: {text_file_key}")

        # Read the newly uploaded text file
        text_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=text_file_key)
        text_data = text_obj["Body"].read().decode("utf-8")

        # Load the static CDSi file
        cdsi_headers, cdsi_data = load_static_cdsi()

        # Extract and filter the CONDITIONS section
        conditions_section = extract_conditions_section(text_data)
        filtered_conditions = filter_disorder_conditions(conditions_section)

        # Call `MODEL_ID` LLM with the processed data
        bedrock_response = call_bedrock(filtered_conditions, cdsi_headers, cdsi_data)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Processing complete",
                "file": text_file_key,
                "bedrock_output": bedrock_response
            }),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
