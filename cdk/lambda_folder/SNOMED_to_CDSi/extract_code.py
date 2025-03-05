#---- code for extracting SNOMED Code and Probability along with CDSi
#---- code for extracting RXNORM

import boto3
from typing import List
from extract_med import get_patient_meds
from src.snomed_to_cdsi_logic import snomed_set_with_cdsi_codes

# Initialize ComprehendMedical client
client = boto3.client('comprehendmedical')

def extract_snomedct(conditions: List[str]):
    snomed_set = set()
    # Iterate through the list of conditions
    for condition in conditions:
        response = client.infer_snomedct(Text=condition)
        
        # Iterate through the results and print the detected entities and their SNOMED-CT codes
        for entity in response['Entities']:
            print(f"Entity Text: {entity['Text']}")
            print(f"Category: {entity['Category']}")
            print(f"Type: {entity['Type']}")
            print(f"SNOMEDCT Concepts:")
            for concept in entity.get('SNOMEDCTConcepts', []):
                snomed_code = int(concept['Code'])
                print(f"  Description: {concept['Description']}")
                print(f"  Code: {concept['Code']}")
                print(f"  Confidence: {concept['Score']}")
                snomed_set.add(snomed_code)
            print("="*50)
    cdsi_dict = snomed_set_with_cdsi_codes(snomed_set)

    # Print the CDSI codes and related information
    for cdsi_code, data in cdsi_dict.items():
        print(f"CDSI Code: {cdsi_code}")
        print(f"Observation Title: {data['observation_title']}")
        for snomed_ref in data['snomed_references']:
            print(f"  SNOMED Code: {snomed_ref['snomed_code']}")
            print(f"  SNOMED Description: {snomed_ref['snomed_description']}")
        print("="*50)

def extract_rxnorm(medications: List[str]):
    # Iterate through the list of medications
    for medication in medications:
        response = client.infer_rx_norm(Text=medication)
        
        # Iterate through the results and print the detected entities and their RxNorm codes
        for entity in response['Entities']:
            print(f"Entity Text: {entity['Text']}")
            print(f"Category: {entity['Category']}")
            print(f"Type: {entity['Type']}")
            print(f"RxNorm Concepts:")
            for concept in entity.get('RxNormConcepts', []):
                print(f"  Description: {concept['Description']}")
                print(f"  Code: {concept['Code']}")
                print(f"  Confidence: {concept['Score']}")
            print("="*50)




patient_records = get_patient_meds("patient.xml")
patient_problems = patient_records['problems']
patient_medications = patient_records['medications']

extract_rxnorm(patient_medications)

