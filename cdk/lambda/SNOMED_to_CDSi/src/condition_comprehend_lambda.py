import boto3
import bs4
import json
from extract_med import get_patient_meds
from extract_code import extract_snomedct 
from snomed_to_cdsi_logic import get_mapping_table, get_s3_bucket_name  # Assuming this is where your CDSI mapping functions are


# Initialize ComprehendMedical client
client = boto3.client('comprehendmedical')

# DynamoDB client
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
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
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
    if "file_key" not in body:
        raise Exception("Missing 'file_key' in request body")
    
    print(f"File key: {body['file_key']}")

    bucket_name = get_s3_bucket_name()
    file_key = body['file_key'] 

    print(f"Bucket name: {bucket_name}")

    xml_content = get_file_from_s3(bucket_name, file_key)

    if not xml_content:
        return {
            'statusCode': 500,
            'body': 'Error: Could not retrieve file from S3'
        }
    
    patient_records = get_patient_meds(xml_content)  

    print(f"Patient records: {patient_records}")

    patient_problems = patient_records['problems']
    snomed_output = extract_snomedct(patient_problems)  

    return {
        'statusCode': 200,
        'body': {
            'snomed_results': patient_problems
        }
    }