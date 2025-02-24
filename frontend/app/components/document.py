import streamlit as st
from services.api import APIClient

class DocumentViewer:
    def __init__(self):
        self.api_client = APIClient()

    def __call__(self):
        if st.session_state.current_document:
            # Get document status from backend
            doc_status = self.api_client.get_document_status(
                st.session_state.current_document
            )
            
            if doc_status:
                st.markdown("### Document Status")
                st.success("✅ Document loaded and ready")
                
                with st.expander("Document Details"):
                    st.write({
                        "Document ID": st.session_state.current_document,
                        "Pages": doc_status.get("total_pages", "Unknown"),
                        "Chunks": doc_status.get("total_chunks", "Unknown"),
                        "Processed": doc_status.get("processed_at", "Unknown")
                    })