import streamlit as st
from services.api import APIClient
from utils.file import validate_file


class FileUploader:
    def __init__(self):
        self.api_client = APIClient()

    def __call__(self):
        # Add clear instructions with visible borders
        st.markdown("""
        ### 📄 Upload your document:
        - Click the box below or drag & drop a file
        - Supported: PDF, DOCX, TXT
        - Max size: 50MB
        """)

        # Create file uploader widget with a more visible prompt
        uploaded_file = st.file_uploader(
            "Click here or drag a file",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=False,
            help="Click anywhere in this box to choose a file"
        )

        # Handle uploaded file
        if uploaded_file is not None:
            st.success(f"📄 Uploaded: {uploaded_file.name}")

            if validate_file(uploaded_file):
                if st.button("📝 Process Document", type="primary"):
                    try:
                        with st.spinner("Processing document..."):
                            response = self.api_client.upload_document(uploaded_file)

                            if response.get("status") == "success":
                                doc_id = response.get("doc_id")
                                st.session_state.current_document = doc_id

                                # Verify document in Chroma
                                doc_status = self.api_client.get_document_status(doc_id)
                                if doc_status.get("status") == "success":
                                    st.success(f"""
                                    ✅ Document processed successfully!
                                    - Chunks created: {doc_status.get('chunk_count')}
                                    - Ready for questions
                                    """)

                                    # Force refresh to show chat interface
                                    st.rerun()
                                else:
                                    st.warning("Document processed but not found in database")
                            else:
                                st.error(f"❌ Processing failed: {response.get('message', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
