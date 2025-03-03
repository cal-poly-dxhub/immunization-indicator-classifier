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

def find_section_by_template_id(root, target_template_id):
    """Manually search for a section with a matching templateId@root."""
    for section in root.findall(".//section"):
        template_id = section.find("./templateId")
        if template_id is not None and template_id.attrib.get("root") == target_template_id:
            return section
    return None

def xml_to_snomed_set(xml_doc: str) -> Set[str]:
    """Extract SNOMED codes from Problems (current only) and Surgeries (all) sections."""
    root = ET.fromstring(xml_doc)
    strip_namespaces(root)
    valid_snomed_codes = set()
    
    def process_table_rows(section, check_end_date):
        date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
        for tr in section.findall(".//tr"):
            td_text = "".join(tr.itertext()).strip()
            dates = date_pattern.findall(td_text)
            
            # Skip rows where the stop date is in the past (only for problem sections)
            if check_end_date and len(dates) > 1 and datetime.strptime(dates[1], "%Y-%m-%dT%H:%M:%SZ") <= datetime.now():
                continue
            match = re.search(r"\d+$", td_text)
            if match:
                valid_snomed_codes.add(match.group(0))

    # Find sections using manual search
    problems_section = find_section_by_template_id(root, "2.16.840.1.113883.10.20.22.2.5.1")
    if problems_section is not None:
        process_table_rows(problems_section, check_end_date=True)

    surgeries_section = find_section_by_template_id(root, "2.16.840.1.113883.10.20.22.2.7.1")
    if surgeries_section is not None:
        process_table_rows(surgeries_section, check_end_date=False)

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
