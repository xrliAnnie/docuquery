import streamlit as st
import requests
from typing import Optional

st.title("DocuQuery")

def upload_document():
    """Handle document upload and send to backend for processing"""
    uploaded_file = st.file_uploader("Choose a document", type=["pdf", "docx"])
    if uploaded_file:
        pass

def chat_interface():
    """Display chat interface for querying documents"""
    question = st.text_input("Ask a question about your document")
    if question:
        pass

def main():
    upload_document()
    chat_interface()

if __name__ == "__main__":
    main()