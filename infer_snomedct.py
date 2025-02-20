import boto3
from typing import Set, Dict, List

# Initialize ComprehendMedical client
client = boto3.client('comprehendmedical')

def infer_snomedct(text):
    response = client.infer_snomedct(Text=text)
    
    # Iterate through the results and print the detected entities and their SNOMED-CT codes
    for entity in response['Entities']:
        print(f"Entity Text: {entity['Text']}")
        print(f"Category: {entity['Category']}")
        print(f"Type: {entity['Type']}")
        print(f"SNOMEDCT Concepts:")
        for concept in entity.get('SNOMEDCTConcepts', []):
            print(f"  Description: {concept['Description']}")
            print(f"  Code: {concept['Code']}")
            print(f"  Confidence: {concept['Score']}")
        print("="*50)


# Example text input (medical conditions or symptoms)
text_input = "Patient is suffering from hypertension and has a history of stroke."
infer_snomedct(text_input)