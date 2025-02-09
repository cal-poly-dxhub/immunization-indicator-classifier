from typing import Set, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
import urllib.parse
import re
import boto3
import json 


TABLE_NAME = "snomed-to-cdsi"
dynamodb = boto3.client('dynamodb')
lambda_client = boto3.client('lambda')
s3 = boto3.client('s3')

def xml_to_snomed_set(xml_doc : str) -> Set[str]:
    soup = BeautifulSoup(xml_doc, features="html.parser")
    valid_snomed_codes = set()     
    
    # for each table row tag, validate table data entries and then save relevant data
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
    td_list = [tr.get_text(strip=True) for tr in list(soup.find_all("tr"))]
    for i, td in enumerate(td_list):
        # ! this might be a buggy way of getting dates and validating but works from schema of this specific xml doc
        dates = date_pattern.findall(td)
        if len(dates) <= 1 or datetime.strptime(dates[1], "%Y-%m-%dT%H:%M:%SZ") > datetime.now():
            if re.search(r"snomed", td):
                valid_snomed_codes.add(re.search(r"\d+$", td).group(0))

    # for each entry tag, validate the data entries and then save relevant data
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
    
def snomed_set_with_cdsi_codes(snomed_set : Set[str]) -> Dict[str, str]:
    snomed_dict = {}
    for i, snomed in enumerate(snomed_set):
        query = dynamodb.query(
            TableName=TABLE_NAME,
            KeyConditionExpression='snomed_code = :snomed_code',
            ExpressionAttributeValues={
                ':snomed_code': {'S': snomed}
            }
        )
        if query['Items']:
            snomed_dict[snomed] = [item['cdsi_code']['S'] for item in query["Items"]]
    return snomed_dict
            

def lambda_handler (event, context): 
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        response = s3.get_object(Bucket=bucket, Key=key)
        
        print(f"CONTENT TYPE: {response['ContentType']}")
        if response['ContentType'] not in ['application/xml', 'text/xml']:
            raise Exception("XML was not passed in")  
        
        snomed_set = xml_to_snomed_set(response['Body'].read().decode('utf-8'))
        snomed_dictionary  = snomed_set_with_cdsi_codes(snomed_set)

        print(f"SNOMED DICTIONARY: {json.dumps(snomed_dictionary)}")
        response['Body'].close()
        
        return {
            "statusCode": 200,
            "body": json.dumps(snomed_dictionary)
        }
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }



