import streamlit as st
from services.api import APIClient
from utils.file import validate_file

class FileUploader:
    def __init__(self):
        self.api_client = APIClient()

    def __call__(self):
        # Debug: Add a visible element to confirm the component is running
        st.write("Upload Component Loaded")  # Add this line temporarily
        
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
            # Display file info in a nice format
            st.success(f"📄 Uploaded: {uploaded_file.name}")
            file_size_mb = uploaded_file.size/1024/1024
            st.text(f"Size: {file_size_mb:.1f}MB")

            # Validate file
            if validate_file(uploaded_file):
                # Show process button
                if st.button("📝 Process Document", type="primary"):
                    try:
                        with st.spinner("Processing your document..."):
                            # TODO: Replace with actual API call once backend is ready
                            import time
                            time.sleep(2)  # Simulate processing time
                            st.session_state.current_document = "dummy_doc_id"
                            st.success("✅ Document processed successfully!")
                            st.balloons()  # Add a fun touch
                    except Exception as e:
                        st.error(f"❌ Error processing document: {str(e)}")
            else:
                st.error("❌ Please upload a valid PDF, DOCX, or TXT file.")