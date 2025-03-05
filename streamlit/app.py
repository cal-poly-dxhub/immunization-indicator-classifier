import streamlit as st
from pages import condition_identifier_page, snomed_to_cdsi_page, condition_snomed_to_cdsi_page, medication_rxnorm_page

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Condition Identifier", "Direct SNOMED to CDSi Matching","Extract SNOMED from Condition and Match to CDSi","Extract RXNORM from Medications"])
    
    if page == "Condition Identifier":
        condition_identifier_page()
    elif page == "Direct SNOMED to CDSi Matching":
        snomed_to_cdsi_page()
    elif page == "Extract SNOMED from Condition and Match to CDSi":
        condition_snomed_to_cdsi_page()
    elif page == "Extract RXNORM from Medications":
         medication_rxnorm_page()

if __name__ == "__main__":
    main()
