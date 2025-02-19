import time
import boto3
from bs4 import BeautifulSoup
from datetime import datetime
import re
import urllib.parse

# Initialize S3 client
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')


def xml_to_snomed_set(xml_doc: str) -> set[str]:
    soup = BeautifulSoup(xml_doc, features="xml")
    valid_snomed_codes = set()

    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
    td_list = [tr.get_text(strip=True) for tr in list(soup.find_all("tr"))]
    for i, td in enumerate(td_list):
        dates = date_pattern.findall(td)
        if len(dates) <= 1 or datetime.strptime(dates[1], "%Y-%m-%dT%H:%M:%SZ") > datetime.now():
            if re.search(r"snomed", td):
                try:
                    valid_snomed_codes.add(re.search(r"\d+$", td).group(0))
                except AttributeError:
                    print(f"Could not extract SNOMED from: {td}")

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


def snomed_set_with_cdsi_codes(snomed_set: set[int], table_name: str) -> dict[int, dict[str, list[dict[str, str]]]]:
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


def main():
    bucket_name = "hl7-xml-to-snomed-code"  # Replace with your bucket name
    s3_key = "Alena861_Danna372_Gusikowski974_bd2a8021-2868-6dd2-c17f-bfd7c36fe247.xml"  # Replace with your S3 key
    table_name = "snomed-to-cdsi" # Replace with your DynamoDB table name

    start_time = time.time()

    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        xml_content = response['Body'].read().decode('utf-8')
        response['Body'].close()
    except Exception as e:
        print(f"Error getting object from S3: {e}")
        return

    s3_end_time = time.time()
    print(f"S3 retrieval time: {s3_end_time - start_time:.4f} seconds")

    snomed_codes = xml_to_snomed_set(xml_content)
    xml_end_time = time.time()
    print(f"XML Parsing Time: {xml_end_time - s3_end_time:.4f} seconds")


    dynamodb_start_time = time.time()
    cdsi_dictionary = snomed_set_with_cdsi_codes(snomed_codes, table_name)
    dynamodb_end_time = time.time()
    print(f"DynamoDB Time: {dynamodb_end_time - dynamodb_start_time:.4f} seconds")

    end_time = time.time()

    print(f"Extracted SNOMED codes: {snomed_codes}")
    print(f"Number of extracted codes: {len(snomed_codes)}")
    print(f"Total execution time: {end_time - start_time:.4f} seconds")
    print(f"CDSI Dictionary: {cdsi_dictionary}")


if __name__ == "__main__":
    main()

