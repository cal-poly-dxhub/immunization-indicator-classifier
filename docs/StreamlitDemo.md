# Streamlit Demo Guide

This project includes a **Streamlit app** for demo purposes to interact with the deployed APIs.

> ⚠️ The Streamlit app can only be used **after completing deployment**.  
> See the [Deployment Guide](./Deployment.md) for detailed deployment steps.

---

## Prerequisites

- Make sure you have valid **AWS API keys** available in your environment (for calling the deployed APIs).

---

## How to Run the Streamlit App

From the **root** of the project:

```bash
cd streamlit
streamlit run app.py
```

This will launch the app with a sidebar where you can select from **three pages**, each corresponding to a deployed solution:

---

## Available Pages

### 1. LLM-Based Classification

- **Purpose:** Match condition text to CDSi codes using an LLM.
- **Input Required:**  
  - Provide your **Text EHR S3 file key** (i.e., the filename in your S3 bucket).
- **Note:**  
  - This must be from the **same S3 bucket** used in `BUCKET_NAME` in `cdk/stacks/serverless_bedrock_stack.py`,  
    or retrieved from the AWS Systems Manager (SSM) Parameter Store key:  
    ```
    /config/BUCKET_NAME
    ```

---

### 2. SNOMED-to-CDSi Mapping: Direct Mapping

- **Purpose:** Match SNOMED codes extracted from structured HL7 CDA files to CDSi codes.
- **Input Required:**  
  - Provide your **HL7 CDA EHR S3 file key**.
- **Note:**  
  - The file must be from the **same bucket** defined in `cdk/stacks/SNOMED_to_CDSi_stack.py`,  
    or found via AWS Systems Manager (SSM) Parameter Store key:  
    ```
    /config/SSMSNOMEDToCDSiBucketName
    ```

---

### 3. SNOMED-to-CDSi Mapping: Extracting SNOMED Codes from Unstructured Text (via AWS Medical Comprehend)

- **Purpose:** Use AWS Medical Comprehend to extract SNOMED codes from unstructured HL7 CDA files, then map to CDSi.
- **Input Required:**  
  - Provide your **HL7 CDA EHR S3 file key**.
- **Note:**  
  - File must come from the **same bucket** as above:
    ```
    /config/SSMSNOMEDToCDSiBucketName
    ```
    (in AWS Systems Manager (SSM) Parameter Store)

---

Happy exploring!
