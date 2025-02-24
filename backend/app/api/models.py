from pydantic import BaseModel

class QueryRequest(BaseModel):
    text: str
    context_id: str 