# Project Overview

This project explores two main approaches for mapping patient conditions to Clinical Decision Support Immunization (CDSi) codes:

1. **LLM-Based Classification**
2. **SNOMED-to-CDSi Mapping**

## 1. LLM-Based Classification

We developed a prototype that processes an Electronic Health Record (EHR) text file containing patient information, including allergies, medications, conditions, care plans, etc. The process follows these steps:

- Extract only **current conditions** (i.e., conditions without an end date).
- Retrieve CDSi codes and their descriptions from an **S3 bucket**.
- Send both the patient’s conditions and the CDSi codes to a **Large Language Model (LLM)** with a specific prompt instructing it to:
  - **Match** conditions directly to CDSi descriptions **without inference**.
- The model returns:
  1. **CDSi codes**
  2. **Observation titles** corresponding to each code
  3. **References** from patient conditions

## 2. SNOMED-to-CDSi Mapping

Since **SNOMED codes** are more readily available than CDSi codes, we use a lookup table to map SNOMED codes to relevant CDSi codes. The solutions based on this method are:

### 2.1 Direct Matching

1. Extract all **SNOMED codes** from:
   - **Conditions section** of the patient document (CDA format)
   - **Surgeries section**
2. Query a **DynamoDB table** to find corresponding **CDSi codes** based on SNOMED codes.
3. Return the mapped **CDSi codes**.

### 2.2 Extracting SNOMED Codes from Unstructured Text

1. Extract **current conditions** (conditions without an end date) from the patient CDA document.
2. Use **AWS Medical Comprehend** to extract **SNOMED codes** from the unstructured text.
3. Query the **DynamoDB table** to retrieve **CDSi codes** that correspond to the extracted SNOMED codes.

## Conclusion

This project provides two effective methods for mapping patient conditions to CDSi codes:
- A **LLM-based approach** for direct classification.
- A **SNOMED-to-CDSi mapping approach**, leveraging structured medical terminology.
