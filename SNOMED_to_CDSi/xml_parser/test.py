import time
import boto3
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import Set
from bs4 import BeautifulSoup

# Initialize S3 client
s3 = boto3.client('s3')



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
def main():
    bucket_name = "hl7-xml-to-snomed-code" 
    s3_key = "Alena861_Danna372_Gusikowski974_bd2a8021-2868-6dd2-c17f-bfd7c36fe247.xml"  

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
    end_time = time.time()

    print(f"Extracted SNOMED codes: {snomed_codes}")
    print(f"Number of extracted codes: {len(snomed_codes)}")
    print(f"Total execution time: {end_time - start_time:.4f} seconds")
    print(f"Parsing Time: {end_time - s3_end_time:.4f} seconds")


if __name__ == "__main__":
    main()