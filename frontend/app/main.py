import streamlit as st
from components.chat import ChatInterface
from components.document import DocumentViewer
from components.upload import FileUploader

# Page config
st.set_page_config(
    page_title="DocuQuery",
    page_icon="📚",
    layout="wide"
)

def main():
    # Add a title
    st.title("📚 DocuQuery")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_document" not in st.session_state:
        st.session_state.current_document = None

    # Layout
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Document upload and preview
        uploader = FileUploader()
        uploader()
        
        if st.session_state.current_document:
            DocumentViewer()
    
    with col2:
        if st.session_state.current_document:
            st.markdown("### Ask Questions")
            ChatInterface()

if __name__ == "__main__":
    main()