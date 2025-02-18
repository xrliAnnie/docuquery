import requests
from typing import Dict, Any


class APIClient:
    def __init__(self):
        self.base_url = "http://localhost:8001/api/v1"  # FastAPI backend URL

    def upload_document(self, file) -> Dict[str, Any]:
        """Upload document to backend"""
        try:
            response = requests.post(
                f"{self.base_url}/ingest",
                files={"file": file}
            )
            return response.json()
        except Exception as e:
            st.error(f"Error uploading document: {str(e)}")
            return {"status": "error", "message": str(e)}

    def query_document(self, doc_id: str, question: str) -> Dict[str, Any]:
        """Query document with a question"""
        try:
            response = requests.post(
                f"{self.base_url}/query",
                json={"doc_id": doc_id, "question": question}
            )
            return response.json()
        except Exception as e:
            st.error(f"Error querying document: {str(e)}")
            return {"status": "error", "message": str(e)}
