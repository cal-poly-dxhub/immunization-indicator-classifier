import polars as pl
import boto3
import json
import re
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeSerializer


diseases_and_attributes = []

# create a Bedrock Runtime client in us-west-2
client = boto3.client("bedrock-runtime", region_name="us-west-2")
model_id = "anthropic.claude-3-haiku-20240307-v1:0"

# create DynamoDB client
dynamodb = boto3.client("dynamodb")
diseases_table = "diseases-attributes"


# 1.  Find xlsx file with RSV CDSi codes and export a cvs with all columns
CSV_DATA = "CDSi ScheduleSupportingData- Coded Observations-508_v4.60_withRSV.csv"
df_csv = pl.scan_csv(CSV_DATA).filter((pl.col("Observation Title").is_not_null()) & (pl.col("PHIN VS (Code)").is_not_null()))

# 2. Combine and de-duplicate Observation Title and SNOMED (Code) columns into meaningful words that will be used to send to LLM
obs_and_snomed = df_csv.select("Observation Title", "SNOMED (Code)", "Observation Code").collect()

disease_dict = {}
for index, obs in enumerate(obs_and_snomed.rows(named=True)):
    # clean the data
    obs["SNOMED (Code)"] = re.sub(r"\d+", "", obs["SNOMED (Code)"]) # remove numbers
    obs["SNOMED (Code)"] = (re.sub(r"(\s{2,}|\n|n/a)", " ", obs["SNOMED (Code)"])).strip() # replace new lines, multple spaces, n/a with a single space and then remove leading/trailing spaces
    disease = f"[{obs["Observation Title"]} in the context of {obs["SNOMED (Code)"]}]" if obs["SNOMED (Code)"] != "" else obs["Observation Title"] # print(text)
    
    # 3. Use the newly derived string as an input to derive likely medications and observations / disorders for each row with sample prompts below 
    attributes = ["medications", "observations / symptoms", "disorders"]
    disease_dict[disease] = []
    for a in attributes:
        
        prompt = f'''
            You are a world-renowned medical expert specializing in diagnosing and treating diseases. 
            Your task is to generate concise, JSON-formatted data related to a single attribute for a specific disease or condition.

            For each of the following attributes — {", ".join(attributes)} — provide only those that are highly specific to the disease or condition in question. 
            Exclude any generic, common conditions or medications that are not directly related to the disease.

            Instructions:
            1. Provide data only for the attribute: "{a}".
            2. Include only highly specific and evidence-based items directly associated with the disease. Exclude any generic, vague, or irrelevant items.
            3. If the attribute does not apply or has no specific data, respond with "N/A".
            4. Return the result strictly in valid JSON format.
            5. Do not include any explanations, sentences, or extra text. Respond only with valid DynamoDB-compatible JSON.


            Examples:
            - If the attribute is medications and specific items are "Aspirin" and "Ibuprofen":
            {{"medications": ["Aspirin", "Ibuprofen"]}}
            - If the attribute is disorders and there is no specific data:
            {{"disorders": "N/A"}}

            Given the disease: "{disease}", provide the relevant data for the attribute: "{a}".
        '''
        
        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 600,
            "temperature": 0.5,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        }

        # execute the request 
        request = json.dumps(native_request)
        try:
            response = client.invoke_model(modelId=model_id, body=request)
        except (ClientError, Exception) as e:
            print(f"Error: Unable to invoke '{model_id}. Reason: {e}'")
            exit(1)
        # extract text from the request
        model_response = json.loads(response["body"].read())
        response_text = model_response["content"][0]["text"]

        response_text = re.sub(r"\n", "", response_text)
        print(obs["Observation Code"], response_text)
        disease_dict[disease].append(json.loads(response_text))    


    # 4. store the results in a dynamoDB table with key = csdi_code and secondary key category
    # input into dynamodb 
    serializer = TypeSerializer()
    for disease, attributes in disease_dict.items():
        print(attributes)
        dynamo_item = {
            "csdi_code": {"S": str(obs["Observation Code"])},
            "disease_name": {"S": disease},
            "medications": serializer.serialize(attributes[0]),
            "observations / symptoms": serializer.serialize(attributes[1]),
            "disorders": serializer.serialize(attributes[2])
        }

        dynamodb.put_item(
            TableName=diseases_table,
            Item=dynamo_item
        )
