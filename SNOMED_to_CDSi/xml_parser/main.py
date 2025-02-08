from typing import Set, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
import re
import boto3
TABLE_NAME = "snomed-to-cdsi"
dynamodb = boto3.client('dynamodb')

def xml_to_snomed_set(xml_doc : str) -> Set[str]:
    if not re.search(r'\.xml$', xml_doc):
        raise Exception("XML was not passed in")  
    with open(xml_doc, "r") as xml:
        soup = BeautifulSoup(xml, features="xml")
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
            
if __name__ == "__main__":
    # TEST_XML_FILE = "Ada662_Sari509_Balistreri607_dbc4a3f7-9c69-4435-3ce3-4e1988ab6b91.xml"
    # TEST_XML_FILE = "Adrianne466_Jonnie215_Glover433_99d3b9b2-46c1-ef9e-da70-81ac3d365f52.xml"
    TEST_XML_FILE = "Alena861_Danna372_Gusikowski974_bd2a8021-2868-6dd2-c17f-bfd7c36fe247.xml"
    set = xml_to_snomed_set(TEST_XML_FILE)
    dictionary  = snomed_set_with_cdsi_codes(set)
    print(dictionary)





#! NOTES:
#! some codes are general e.g. 314529007


# take in xml. return valid SNOMED to CDSi code pairings for SNOMED that fit active criteria and are in DynamoDB
# strucutre

# only look at cases where second td is passed current date or where second td is empty (meaning ongoing) and use corresponding snomed in fourth td
'''
        <tr>
          <td>1976-09-18T23:01:05Z</td>
          <td></td>
          <td ID="conditions-desc-1">Risk activity involvement (finding)</td>
          <td ID="conditions-code-1">http://snomed.info/sct 160968000</td>
        </tr>
'''

# only look at cases where the effectiveTime high value is passed current date or where effectiveTime high value is missing
'''
        <entry typeCode="DRIV">
      <act classCode="ACT" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
        <templateId root="2.16.840.1.113883.10.20.22.4.3" extension="2015-08-01"/>
        <!-- Problem act template -->
        <id root="da6caa85-4086-ad25-15d2-e19a0b44bac3"/>
        <code nullFlavor="NA"/>
        <statusCode code="active"/>
        <effectiveTime>
          <low value="19990807215747"/>
          
        </effectiveTime>
        <entryRelationship typeCode="SUBJ" inversionInd="false">
          <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
            <!--Problem observation template - NOT episode template-->
            <id root="6a64be0d-333e-3aa2-2562-0b26a50c7790"/>
            <code code="64572001" displayName="Condition" codeSystem="2.16.840.1.113883.6.96" codeSystemName="SNOMED-CT">
              <translation code="75323-6" displayName="Condition" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC"/>
            </code>
            <text>
              <reference value="#conditions-desc-5"/>
            </text>
            <statusCode code="completed"/>
            <effectiveTime>
              <low value="19990807215747"/>
              
            </effectiveTime>
            <priorityCode code="8319008" codeSystem="2.16.840.1.113883.6.96" displayName="Principal diagnosis" />
        <value xsi:type="CD" code="162864005" codeSystem="2.16.840.1.113883.6.96" displayName="Body mass index 30+ - obesity (finding)">
          <originalText><reference value="#conditions-desc-5"/></originalText>
        </value>
          </observation>
        </entryRelationship>
      </act>
    </entry>
'''
#55