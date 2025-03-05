import re
import xml.etree.ElementTree as ET
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
