from typing import Set, Dict, List
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse
import re
import boto3
import json
from snomed_to_cdsi_logic import snomed_set_with_cdsi_codes, get_s3_bucket_name, get_mapping_table

s3 = boto3.client('s3')

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
