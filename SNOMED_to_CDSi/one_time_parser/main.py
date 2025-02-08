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
    # test = re.compile(r'(?<!\()\d+(?!\))') # test to see nums without parens
    deparenthesized_nums = re.compile(r'\((\d+)\)')
    snomeds = deparenthesized_nums.findall(obs["SNOMED (Code)"])
    if snomeds:
        print(obs["Observation Code"], obs["Observation Title"])
        print(snomeds)
        #! LEFT OFF ON ADDING TO DYNAMO TABLE
    try: 
        serializer = TypeSerializer()
        for snomed in snomeds:
            dynamodb.put_item(
                TableName = TABLE_NAME,
                Item = {
                    "snomed_code": serializer.serialize(str(snomed)),
                    "cdsi_code": serializer.serialize(str(obs["Observation Code"] + 2))
                }
            )
    except (Exception) as e:
        print(e)
        print(f"failed to append SNOMEDS associated with {obs["Observation Code"]}")
        





# Data Exploration

#! There are duplicate SNOMEDs, so they map one to many
#? List of duplicate SNOMEDs
# {'31323000': 2, '13645005': 2, '87433001': 2, '86406008': 2, '11723008': 2, '165806002': 2, '159138004': 2, '14698002': 2, '24932003': 8, '159282002': 4, '59881000': 2, '44172002': 2, '223366009': 3, '451291000124104': 2, '116859006': 3, '77128003': 2, '62479008': 2, '70995007': 2, '83911000119104': 2, '40108008': 2, '417357006': 2}
#? code to confirm that SNOMEDs can duplicate 
# from collections import Counter
# agg = []
#         agg += snomeds
# print({key : val for key, val in Counter(agg).items() if val > 1})


#! DB decision: 
# ? DynamoDB
# * RDMS 
# Joins are expensive in lambda
# * Graph
# Too much for simple look up
# * DynamoDB
# single look up
# no db mangement
# serverless
# can add revesr index later if need be