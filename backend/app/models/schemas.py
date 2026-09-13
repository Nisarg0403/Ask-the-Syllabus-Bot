from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str = Field(..., description="User question to answer against syllabi")
    provider: str = Field(default="Ollama", description="LLM Provider: Ollama or OpenRouter")
    model: str = Field(..., description="Target model name")
    api_key: Optional[str] = Field(default=None, description="OpenRouter API key if applicable")
    k: int = Field(default=4, ge=1, le=10, description="Top-k chunks to retrieve")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="LLM sampling temperature")

class DocumentInfo(BaseModel):
    filename: str
    size: str
    indexed_at: str

class DocumentsResponse(BaseModel):
    documents: List[DocumentInfo]

class StatusResponse(BaseModel):
    active: bool
    size: str
    raw_size_bytes: int

class ModelsResponse(BaseModel):
    online: bool
    models: List[str]
