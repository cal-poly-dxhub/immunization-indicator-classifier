import polars as pl
import datetime as dt
import re
import boto3
import json
from botocore.exceptions import ClientError


# create a Bedrock Runtime client in us-west-2
client = boto3.client("bedrock-runtime", region_name="us-west-2")
model_id = "anthropic.claude-3-haiku-20240307-v1:0"


# 1.  Find xlsx file with RSV CDSi codes and export a cvs with all columns
CSV_DATA = "./files/CDSi ScheduleSupportingData- Coded Observations-508_v4.60_withRSV.csv"
df_csv = pl.scan_csv(CSV_DATA).filter((pl.col("Observation Title").is_not_null()) & (pl.col("PHIN VS (Code)").is_not_null()))


# 2. Combine and de-duplicate Observation Title and SNOMED (Code) columns into meaningful words that will be used to send to LLM
obs_and_snomed = df_csv.select("Observation Title", "SNOMED (Code)").collect()
for index, obs in enumerate(obs_and_snomed.rows(named=True)):
    # basic filter: remove a new line and a word from SNOMED Code if it is already in the Observation Title
    obs["SNOMED (Code)"] = obs["SNOMED (Code)"].replace(obs["Observation Title"], "").replace("\n", "")
    # obs["SNOMED (Code)"]re.sub("^\d+\s|\s\d+\s|\s\d+$", " ", obs["SNOMED (Code)"])
    text = f"{obs["Observation Title"]}: {obs["SNOMED (Code)"]}"
    # print(obs["SNOMED (Code)"])
    print(text)

    diseases = ["chronic liver disease", "type 2 diabetes", "COVID-19", "Malaria", "Chickenpox", "Dengue Fever", "Measles"]
    attributes = ["symptoms", "medications"] 


    # 3. Use the newly derived string as an input to derive likely medications and observations 
    # / disorders for each row with sample prompts below
    # store the results in a dynamoDB table with key = csdi_code and secondary key category
    # diseses and symptoms 
    for d in diseases:
        for a in attributes:

            system_prompt = '''
                            You are an expert doctor in medicine. You know what medicatations are best for what diseases. 
                            You are tasked to help students understand medications and symptoms associated 
                            with different medical condiitions.
                            '''
            
            assistant_prompt = f'''
                            Please only list {a} that are directly relavant and please exclude common {a}.
                            Only list the {a} in likey to unlikey order and don't list anything else.

                            Please respond in this format:
                            {{
                                {a}: [{a} 1, {a} 2, {a} 3]
                            }}             
                            '''

            user_prompt = f'''What are the actual {a} that someone with {d} may be taking/having.'''
            
            native_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,
                "temperature": 0.5,
                "messages": [
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": system_prompt}]
                    },
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": assistant_prompt}]
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_prompt}]
                    }
                ]
            }

        # translate request to json
        request = json.dumps(native_request)
        
        try:
            # invoke the model with the request
            response = client.invoke_model(model_id=model_id, body=request)
        except (ClientError, Exception) as e:
            print(f"Error: Unable to invoke '{model_id}. Reason: {e}'")
            exit(1)

    model_response = json.loads(response["body"].read(response))
    response_text = model_response["content"][0]["text"]

    print(model_response)
    print(response_text)


    if index >= 2:
        break




