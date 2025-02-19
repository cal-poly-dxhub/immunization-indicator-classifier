import streamlit as st
import requests
import json

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

# def snomed_to_cdsi_page():
#     st.title("Direct SNOMED to CDSi Matching")

#     # Ensure session state variables exist
#     if "file_key_snomed" not in st.session_state:
#         st.session_state.file_key_snomed = ""
#     if "result_snomed" not in st.session_state:
#         st.session_state.result_snomed = None
#     if "submitted_snomed" not in st.session_state:
#         st.session_state.submitted_snomed = False

#     # Text input linked to session state (DO NOT modify this variable after)
#     file_key = st.text_input(
#         "Enter the S3 file key:",
#         key="file_key_snomed"  # This links it directly to session state
#     )

#     # Submit button logic
#     if st.button("Submit", key="submit_snomed"):
#         st.session_state.submitted_snomed = True
#         st.write(f"Processing file: {file_key}")
        
#         with st.spinner("Fetching SNOMED-CDSi mappings, please wait..."):
#             st.session_state.result_snomed = call_snomed_to_cdsi_api(file_key)  # Call API
#         st.rerun()

#     # Display the results
#     if st.session_state.result_snomed:
#         st.subheader("SNOMED to CDSi Mappings")
#         st.json(st.session_state.result_snomed)  # Display JSON response neatly

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


# Main Navigation
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Condition Identifier", "Direct SNOMED to CDSi Matching"])
    
    if page == "Condition Identifier":
        condition_identifier_page()
    elif page == "Direct SNOMED to CDSi Matching":
        snomed_to_cdsi_page()

if __name__ == "__main__":
    main()
