import boto3
import json
import urllib.parse
from extract_med import get_patient_meds
from snomed_to_cdsi_logic import get_s3_bucket_name, snomed_to_cdsi_mapping_with_confidence

client = boto3.client('comprehendmedical')
dynamodb = boto3.client('dynamodb')

def get_file_from_s3(bucket_name: str, file_key: str) -> str:
    """
    Retrieves a file from S3 as a string.

    Args:
        bucket_name (str): The name of the S3 bucket.
        file_key (str): The key of the file in the S3 bucket.

    Returns:
        str: The file content as a string, or None if there was an error.
    """
    s3 = boto3.client('s3')
    try:
        key = urllib.parse.unquote_plus(file_key, encoding='utf-8')
        response = s3.get_object(Bucket=bucket_name, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        return file_content
    except Exception as e:
        print(f"Error retrieving file from S3: {e}")
        return None

def lambda_handler(event, context):
    """
    Lambda handler function.

    Args:
        event (dict): The event dictionary containing the S3 file key.
        context (object): The Lambda context object.

    Returns:
        dict: A dictionary containing the SNOMED and CDSI results as strings.
    """
    body = json.loads(event.get("body", "{}"))
    if "s3_key" not in body:
        raise Exception("Missing 's3_key' in request body")
    
    print(f"s3 key: {body['s3_key']}")

    bucket_name = get_s3_bucket_name()
    s3_key = body['s3_key'] 

    xml_content = get_file_from_s3(bucket_name, s3_key)

    if not xml_content:
        return {
            'statusCode': 500,
            'body': 'Error: Could not retrieve file from S3'
        }
    
    patient_records = get_patient_meds(xml_content)  
    patient_problems = patient_records['problems']
    patient_problems = "\n".join(patient_problems)
    comprehend = client.infer_snomedct(Text=patient_problems)
    cdsi = snomed_to_cdsi_mapping_with_confidence(comprehend["Entities"], threshold=0.3, medical_condition_only=True)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'snomed_results': comprehend["Entities"],
            'cdsi_results': cdsi
        })
    }
