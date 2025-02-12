import streamlit as st
import requests
import json

def call_api(file_key):
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

def condition_identifier_page():
    st.title("Medical Condition Identifier")
    
    if "file_key" not in st.session_state:
        st.session_state.file_key = ""
    if "result" not in st.session_state:
        st.session_state.result = ""
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        file_key = st.text_input("Enter the S3 file key:", value=st.session_state.file_key, key="file_key_input")
    
    if st.button("Submit"):
        st.session_state.file_key = file_key
        st.session_state.submitted = True
        st.write(f"Processing file: {file_key}")
        with st.spinner("Analyzing conditions, please wait..."):
            st.session_state.result = call_api(file_key)
        st.rerun()
    
    if st.session_state.submitted:
        with col2:
            if st.button("Reset"):
                for key in ["file_key", "result", "submitted"]:
                    st.session_state[key] = ""
                st.rerun()
    
    if st.session_state.result:
        st.subheader("Generated Output")
        st.markdown(f"""<div style="word-wrap: break-word; white-space: pre-wrap;">{st.session_state.result}</div>""", unsafe_allow_html=True)

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Condition Identifier", "Another Feature"])
    
    if page == "Condition Identifier":
        condition_identifier_page()
    elif page == "Another Feature":
        st.title("Another Feature Coming Soon")

if __name__ == "__main__":
    main()
