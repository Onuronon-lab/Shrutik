from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.script import DurationCategory


class ScriptBase(BaseModel):
    """Base script schema with common fields."""

    text: str = Field(
        ..., min_length=1, max_length=10000, description="Script text content"
    )
    duration_category: DurationCategory = Field(
        ..., description="Duration category for the script"
    )
    language_id: int = Field(..., gt=0, description="Language ID")
    meta_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate script text content."""
        if not v.strip():
            raise ValueError("Script text cannot be empty or whitespace only")
        return v.strip()


class ScriptCreate(ScriptBase):
    """Schema for creating a new script."""


class ScriptUpdate(BaseModel):
    """Schema for updating an existing script."""

    text: Optional[str] = Field(None, min_length=1, max_length=10000)
    duration_category: Optional[DurationCategory] = None
    language_id: Optional[int] = Field(None, gt=0)
    meta_data: Optional[Dict[str, Any]] = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate script text content if provided."""
        if v is not None and not v.strip():
            raise ValueError("Script text cannot be empty or whitespace only")
        return v.strip() if v else v


class ScriptResponse(ScriptBase):
    """Schema for script response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScriptListResponse(BaseModel):
    """Schema for paginated script list response."""

    scripts: list[ScriptResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class RandomScriptRequest(BaseModel):
    """Schema for requesting a random script."""

    duration_category: DurationCategory = Field(
        ..., description="Desired duration category"
    )
    language_id: Optional[int] = Field(
        None, gt=0, description="Language ID (optional, defaults to Bangla)"
    )


class ScriptValidationResponse(BaseModel):
    """Schema for script validation response."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    estimated_duration: Optional[float] = Field(
        None, description="Estimated reading duration in minutes"
    )
    word_count: int
    character_count: int
