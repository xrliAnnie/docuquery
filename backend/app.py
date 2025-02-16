from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class Query(BaseModel):
    question: str
    context_id: Optional[str] = None

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """Endpoint to ingest documents and create embeddings"""
    pass

@app.post("/query")
async def query_document(query: Query):
    """Endpoint to query the document based on user questions"""
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)