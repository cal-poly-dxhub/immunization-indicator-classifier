from typing import Set
from datetime import datetime
import urllib.parse
import re
import boto3
import json
from snomed_to_cdsi_logic import snomed_set_with_cdsi_codes, get_s3_bucket_name
import xml.etree.ElementTree as ET

s3 = boto3.client('s3')

def strip_namespaces(element):
    """Recursively remove namespace prefixes from tags."""
    for elem in element.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]

def xml_to_snomed_set(xml_doc: str) -> Set[str]:
    root = ET.fromstring(xml_doc)
    strip_namespaces(root) 

    valid_snomed_codes = set()
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

    # Handle <tr> text extraction (like your original code)
    for tr in root.findall(".//tr"):
        td_text = "".join(tr.itertext()).strip()
        dates = date_pattern.findall(td_text)
        if len(dates) <= 1 or datetime.strptime(dates[1], "%Y-%m-%dT%H:%M:%SZ") > datetime.now():
            if "snomed" in td_text.lower():
                match = re.search(r"\d+$", td_text)
                if match:
                    valid_snomed_codes.add(match.group(0))

    # Handle <entry> extraction with optional <high>, <code>, <value>
    for entry in root.findall(".//entry"):
        high = entry.find(".//high")
        code = entry.find(".//code[@codeSystemName='SNOMED-CT']")
        value = entry.find(".//value")

        high_valid = True
        if high is not None:
            high_value = high.attrib.get("value")
            if not high_value or not re.search(r'\d', high_value) or datetime.strptime(high_value, "%Y%m%d%H%M%S") > datetime.now():
                high_valid = False

        if code is not None and value is not None and not high_valid:
            snomed_code = value.attrib.get("code")
            if snomed_code:
                valid_snomed_codes.add(snomed_code)

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
