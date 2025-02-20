from bs4 import BeautifulSoup
import json
import re

import boto3
from typing import List


def get_direct_text(element):
  return ''.join([t for t in element.contents if isinstance(t, str)]).strip()

def xml_to_dict(element):
  data = {}
  if element.attrs:
    data.update(element.attrs)
  text = get_direct_text(element)
  if text:
    data["content"] = text
  children = [child for child in element.children if child.name]
  if children:
    for child in children:
      child_content = xml_to_dict(child)
      if child.name in data:
        if not isinstance(data[child.name], list):
          data[child.name] = [data[child.name]]
        data[child.name].append(child_content)
      else:
        data[child.name] = child_content
  return data

def extract_meds(data: dict) -> list:
  table = data.get("text", {}).get("table", {})
  if table == {}:
    return []

  medications: list[str] = []
  rows = table.get("tbody", {}).get("tr", [])
  if isinstance(rows, dict):
    rows = [rows]

  for row in rows:
    cells = row.get("td", [])
    if isinstance(cells, dict):
      cells = [cells]
    if len(cells) >= 4:
      stop_date = cells[1].get("content", "")
      if not stop_date.strip():
        description = cells[2].get("content", "")
        medications.append(description)
  return medications

def extract_problems(data: dict) -> list:
  table: dict[str, any] = data.get("text", {}).get("table", {})
  if table == {}:
    return []
  
  problems: list[str] = []
  rows: any = table.get("tbody", {}).get("tr", [])
  if isinstance(rows, dict):
    rows = [rows]
    
  for row in rows:
    cells: any = row.get("td", [])
    if isinstance(cells, dict):
      cells = [cells]
      
    if len(cells) >= 4:
      stop_date: str = cells[1].get("content", "")
      if not stop_date.strip():
        description: str = cells[2].get("content", "")
        description = re.sub(r'\s*\(.*?\)', '', description)
        problems.append(description)
        
  return problems

def get_patient_meds(filename: str):
  with open(filename, 'r') as f:
    soup = BeautifulSoup(f.read(), 'xml')
    data = xml_to_dict(soup.ClinicalDocument)
  
  components = data.get("component",{}).get("structuredBody", {}).get("component", [])
  med_info = {"medications" : [],
              "problems" : [],
              "conditions" : []}
  if len(components) == 0:
    return med_info
  
  meds = []
  problems = []
  for component in components:
    if isinstance(component, dict) and (component.get("content", "") != "") and 'medications' in component['content'].lower():
      meds = extract_meds(component.get("section", {}))
    
    if isinstance(component, dict) and (component.get("content", "") != "") and 'problems' in component['content'].lower():
      problems = extract_problems(component.get("section", {}))
    
  med_info['medications'] = meds
  med_info['problems'] = problems
  return med_info['problems'] #getting the list of conditions



#---- code for extracting SNOMED Code and Probability 

# Initialize ComprehendMedical client
client = boto3.client('comprehendmedical')

def infer_snomedct(conditions: List[str]):
    # Iterate through the list of conditions
    for condition in conditions:
        print(f"Processing condition: {condition}")
        response = client.infer_snomedct(Text=condition)
        
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

infer_snomedct(get_patient_meds("patient.xml"))
