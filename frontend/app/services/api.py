import requests
import streamlit as st
from typing import Dict, Any, Optional

class APIClient:
    def __init__(self, base_url="http://localhost:8001/api/v1"):
        self.base_url = base_url

    def upload_document(self, file) -> Dict[str, Any]:
        """Upload and process a document"""
        try:
            files = {"file": file}
            response = requests.post(
                f"{self.base_url}/ingest",
                files=files
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error uploading document: {str(e)}")
            return {"status": "error", "message": str(e)}

    def query_document(self, document_id: str, question: str) -> Dict[str, Any]:
        """Query a document with a question"""
        try:
            url = f"{self.base_url}/query"
            payload = {
                "text": question,
                "context_id": document_id
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error querying document: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_document_status(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document processing status and metadata"""
        try:
            response = requests.get(
                f"{self.base_url}/document/{doc_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error getting document status: {str(e)}")
            return None

    def get_document_status(self, doc_id: str) -> Dict[str, Any]:
        """Get document status from Chroma"""
        try:
            response = requests.get(
                f"{self.base_url}/documents/{doc_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error getting document status: {str(e)}")
            return {"status": "error", "message": str(e)}
