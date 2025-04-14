import streamlit as st
from api_endpoints import call_condition_api, call_snomed_to_cdsi_api, call_condition_snomed_to_cdsi_api

def condition_identifier_page():
    st.title("LLM-Based Classification")
    
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
    st.title("SNOMED-to-CDSi Mapping: Direct Mapping")

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

def condition_snomed_to_cdsi_page():
    st.title("SNOMED-to-CDSi Mapping:Extracting SNOMED Codes from Unstructured Text via Medical Comprehend")

    if "file_key_condition_snomed" not in st.session_state:
        st.session_state.file_key_condition_snomed = ""
    if "result_condition_snomed" not in st.session_state:
        st.session_state.result_condition_snomed = None
    if "submitted_condition_snomed" not in st.session_state:
        st.session_state.submitted_condition_snomed = False

    file_key = st.text_input("Enter the S3 file key:", key="file_key_condition_snomed")

    if st.button("Submit", key="submit_condition_snomed"):
        st.session_state.submitted_condition_snomed = True
        st.write(f"Processing file: `{file_key}`")

        with st.spinner("Contacting Medical Comprehend for condition and SNOMED-CDSi mapping..."):
            result = call_condition_snomed_to_cdsi_api(file_key)
            if "error" in result:
                st.error(result["error"])
                st.session_state.result_condition_snomed = None
            else:
                st.session_state.result_condition_snomed = result
        st.rerun()

    if st.session_state.result_condition_snomed:
        st.subheader("CDSI Mappings from API")

        cdsi_results = st.session_state.result_condition_snomed.get("cdsi_results", {})

        if not cdsi_results:
            st.warning("No CDSI mappings found.")
        else:
            for cdsi_code, data in cdsi_results.items():
                st.markdown(f"### 🔹 CDSi Code: `{cdsi_code}`")
                st.markdown(f"**Observation Title:** {data['observation_title']}")
                st.markdown("#### 🔗 Related SNOMED Codes:")
                for snomed_ref in data["snomed_references"]:
                    st.markdown(f"**SNOMED Code:** `{snomed_ref['snomed_code']}` - {snomed_ref['snomed_description']}")
                    st.markdown(f"- Confidence: `{snomed_ref['confidence']:.4f}`")
                    st.markdown(f"- Text Reference: `{snomed_ref['text_reference']}`")
                st.markdown("---")
