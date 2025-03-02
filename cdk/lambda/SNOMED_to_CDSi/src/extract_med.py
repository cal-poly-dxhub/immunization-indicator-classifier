from bs4 import BeautifulSoup
import re

import xml.etree.ElementTree as ET
import re
from typing import List, Dict

def strip_namespaces(element):
    """Remove namespace prefixes from tags."""
    for elem in element.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]

def extract_table_meds_or_problems(section_element: ET.Element) -> List[str]:
    """Extract meds or problems from a <section> element containing a <table>."""
    items = []
    table = section_element.find(".//table")

    if table is not None:
        for tr in table.findall(".//tr"):
            cells = tr.findall("td")
            if len(cells) >= 4:
                stop_date = (cells[1].text or "").strip()
                if not stop_date:
                    description = (cells[2].text or "").strip()
                    description = re.sub(r'\s*\(.*?\)', '', description)  # Strip (notes) if needed
                    items.append(description)

    return items

def get_patient_meds(xml_content: str) -> Dict[str, List[str]]:
    root = ET.fromstring(xml_content)
    strip_namespaces(root)

    med_info = {
        "medications": [],
        "problems": [],
    }

    # Walk through every section to find medications & problems
    for section in root.iter("section"):
        # Check if there's a <title> to identify the section
        title_element = section.find("title")
        title = (title_element.text or "").strip().lower() if title_element is not None else ""

        if "medication" in title:
            med_info["medications"] = extract_table_meds_or_problems(section)
        elif "problem" in title:
            med_info["problems"] = extract_table_meds_or_problems(section)

    return med_info

# def get_direct_text(element):
#   return ''.join([t for t in element.contents if isinstance(t, str)]).strip()

# def xml_to_dict(element):
#   data = {}
#   if element.attrs:
#     data.update(element.attrs)
#   text = get_direct_text(element)
#   if text:
#     data["content"] = text
#   children = [child for child in element.children if child.name]
#   if children:
#     for child in children:
#       child_content = xml_to_dict(child)
#       if child.name in data:
#         if not isinstance(data[child.name], list):
#           data[child.name] = [data[child.name]]
#         data[child.name].append(child_content)
#       else:
#         data[child.name] = child_content
#   return data

# def extract_meds(data: dict) -> list:
#   table = data.get("text", {}).get("table", {})
#   if table == {}:
#     return []

#   medications: list[str] = []
#   rows = table.get("tbody", {}).get("tr", [])
#   if isinstance(rows, dict):
#     rows = [rows]

#   for row in rows:
#     cells = row.get("td", [])
#     if isinstance(cells, dict):
#       cells = [cells]
#     if len(cells) >= 4:
#       stop_date = cells[1].get("content", "")
#       if not stop_date.strip():
#         description = cells[2].get("content", "")
#         medications.append(description)
#   return medications

# def extract_problems(data: dict) -> list:
#   table: dict[str, any] = data.get("text", {}).get("table", {})
#   if table == {}:
#     return []
  
#   problems: list[str] = []
#   rows: any = table.get("tbody", {}).get("tr", [])
#   if isinstance(rows, dict):
#     rows = [rows]
    
#   for row in rows:
#     cells: any = row.get("td", [])
#     if isinstance(cells, dict):
#       cells = [cells]
      
#     if len(cells) >= 4:
#       stop_date: str = cells[1].get("content", "")
#       if not stop_date.strip():
#         description: str = cells[2].get("content", "")
#         description = re.sub(r'\s*\(.*?\)', '', description)
#         problems.append(description)
        
#   return problems

# def get_patient_meds(xml_content: str):
#     soup = BeautifulSoup(xml_content, 'xml')
#     data = xml_to_dict(soup.ClinicalDocument)
  
#     components = data.get("component", {}).get("structuredBody", {}).get("component", [])
#     med_info = {
#         "medications": [],
#         "problems": [],
#         "conditions": []
#     }

#     if not components:
#         return med_info

#     meds = []
#     problems = []

#     for component in components:
#         if isinstance(component, dict) and component.get("content", "") and 'medications' in component['content'].lower():
#             meds = extract_meds(component.get("section", {}))
        
#         if isinstance(component, dict) and component.get("content", "") and 'problems' in component['content'].lower():
#             problems = extract_problems(component.get("section", {}))

#     med_info['medications'] = meds
#     med_info['problems'] = problems
#     return med_info

# def get_patient_meds(filename: str):
#   with open(filename, 'r') as f:
#     soup = BeautifulSoup(f.read(), 'xml')
#     data = xml_to_dict(soup.ClinicalDocument)
  
#   components = data.get("component",{}).get("structuredBody", {}).get("component", [])
#   med_info = {"medications" : [],
#               "problems" : [],
#               "conditions" : []}
#   if len(components) == 0:
#     return med_info
  
#   meds = []
#   problems = []
#   for component in components:
#     if isinstance(component, dict) and (component.get("content", "") != "") and 'medications' in component['content'].lower():
#       meds = extract_meds(component.get("section", {}))
    
#     if isinstance(component, dict) and (component.get("content", "") != "") and 'problems' in component['content'].lower():
#       problems = extract_problems(component.get("section", {}))
    
#   med_info['medications'] = meds
#   med_info['problems'] = problems
#   return med_info