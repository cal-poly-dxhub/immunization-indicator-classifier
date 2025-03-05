import boto3
import json
import urllib.parse
from extract_med import get_patient_meds


# Initialize AWS clients
client = boto3.client('comprehendmedical')
dynamodb = boto3.client('dynamodb')
ssm = boto3.client('ssm')

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

def get_s3_bucket_name():
    response = ssm.get_parameter(Name="/config/SSMSNOMEDToCDSiBucketName")
    return response["Parameter"]["Value"]

def extract_rxnorm_codes_with_confidence(rxnorm_results, threshold=0.5):
    """Extract RxNorm codes and confidence, optionally filtered by threshold."""
    rxnorm_with_confidence = []
    
    for result in rxnorm_results:
        for concept in result.get("RxNormConcepts", []):
            confidence = concept["Score"]
            if confidence >= threshold:
                rxnorm_with_confidence.append({
                    "code": concept["Code"],
                    "description": concept["Description"],
                    "confidence": confidence,
                    "text_reference": result["Text"]
                })
                
    return rxnorm_with_confidence

def lambda_handler(event, context):
    """
    Lambda handler function to extract RxNorm codes and their confidence from medication data.
    Args:
        event (dict): The event dictionary containing the S3 file key.
        context (object): The Lambda context object.
    
    Returns:
        dict: A dictionary containing the RxNorm results with codes, descriptions, and confidence scores.
    """
    body = json.loads(event.get("body", "{}"))
    if "s3_key" not in body:
        raise Exception("Missing 's3_key' in request body")
    
    print(f"s3 key: {body['s3_key']}")

    bucket_name = get_s3_bucket_name()
    s3_key = body['s3_key'] 

    # Retrieve the XML file content from S3
    xml_content = get_file_from_s3(bucket_name, s3_key)

    if not xml_content:
        return {
            'statusCode': 500,
            'body': 'Error: Could not retrieve file from S3'
        }
    
    # Extract patient medication records from the XML content
    patient_records = get_patient_meds(xml_content)  
    patient_medications = patient_records['medications']
    
    # Join all medications into a single text string
    medications_text = "\n".join(patient_medications)
    
    # Call comprehend API to extract RxNorm concepts
    comprehend = client.infer_rx_norm(Text=medications_text)
    
    # Process RxNorm results with confidence filtering
    rxnorm_results = extract_rxnorm_codes_with_confidence(comprehend.get("Entities", []), threshold=0.5)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'rxnorm_results': rxnorm_results
        })
    }
