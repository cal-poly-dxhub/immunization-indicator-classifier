## Deployment Guide

This project includes two sets of deployable solutions using **AWS CDK (Cloud Development Kit)**. If you're unfamiliar with CDK, see [What is the AWS CDK?](https://docs.aws.amazon.com/cdk/v2/guide/home.html).

---

### Prerequisites

- An **AWS account**
- API credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN)
- Python 3 installed

---

### Environment Setup

```bash
# Install Node.js (if not installed)
https://nodejs.org/en/download

# Install AWS CDK
sudo npm install -g aws-cdk

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Navigate to CDK folder
cd cdk

## TODO: Set your environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN)
```

---

## 1. LLM-Based Classification Deployment

> ✅ Tested on **Synthea HL7 Text format** ([Instructions on how to generate available here](https://github.com/synthetichealth/synthea))

### Setup

- In your AWS Account, make an s3 bucket (or use an existing one) and upload your `CDSi.csv` to an S3 bucket.
  - It must contain **only** these columns for the LLM to not get confused:
    - `Observation Code`
    - `Observation Title`
    - `SNOMED (Code)`

- Set the following in the CDK parameter store in the file `cdk/stacks/serverless_bedrock_stack.py`:
  - `STATIC_CDSi_KEY`: The s3 file key of the `CDSi.csv` you just uploaded to s3
  - `BUCKET_NAME`: The bucket that contains this `CDSi.csv`
  - `MODEL_ID`: The AWS Bedrock ID of the LLM you want to use

### Deploy

```bash
cdk deploy ServerlessBedrock
```

- CDK will output an API Gateway URL:
  ```
  ServerlessBedrockStack.APIGatewayURL = https://...
  ```
  - Also available in AWS Systems Manager Parameter Store under `/config/Level1IZClassificationEndpoint`

### Use
- Upload a **Synthea-format EHR text file** to the same S3 bucket as `BUCKET_NAME` in `cdk/stacks/serverless_bedrock_stack.py`
- Send the key of that file to the API endpoint (`{ServerlessBedrockStack.APIGatewayURL}level-1-iz-classification`).
- The API will return a JSON outupt. In `output["bedrock_output"]["content"]["text"]`, you will find the following:
  - Matched **CDSi codes**
  - **Observation titles** for each matched code
  - **Condition references** for each matched code

#### Example of usage
```
curl -X POST \
  {ServerlessBedrockStack.APIGatewayURL}level-1-iz-classification \
  -H 'Content-Type: application/json' \
  -d '{"file_key": "s3_file.txt"}'
```

---

## 2. SNOMED-to-CDSi Mapping Deployment

> ✅ Tested on **Synthea HL7 CDA XML format** ([See Samples](https://synthetichealth.github.io/synthea-sample-data/downloads/latest/synthea_sample_data_ccda_latest.zip))

### Setup
1. In you AWS Account, create an S3 bucket that will be used to store and retrieve your HL7 CDA file

2. In `cdk/stacks/SNOMED_to_CDSi_stack.py`, set:
   - `BUCKET_NAME` : The name of the bucket you just created
   - `TABLE_NAME` (DynamoDB table to store SNOMED-CDSi mappings), this will be automatically created

3. Deploy:

```bash
cdk deploy ServerlessSNOMEDTOCDSi
```

4. Populate DynamoDB with a CSV:
   - From the root of of the project run 
   ``` 
   cd SNOMED_to_CDSi/one_time_parser 
   ```
   - Add (to this directory: `one_time_parser`) the CSV file you want to populate the table with
      - Format must include these 3 colums:
        - `Observation Code`
        - `Observation Title`
        - `SNOMED (Code)`
      - NOTE: SNOMED Code must be in `()`. If there are multiple SNOMED codes for one CDSi code, separate them with a `;`
   - Assign `CSV_FILE` to the name of the CSV file you just added
   - Assign `TABLE_NAME` to the same `TABLE_NAME` in `cdk/stacks/SNOMED_to_CDSi_stack.py`
   - Run the follwing to populate the DynamoDB table
   ```
   python3 main.py
   ```

### API Access

- CDK will output:
  ```
  ServerlessSNOMEDTOCDSi.APIGatewayURL = https://...
  ```
  - Also available in AWS Systems Manager Parameter Store under `/config/SNOMEDToCDSiAPIURL`

### Use
- Upload a **Synthea CDA XML file** to the same S3 bucket as `BUCKET_NAME` in `cdk/stacks/SNOMED_to_CDSi_stack.py`

### 2.1 Direct Matching Usage

- Send the key of that file to the API endpoint (`{ServerlessSNOMEDTOCDSi.APIGatewayURL}hl7-to-snomed-to-cdsi`).
- The API:
  - Extracts SNOMED codes from patient HL7 CDA document
  - Matches them to CDSi codes via **DynamoDB**
- Output: JSON mapping SNOMED to CDSi
  - CDSi Results based on mapping of SNOMED result to CDSi using the DynamoDB table created earlier. It includes:
    - CDSi codes
    - Observation Title (for each code)
    - SNOMED References (for each code)

#### Example of usage
```
curl -X POST \
  {ServerlessSNOMEDTOCDSi.APIGatewayURL}hl7-to-snomed-to-cdsi \
  -H 'Content-Type: application/json' \
  -d '{"s3_key": "patient.xml"}'
```
---
### 2.2 Extracting SNOMED Codes from Unstructured Text

- Send the key of that file to the API endpoint (`{ServerlessSNOMEDTOCDSi.APIGatewayURL}condition-snomed-to-cdsi`).
- The API:
  - Extracts SNOMED codes using AWS **Comprehend Medical**
  - Matches them to CDSi codes via **DynamoDB**
- Output:
  - SNOMED Results from AWS Medical comprehend: `output["snomed_results"]`
  - CDSi Results based on mapping of SNOMED result to CDSi using the DynamoDB table created earlier (`output["cdsi_results"]`). It includes:
    - CDSi codes
    - Observation Title (for each code)
    - SNOMED References (for each code) with their confidence scores from AWS Medical Comprehend 

#### Example of usage
```
curl -X POST \
  {ServerlessSNOMEDTOCDSi.APIGatewayURL}condition-snomed-to-cdsi \
  -H 'Content-Type: application/json' \
  -d '{"file_key": "patient.xml"}'
```

---
