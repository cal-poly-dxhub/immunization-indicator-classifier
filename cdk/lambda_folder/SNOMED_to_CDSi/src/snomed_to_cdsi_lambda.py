import json
from snomed_to_cdsi_logic import snomed_set_with_cdsi_codes

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        if "snomed_codes" not in body or not isinstance(body["snomed_codes"], list):
            raise ValueError("Invalid request body.  Must contain a 'snomed_codes' list.")

        snomed_codes = set(map(int, body["snomed_codes"]))  # Convert to set of integers

        cdsi_dictionary = snomed_set_with_cdsi_codes(snomed_codes)

        return {
            "statusCode": 200,
            "body": json.dumps(cdsi_dictionary)
        }

    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }