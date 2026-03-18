
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    mode: str = Field(default="ep")
    output_format: str = Field(default="structured_text")
    session_id: Optional[str] = None
    user_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompareRequest(BaseModel):
    question: str = Field(..., min_length=1)
    left_mode: str = Field(default="ep")
    right_mode: str = Field(default="baseline")
    output_format: str = Field(default="structured_text")
    session_id: Optional[str] = None
    user_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EPResult(BaseModel):
    ok: bool = True
    answer: str
    mode: str
    session_id: Optional[str] = None
    user_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
