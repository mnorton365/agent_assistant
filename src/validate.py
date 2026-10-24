from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal

class SourceDocument(BaseModel):
    # Purpose: Validates document records before ingestion pipeline.

    # Establish Config settings
    model_config = ConfigDict(
        extra = "forbid",
        str_strip_whitespace = True)
    
    # Set data types
    document_id: str = Field(min_length = 1, max_length = 200)
    title: str = Field(min_length = 1, max_length = 500)
    source: str = Field(min_length = 1, max_length = 500)
    updated_at: datetime
    classification: Literal["PUBLIC", "INTERNAL"]
    text: str = Field(min_length = 1)

    # Validate updated_at field
    @field_validator("updated_at")
    @classmethod
    def require_timezone(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("updated_at field must include a timezone.")
        return value.astimezone(timezone.utc)
    
    # Validate text field
    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str):
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("text field can't be empty.")
        return normalized