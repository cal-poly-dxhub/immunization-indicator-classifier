# one time parser
# SNOMED (Code) to CDSi code

import boto3.dynamodb
import polars as pl
import re

import boto3
from boto3.dynamodb.types import TypeSerializer
dynamodb = boto3.client('dynamodb')
TABLE_NAME = "snomed-to-cdsi"

CSV_FILE = "CDSi ScheduleSupportingData- Coded Observations-508_v4.60_withRSV.csv"

df = (pl.scan_csv(CSV_FILE)).filter((pl.col("Observation Title").is_not_null()) & (pl.col("SNOMED (Code)")).is_not_null())
df =  df.collect()
        
for i, obs in enumerate(df.rows(named=True)):
    # Regex to capture description and SNOMED code
    snomed_pattern = re.compile(r'([^\(]+)\s\((\d+)\)')  # Capture description before the parentheses
    snomed_match = snomed_pattern.search(obs["SNOMED (Code)"])  # Search for the pattern

    if snomed_match:
        description = snomed_match.group(1).strip()  # Extract the description
        snomed_code = snomed_match.group(2)  # Extract the SNOMED code

        print(obs["Observation Code"], obs["Observation Title"])
        print(snomed_code, description)

        try:
            serializer = TypeSerializer()
            # Now store both the SNOMED code and description in DynamoDB along with other details
            dynamodb.put_item(
                TableName=TABLE_NAME,
                Item={
                    "snomed_code": serializer.serialize(int(snomed_code)),
                    "cdsi_code": serializer.serialize(int(obs["Observation Code"] + 2)),
                    "snomed_description": serializer.serialize(description),
                    "observation_title": serializer.serialize(obs["Observation Title"])
                }
            )
        except Exception as e:
            print(e)
            print(f"Failed to append SNOMEDS associated with {obs['Observation Code']}")
