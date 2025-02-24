from typing import List
from pydantic import BaseModel

class Document(BaseModel):
    page_content: str

class Source(BaseModel):
    name: str
    url: str

class Response(BaseModel):
    answer: str
    sources: list[source] = []