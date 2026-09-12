import streamlit as st
from core.pipeline import run_full_poleazy_pipeline

def main():
    st.title("Poleazy Unified Dashboard")
    
    st.write("Welcome to the Poleazy Civic AI application.")

    # Input for PDF path (or you could adapt for file uploader)
    pdf_path = st.text_input("Enter Path to Municipal PDF Docket", "data/raw/20260910-039, Agenda Backup_ Draft Ordinance.PDF")
    
    # Toggle for using mock data during development/testing
    use_mock = st.checkbox("Use Mock Data (bypass LLM/API calls)", value=True)
    
    if st.button("Run Pipeline"):
        with st.spinner("Processing..."):
            try:
                # Developer 3 calls the unified runner here
                result = run_full_poleazy_pipeline(input_source=pdf_path, mock=use_mock)
                
                st.success("Pipeline executed successfully!")
                
                st.subheader("Docket Information")
                st.write(f"**ID:** {result.get('docket_id', result.get('docket', {}).get('docket_id'))}")
                st.write(f"**Title:** {result.get('title', result.get('docket', {}).get('title'))}")
                
                st.subheader("Legal Analysis")
                if "legal_diff" in result:
                    st.json(result["legal_diff"])
                    
                st.subheader("Citizen Action Materials")
                if "citizen_action" in result:
                    st.json(result["citizen_action"])
                    
            except Exception as e:
                st.error(f"Error running pipeline: {e}")

if __name__ == "__main__":
    main()
