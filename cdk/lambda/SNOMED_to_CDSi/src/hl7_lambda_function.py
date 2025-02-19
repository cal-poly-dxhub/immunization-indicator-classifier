# from typing import Set, Dict, List
# from bs4 import BeautifulSoup
# from datetime import datetime
# import urllib.parse
# import re
# import boto3
# import json
# from snomed_to_cdsi_logic import snomed_set_with_cdsi_codes, get_s3_bucket_name, get_mapping_table

# s3 = boto3.client('s3')

# def xml_to_snomed_set(xml_doc: str) -> Set[str]:
#     soup = BeautifulSoup(xml_doc, features="html.parser")
#     valid_snomed_codes = set()     
    
#     date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
#     td_list = [tr.get_text(strip=True) for tr in list(soup.find_all("tr"))]
#     for i, td in enumerate(td_list):
#         dates = date_pattern.findall(td)
#         if len(dates) <= 1 or datetime.strptime(dates[1], "%Y-%m-%dT%H:%M:%SZ") > datetime.now():
#             if re.search(r"snomed", td):
#                 valid_snomed_codes.add(re.search(r"\d+$", td).group(0))
    
#     entries = soup.find_all("entry")
#     for entry in entries:
#         high = entry.find("high")
#         code = entry.find("code", codeSystemName="SNOMED-CT")
#         value = entry.find("value")
#         if high and (not high.get("value") or not re.search(r'\d', high.get("value")) or datetime.strptime(high.get("value"), "%Y%m%d%H%M%S") > datetime.now()):
#             high = None
#         if code and value and not high:
#             valid_snomed_codes.add(value.get("code"))

#     return valid_snomed_codes


# def lambda_handler(event, context):
#     try:
#         # Parse request body
#         body = json.loads(event.get("body", "{}"))
#         if "s3_key" not in body:
#             raise Exception("Missing 's3_key' in request body")

#         # Get S3 object
#         bucket = get_s3_bucket_name()
#         key = urllib.parse.unquote_plus(body['s3_key'], encoding='utf-8')
#         response = s3.get_object(Bucket=bucket, Key=key)

#         print(f"CONTENT TYPE: {response['ContentType']}")
#         if response['ContentType'] not in ['application/xml', 'text/xml']:
#             raise Exception("XML was not passed in")

#         # Extract SNOMED codes from XML
#         snomed_set = xml_to_snomed_set(response['Body'].read().decode('utf-8'))

#         # Retrieve CDSi mapping with SNOMED references
#         cdsi_dictionary = snomed_set_with_cdsi_codes(snomed_set)

#         print(f"CDSi DICTIONARY: {json.dumps(cdsi_dictionary, indent=2)}")
#         response['Body'].close()

#         return {
#             "statusCode": 200,
#             "body": json.dumps(cdsi_dictionary)
#         }

#     except Exception as e:
#         print(f"Error processing file: {str(e)}")
#         return {
#             "statusCode": 500,
#             "body": json.dumps({"error": str(e)})
#         }

from typing import Set
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse
import re
import boto3
import json
import time  # Import time module
from snomed_to_cdsi_logic import snomed_set_with_cdsi_codes, get_s3_bucket_name

s3 = boto3.client('s3')

import os
print(os.listdir())
try:
    import lxml
    print("lxml imported successfully")
except ImportError:
    print("lxml import failed")

def xml_to_snomed_set(xml_doc: str) -> Set[str]:
    soup = BeautifulSoup(xml_doc, features="xml")
    valid_snomed_codes = set()

    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

    # Find all <section> elements with the title "Problems"
    for section in soup.find_all("section"):
        if section.find("title") and "Problems" in section.find("title").text:
            # Find all <tr> elements within the section
            for tr in section.find_all("tr"):
                # Find the <td> element that contains the code
                td = tr.find("td", attrs={"ID": re.compile(r"conditions-code-\d+")})
                if td:
                    dates = date_pattern.findall(td.text)
                    if len(dates) <= 1 or datetime.strptime(dates[1], "%Y-%m-%dT%H:%M:%SZ") > datetime.now():
                        # Extract the code from the <td> element
                        code_text = td.text.strip()
                        # Use regular expression to find the SNOMED code
                        match = re.search(r"\d+$", code_text)
                        if match:
                            valid_snomed_codes.add(match.group(0))
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
    start_time = time.time()  # Start timing the function execution
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        if "s3_key" not in body:
            raise Exception("Missing 's3_key' in request body")

        # Get S3 object
        bucket = get_s3_bucket_name()
        key = urllib.parse.unquote_plus(body['s3_key'], encoding='utf-8')
        s3_start_time = time.time()  # Start timing S3 retrieval
        response = s3.get_object(Bucket=bucket, Key=key)
        s3_end_time = time.time()  # End timing S3 retrieval
        print(f"S3 Retrieval Time: {s3_end_time - s3_start_time:.4f} seconds")

        print(f"CONTENT TYPE: {response['ContentType']}")
        if response['ContentType'] not in ['application/xml', 'text/xml']:
            raise Exception("XML was not passed in")

        # Extract SNOMED codes from XML
        xml_start_time = time.time()  # Start timing XML parsing
        xml_content = response['Body'].read().decode('utf-8')  # Read the XML content
        snomed_set = xml_to_snomed_set(xml_content)
        xml_end_time = time.time()  # End timing XML parsing
        print(f"XML Parsing Time: {xml_end_time - xml_start_time:.4f} seconds")
        print(f"Number of SNOMED codes extracted: {len(snomed_set)}")

        # Retrieve CDSi mapping with SNOMED references
        cdsi_start_time = time.time()  # Start timing CDSi mapping
        cdsi_dictionary = snomed_set_with_cdsi_codes(snomed_set)
        cdsi_end_time = time.time()  # End timing CDSi mapping
        print(f"CDSi Mapping Time: {cdsi_end_time - cdsi_start_time:.4f} seconds")

        print(f"CDSi DICTIONARY: {json.dumps(cdsi_dictionary, indent=2)}")
        response['Body'].close()

        end_time = time.time()  # End timing the function execution
        print(f"Total Execution Time: {end_time - start_time:.4f} seconds")

        return {
            "statusCode": 200,
            "body": json.dumps(cdsi_dictionary)
        }

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        end_time = time.time()  # End timing the function execution
        print(f"Total Execution Time: {end_time - start_time:.4f} seconds")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }