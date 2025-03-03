import boto3

dynamodb = boto3.client('dynamodb')
ssm = boto3.client('ssm')

def get_s3_bucket_name():
    response = ssm.get_parameter(Name="/config/SSMSNOMEDToCDSiBucketName")
    return response["Parameter"]["Value"]

def get_mapping_table():
    response = ssm.get_parameter(Name="/config/DynamoSNOMEDToCDSiTableName")
    return response["Parameter"]["Value"]

def extract_snomed_codes_with_confidence(snomed_results, threshold=0.5, medical_condition_only=True):
    """Extract SNOMED codes and retain only the highest confidence entry for each code."""
    snomed_map = {}

    for result in snomed_results:
        if medical_condition_only and result.get("Category") != "MEDICAL_CONDITION":
            continue
        
        for concept in result.get("SNOMEDCTConcepts", []):
            confidence = concept["Score"]
            if confidence >= threshold:
                snomed_code = concept["Code"]

                # Check if we've seen this code before and update if confidence is higher
                if (snomed_code not in snomed_map) or (confidence > snomed_map[snomed_code]["confidence"]):
                    snomed_map[snomed_code] = {
                        "code": snomed_code,
                        "description": concept["Description"],
                        "confidence": confidence,
                        "text_reference": result["Text"]
                    }
                
    return list(snomed_map.values())

def snomed_to_cdsi_mapping_with_confidence(snomed_results, threshold=0.5, medical_condition_only=True):
    """Maps SNOMED codes to CDSi codes, ensuring only the highest confidence match per SNOMED code."""
    table_name = get_mapping_table()
    cdsi_dict = {}

    # Extracted and grouped SNOMED codes with highest confidence
    snomed_list = extract_snomed_codes_with_confidence(snomed_results, threshold, medical_condition_only)

    for snomed_item in snomed_list:
        snomed_code = snomed_item["code"]
        snomed_description = snomed_item["description"]
        confidence = snomed_item["confidence"]
        text_reference = snomed_item["text_reference"]

        # Query DynamoDB for CDSi codes linked to this SNOMED code
        query = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression='snomed_code = :snomed_code',
            ExpressionAttributeValues={
                ':snomed_code': {'N': str(snomed_code)}
            }
        )

        for item in query.get('Items', []):
            cdsi_code = int(item['cdsi_code']['N'])
            observation_title = item.get('observation_title', {}).get('S', '')

            if cdsi_code not in cdsi_dict:
                cdsi_dict[cdsi_code] = {
                    "observation_title": observation_title,
                    "snomed_references": {}
                }

            # Either add or replace if the new entry has higher confidence
            if (snomed_code not in cdsi_dict[cdsi_code]["snomed_references"]) or (
                confidence > cdsi_dict[cdsi_code]["snomed_references"][snomed_code]["confidence"]
            ):
                cdsi_dict[cdsi_code]["snomed_references"][snomed_code] = {
                    "snomed_code": snomed_code,
                    "snomed_description": snomed_description,
                    "confidence": confidence,
                    "text_reference": text_reference
                }

    # Convert nested dictionaries to lists for final output
    for cdsi_code, data in cdsi_dict.items():
        data["snomed_references"] = list(data["snomed_references"].values())

    return cdsi_dict

def snomed_to_cdsi_mapping_with_confidence(snomed_results, threshold=0.5, medical_condition_only=True):
    table_name = get_mapping_table()
    cdsi_dict = {}

    # Extract SNOMED codes with confidence filtering and optional category filtering
    snomed_list = extract_snomed_codes_with_confidence(snomed_results, threshold, medical_condition_only)

    for snomed_item in snomed_list:
        snomed_code = snomed_item["code"]
        snomed_description = snomed_item["description"]
        confidence = snomed_item["confidence"]
        text_reference = snomed_item["text_reference"]

        # Query DynamoDB for CDSi codes linked to this SNOMED code
        query = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression='snomed_code = :snomed_code',
            ExpressionAttributeValues={
                ':snomed_code': {'N': str(snomed_code)}
            }
        )

        for item in query.get('Items', []):
            cdsi_code = int(item['cdsi_code']['N'])
            observation_title = item.get('observation_title', {}).get('S', '')

            if cdsi_code not in cdsi_dict:
                cdsi_dict[cdsi_code] = {
                    "observation_title": observation_title,
                    "snomed_references": []
                }

            snomed_reference = {
                "snomed_code": int(snomed_code),
                "snomed_description": snomed_description,
                "confidence": confidence,
                "text_reference": text_reference
            }

            if snomed_reference not in cdsi_dict[cdsi_code]["snomed_references"]:
                cdsi_dict[cdsi_code]["snomed_references"].append(snomed_reference)

    return cdsi_dict
