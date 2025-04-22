
# Immunization Indicatior Classifier Solution

# Collaboration
Thanks for your interest in our solution.  Having specific examples of replication and cloning allows us to continue to grow and scale our work. If you clone or download this repository, kindly shoot us a quick email to let us know you are interested in this work!

[wwps-cic@amazon.com] 

# Disclaimers

**Customers are responsible for making their own independent assessment of the information in this document.**

**This document:**

(a) is for informational purposes only, 

(b) represents current AWS product offerings and practices, which are subject to change without notice, and 

(c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers. 

(d) is not to be considered a recommendation or viewpoint of AWS

**Additionally, all prototype code and associated assets should be considered:**

(a) as-is and without warranties

(b) not suitable for production environments

(d) to include shortcuts in order to support rapid prototyping such as, but not limitted to, relaxed authentication and authorization and a lack of strict adherence to security best practices

**All work produced is open source. More information can be found in the GitHub repo.**

## Authors
- Belal Elshenety - belshene@calpoly.edu

## Table of Contents
- [Project Overview](#project-overview)
- [Deployment](#deployment)
- [Frontend Demo](#frontend-demo)
- [Experiments & Abandoned Approaches](#experiments--abandoned-approaches)

## Project Overview

This project explores two main approaches for mapping patient conditions to Clinical Decision Support information (CDSi) codes:

1. **LLM-Based Classification**
2. **SNOMED-to-CDSi Mapping**

### 1. LLM-Based Classification

We developed a prototype that processes an Electronic Health Record (EHR) text file containing patient information, including allergies, medications, conditions, care plans, etc. The process follows these steps:

- Extract only **current conditions** (i.e., conditions without an end date).
- Retrieve CDSi codes and their descriptions from an **S3 bucket**.
- Send both the patient’s conditions and the CDSi codes to a **Large Language Model (LLM)** with a specific prompt instructing it to:
  - **Match** conditions directly to CDSi descriptions **without inference**.
- The model returns:
  1. **CDSi codes**
  2. **Observation titles** corresponding to each code
  3. **References** from patient conditions

![image](https://github.com/user-attachments/assets/8933a7c0-c417-47b2-b9a7-859f94baf7ef)

### 2. SNOMED-to-CDSi Mapping

Since **SNOMED codes** are more readily available than CDSi codes, we use a lookup table to map SNOMED codes to relevant CDSi codes. The solutions based on this method are:

#### 2.1 Direct Matching

1. Extract all **SNOMED codes** from:
   - **Conditions section** of the patient document (CDA format)
   - **Surgeries section**
2. Query a **DynamoDB table** to find corresponding **CDSi codes** based on SNOMED codes.
3. Return the mapped **CDSi codes**.
   
![image](https://github.com/user-attachments/assets/0e0158bb-6d8c-4f62-af4f-efecbbc48a3d)


#### 2.2 Extracting SNOMED Codes from Unstructured Text

1. Extract **current conditions** (conditions without an end date) from the patient CDA document.
2. Use **AWS Medical Comprehend** to extract **SNOMED codes** from the unstructured text.
3. Query the **DynamoDB table** to retrieve **CDSi codes** that correspond to the extracted SNOMED codes.

![image](https://github.com/user-attachments/assets/df8f453b-b46a-40bb-ae6f-3df484a45417)


### Conclusion

This project provides two effective methods for mapping patient conditions to CDSi codes:
- A **LLM-based approach** for direct classification.
- A **SNOMED-to-CDSi mapping approach**, leveraging structured medical terminology.

---
## Deployment
> See the [Deployment Guide](./docs/Deployment.md) for detailed deployment steps.

## Frontend Demo
> After deployment, see the [Streamlit Demo Guide](./docs/StreamlitDemo.md) for detailed steps for running the frontend demo.

## Experiments & Abandoned Approaches
> Check out the [Experiments Guide](./docs/Experiments.md) to learn about exploratory ideas and approaches we tested but ultimately did not include in the final solution.


## Support
For any queries or issues, please contact:
- Darren Kraker, Sr Solutions Architect - dkraker@amazon.com 
- Belal Elshenety, Software Developer Intern - belshene@calpoly.edu
  
