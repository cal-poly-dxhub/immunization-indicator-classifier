import requests
import boto3

ssm = boto3.client("ssm")
hl7_to_snomed_direct_route = "hl7-to-snomed-to-cdsi"
comprehend_condition_route = "condition-snomed-to-cdsi"
comprehend_medication_route = "medication-rxnorm"


def get_level1_iz_classification_endpoint():
    response = ssm.get_parameter(
        Name="/config/Level1IZClassificationEndpoint",
        WithDecryption=False
    )
    return response['Parameter']['Value']

def get_hl7_to_snomed_to_cdsi_endpoint():
    response = ssm.get_parameter(
        Name="/config/SNOMEDToCDSiAPIURL",
        WithDecryption=False
    )
    return response['Parameter']['Value']

def call_condition_api(file_key):
    url = get_level1_iz_classification_endpoint()
    headers = {"Content-Type": "application/json"}
    data = {"file_key": file_key}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response_json = response.json()
        try:
            return response_json["bedrock_output"]["content"][0]["text"]
        except KeyError:
            return "Error: Unexpected response format"
    else:
        return "Error: Failed to get response from API"
    
def call_snomed_to_cdsi_api(file_key):
    url = get_hl7_to_snomed_to_cdsi_endpoint() + hl7_to_snomed_direct_route
    headers = {"Content-Type": "application/json"}
    data = {"s3_key": file_key}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()  # Return JSON response
    else:
        return {"error": "Failed to get response from API"}
    

def call_condition_snomed_to_cdsi_api(file_key):
    url = get_hl7_to_snomed_to_cdsi_endpoint() + comprehend_condition_route
    #url = "https://localhost:8501/condition-snomed-to-cdsi"
    headers = {"Content-Type": "application/json"}
    data = {"s3_key": file_key}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        #response = condition_comprehend_lambda.lambda_handler(data, None)
       
        
        # Check if the response is successful
        if response.status_code == 200:
            # Log the raw response data for debugging
            #print("API Response:", response.json())  # Print out the full JSON response
            return response.json()  # Return JSON response
        else:
            # If the API fails, print the error and status code
            print("API Error:", response.status_code, response.text)
            return {"error": f"Failed to get response from API, Status code: {response.status_code}"}
    
    except Exception as e:
        print("Exception occurred while calling API:", e)
        return {"error": f"Exception occurred: {str(e)}"}



def call_medication_rxnorm_api(file_key):
    url = get_hl7_to_snomed_to_cdsi_endpoint() + comprehend_medication_route
    headers = {"Content-Type": "application/json"}
    data = {"s3_key": file_key}

    try:
        response = requests.post(url, headers=headers, json=data)
        #response = medication_comprehend_lambda.lambda_handler(data, None)
        
        # Check if the response is successful
        if response.status_code == 200:
            # Log the raw response data for debugging
            #print("API Response:", response.json())  # Print out the full JSON response
            return response.json()
            #return json.dumps(response)  # Return JSON response
        else:
            # If the API fails, print the error and status code
            print("API Error:", response.status_code, response.text)
            return {"error": f"Failed to get response from API, Status code: {response.status_code}"}
    
    except Exception as e:
        print("Exception occurred while calling API:", e)
        return {"error": f"Exception occurred: {str(e)}"}
