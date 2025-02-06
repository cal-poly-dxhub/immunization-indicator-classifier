from bs4 import BeautifulSoup
import json
import re

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
  table = data.get("text",{}).get("table",{})
  if table == {}:
    return []
  
  medications: list[str] = []
  rows = table.get("tbody", {}).get("tr", [])
  for row in rows:
    cells = row.get("td", [])
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
  rows: list[any] = table.get("tbody", {}).get("tr", [])
  for row in rows:
    cells: list[any] = row.get("td", [])
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
              "problems" : [] }
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
  return med_info

with open("out.json" , "w") as f:
  f.write(json.dumps(get_patient_meds("assets/file4.xml")))


#2021-08-01T06:37:45Z