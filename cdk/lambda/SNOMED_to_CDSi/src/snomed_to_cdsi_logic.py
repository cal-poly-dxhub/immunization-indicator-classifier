import boto3
from typing import Set, Dict, List

dynamodb = boto3.client('dynamodb')
ssm = boto3.client('ssm')

def get_s3_bucket_name():
    response = ssm.get_parameter(Name="/config/SSMSNOMEDToCDSiBucketName")
    return response["Parameter"]["Value"]

def get_mapping_table():
    response = ssm.get_parameter(Name="/config/DynamoSNOMEDToCDSiTableName")
    return response["Parameter"]["Value"]

def snomed_set_with_cdsi_codes(snomed_set: Set[int]) -> Dict[int, Dict[str, List[Dict[str, str]]]]:
    table_name = get_mapping_table()
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
