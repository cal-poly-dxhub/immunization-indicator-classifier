import streamlit as st
import requests
import boto3
from extract_med import get_patient_meds  # Parses XML content
from snomed_to_cdsi_logic import snomed_set_with_cdsi_codes  # Maps SNOMED to CDSI

def call_condition_api(file_key):
    url = "https://dsqmp3jp3b.execute-api.us-west-2.amazonaws.com/prod/level-1-iz-classification"
    headers = {"Content-Type": "application/json"}
    data = {"file_key": file_key}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response_json = response.json()
        try:
            return response_json["bedrock_output"]["content"][0]["text"]
        except KeyError:
            return "Error: Unexpected response format"
    else:
        return "Error: Failed to get response from API"
    
def call_snomed_to_cdsi_api(file_key):
    url = "https://jlnk2zoyf1.execute-api.us-west-2.amazonaws.com/prod/hl7-to-snomed-to-cdsi"
    headers = {"Content-Type": "application/json"}
    data = {"s3_key": file_key}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()  # Return JSON response
    else:
        return {"error": "Failed to get response from API"}
    

def call_condition_snomed_to_cdsi_api(file_key):
    url = "https://jlnk2zoyf1.execute-api.us-west-2.amazonaws.com/prod/condition-snomed-to-cdsi"
    headers = {"Content-Type": "application/json"}
    data = {"s3_key": file_key}
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()  # Return JSON response
    else:
        return {"error": "Failed to get response from API"}

def condition_identifier_page():
    st.title("Medical Condition Identifier")
    
    if "file_key" not in st.session_state:
        st.session_state.file_key = ""
    if "result" not in st.session_state:
        st.session_state.result = ""
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    
    file_key = st.text_input("Enter the S3 file key:", value=st.session_state.file_key, key="file_key_input")
    
    if st.button("Submit"):
        st.session_state.file_key = file_key
        st.session_state.submitted = True
        st.write(f"Processing file: {file_key}")
        with st.spinner("Analyzing conditions, please wait..."):
            st.session_state.result = call_condition_api(file_key)
        st.rerun()
    
    if st.session_state.result:
        st.subheader("Generated Output")
        st.markdown(f"""<div style="word-wrap: break-word; white-space: pre-wrap;">{st.session_state.result}</div>""", unsafe_allow_html=True)

def snomed_to_cdsi_page():
    st.title("Direct SNOMED to CDSi Matching")

    # Ensure session state variables exist
    if "file_key_snomed" not in st.session_state:
        st.session_state.file_key_snomed = ""
    if "result_snomed" not in st.session_state:
        st.session_state.result_snomed = None
    if "submitted_snomed" not in st.session_state:
        st.session_state.submitted_snomed = False

    # Text input linked to session state
    file_key = st.text_input(
        "Enter the S3 file key:",
        key="file_key_snomed"
    )

    # Submit button logic
    if st.button("Submit", key="submit_snomed"):
        st.session_state.submitted_snomed = True
        st.write(f"Processing file: {file_key}")
        
        with st.spinner("Fetching SNOMED-CDSi mappings, please wait..."):
            st.session_state.result_snomed = call_snomed_to_cdsi_api(file_key)  # Call API
        st.rerun()

    # Display the results in a human-readable format
    if st.session_state.result_snomed:
        st.subheader("SNOMED to CDSi Mappings")

        for cdsi_code, data in st.session_state.result_snomed.items():
            st.markdown(f"#### 🏥 CDSi Code **{cdsi_code}**: {data['observation_title']}")
            st.write("**SNOMED References:**")
            
            for ref in data["snomed_references"]:
                st.markdown(f"- **{ref['snomed_code']}**: {ref['snomed_description']}")

            st.markdown("---")  # Separator for clarity


# Initialize AWS clients
s3_client = boto3.client("s3")
comprehend_client = boto3.client("comprehendmedical")

# Function to get XML content from S3
def get_file_from_s3(bucket_name, file_key):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response["Body"].read().decode("utf-8")  # Convert bytes to string
        return file_content
    except Exception as e:
        st.error(f"Error retrieving file from S3: {e}")
        return None

# Initialize AWS clients
s3_client = boto3.client("s3")
comprehend_client = boto3.client("comprehendmedical")

# Function to get XML content from S3
def get_file_from_s3(bucket_name, file_key):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response["Body"].read().decode("utf-8")  # Convert bytes to string
        return file_content
    except Exception as e:
        st.error(f"Error retrieving file from S3: {e}")
        return None

def condition_snomed_to_cdsi_page():
    st.title("Extract SNOMED from Condition and Match to CDSi")

    bucket_name = "hl7-xml-to-snomed-code"  # Replace with actual S3 bucket name
    file_key = st.text_input("Enter the S3 file key:", key="file_key_condition_snomed")

    if st.button("Submit", key="submit_condition_snomed"):
        st.session_state.submitted_condition_snomed = True
        st.write(f"Fetching file from S3: `{file_key}`")

        with st.spinner("Downloading XML file..."):
            xml_content = get_file_from_s3(bucket_name, file_key)  # Retrieve XML file from S3
        
        if not xml_content:
            st.error("Failed to retrieve XML file from S3. Please check the file key and try again.")
            return

        with st.spinner("Extracting conditions from XML..."):
            patient_records = get_patient_meds(xml_content)  # Extract conditions from XML content
            conditions = patient_records.get("problems", [])

        if not conditions:
            st.error("No medical conditions found in the XML file.")
            return

        snomed_set = set()
        st.markdown("# 🏥 **Detecting SNOMED-CT Mappings**")

        for condition in conditions:
            response = comprehend_client.infer_snomedct(Text=condition)  # AWS Comprehend Medical API call
            
            valid_snomed_concepts = []

            for entity in response.get("Entities", []):
                if entity.get("Category") != "MEDICAL_CONDITION":  
                    continue  # ✅ Skip non-medical conditions immediately

                # Extract SNOMED-CT mappings
                for concept in entity.get("SNOMEDCTConcepts", []):
                    snomed_code = int(concept["Code"])
                    snomed_set.add(snomed_code)
                    valid_snomed_concepts.append({
                        "description": concept["Description"],
                        "code": concept["Code"],
                        "score": concept["Score"]
                    })

            # 🚨 Skip displaying conditions that have no valid SNOMED concepts
            if not valid_snomed_concepts:
                continue  

            # ✅ Display condition with valid SNOMED-CT mappings
            st.markdown(f"### 🏥 Condition: **{condition}**")
            st.markdown("#### 🔗 SNOMED-CT Concepts:")
            for concept in valid_snomed_concepts:
                st.markdown(f"- **Description:** {concept['description']}")
                st.markdown(f"- **Code:** `{concept['code']}`")
                st.markdown(f"- **Confidence Score:** `{concept['score']:.5f}`")
                st.markdown("---")  # Separator between SNOMED concepts
            
            st.markdown("----")  # Separator between conditions

        if not snomed_set:
            st.error("No SNOMED-CT codes detected.")
            return

        with st.spinner("Mapping SNOMED codes to CDSI..."):
            cdsi_dict = snomed_set_with_cdsi_codes(snomed_set)

        st.subheader("📌 **CDSI Code Mappings**")
        for cdsi_code, data in cdsi_dict.items():
            st.markdown(f"### 🔹 CDSI Code: `{cdsi_code}`")
            st.markdown(f"**Observation Title:** {data['observation_title']}")
            st.markdown("#### 🔗 Related SNOMED Codes:")
            for snomed_ref in data["snomed_references"]:
                st.markdown(f"- **SNOMED Code:** `{snomed_ref['snomed_code']}` - {snomed_ref['snomed_description']}")
            st.markdown("----")  # Separator for clarity

# Main Navigation
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Condition Identifier", "Direct SNOMED to CDSi Matching","Extract SNOMED from Condition and Match to CDSi"])
    
    if page == "Condition Identifier":
        condition_identifier_page()
    elif page == "Direct SNOMED to CDSi Matching":
        snomed_to_cdsi_page()
    elif page == "Extract SNOMED from Condition and Match to CDSi":
        condition_snomed_to_cdsi_page()

if __name__ == "__main__":
    main()
