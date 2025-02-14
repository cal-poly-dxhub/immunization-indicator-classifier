from typing import Set, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Set, Dict, List
import urllib.parse
import re
import boto3
import json 

dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')
ssm = boto3.client('ssm')

def get_s3_bucket_name():
    response = ssm.get_parameter(Name="/config/SSMSNOMEDToCDSiBucketName")
    return response["Parameter"]["Value"]

def get_mapping_table():
    response = ssm.get_parameter(Name="/config/DynamoSNOMEDToCDSiTableName")
    return response["Parameter"]["Value"]


def xml_to_snomed_set(xml_doc: str) -> Set[str]:
    soup = BeautifulSoup(xml_doc, features="html.parser")
    valid_snomed_codes = set()     
    
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
    td_list = [tr.get_text(strip=True) for tr in list(soup.find_all("tr"))]
    for i, td in enumerate(td_list):
        dates = date_pattern.findall(td)
        if len(dates) <= 1 or datetime.strptime(dates[1], "%Y-%m-%dT%H:%M:%SZ") > datetime.now():
            if re.search(r"snomed", td):
                valid_snomed_codes.add(re.search(r"\d+$", td).group(0))
    
    entries = soup.find_all("entry")
    for entry in entries:
        high = entry.find("high")
        code = entry.find("code", codeSystemName="SNOMED-CT")
        value = entry.find("value")
        if high and (not high.get("value") or not re.search(r'\d', high.get("value")) or datetime.strptime(high.get("value"), "%Y%m%d%H%M%S") > datetime.now()):
            high = None
        if code and value and not high:
            valid_snomed_codes.add(value.get("code"))

    return valid_snomed_codes


def snomed_set_with_cdsi_codes(snomed_set: Set[int]) -> Dict[int, Dict[str, List[Dict[str, str]]]]:
    table_name = get_mapping_table()
    cdsi_dict = {}

    for snomed in snomed_set:
        query = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression='snomed_code = :snomed_code',
            ExpressionAttributeValues={
                ':snomed_code': {'N': str(snomed)}  # Convert number to string for DynamoDB query
            }
        )

        if query['Items']:
            # Extract SNOMED description from first item
            snomed_description = query["Items"][0].get('snomed_description', {}).get('S', '')

            for item in query["Items"]:
                cdsi_code = int(item['cdsi_code']['N'])  # Convert CDSi code to int
                observation_title = item.get('observation_title', {}).get('S', '')  # Observation title

                # Store in dictionary with CDSi as primary key
                if cdsi_code not in cdsi_dict:
                    cdsi_dict[cdsi_code] = {
                        "observation_title": observation_title,
                        "snomed_references": []
                    }

                # Add SNOMED reference (avoiding duplicates)
                snomed_entry = {"snomed_code": int(snomed), "snomed_description": snomed_description}
                if snomed_entry not in cdsi_dict[cdsi_code]["snomed_references"]:
                    cdsi_dict[cdsi_code]["snomed_references"].append(snomed_entry)

    return cdsi_dict

def lambda_handler(event, context): 
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        if "s3_key" not in body:
            raise Exception("Missing 's3_key' in request body")
        
        # Get S3 object
        bucket = get_s3_bucket_name()
        key = urllib.parse.unquote_plus(body['s3_key'], encoding='utf-8')
        response = s3.get_object(Bucket=bucket, Key=key)
        
        print(f"CONTENT TYPE: {response['ContentType']}")
        if response['ContentType'] not in ['application/xml', 'text/xml']:
            raise Exception("XML was not passed in")  
        
        # Extract SNOMED codes from XML
        snomed_set = xml_to_snomed_set(response['Body'].read().decode('utf-8'))

        # Retrieve CDSi mapping with SNOMED references
        cdsi_dictionary = snomed_set_with_cdsi_codes(snomed_set)
        
        print(f"CDSi DICTIONARY: {json.dumps(cdsi_dictionary, indent=2)}")
        response['Body'].close()
        
        return {
            "statusCode": 200,
            "body": json.dumps(cdsi_dictionary)
        }
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
