import random
import re
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.language import Language
from app.models.script import DurationCategory, Script
from app.schemas.script import (
    RandomScriptRequest,
    ScriptCreate,
    ScriptListResponse,
    ScriptUpdate,
    ScriptValidationResponse,
)


class ScriptService:
    """Service for managing scripts and script-related operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_script(self, script_data: ScriptCreate) -> Script:
        """Create a new script with validation."""
        # Validate language exists
        language = (
            self.db.query(Language)
            .filter(Language.id == script_data.language_id)
            .first()
        )
        if not language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Language with ID {script_data.language_id} not found",
            )

        # Validate script content
        validation_result = self.validate_script_content(
            script_data.text, script_data.duration_category
        )
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Script validation failed: {', '.join(validation_result.errors)}",
            )

        # Create script
        db_script = Script(
            text=script_data.text,
            duration_category=script_data.duration_category,
            language_id=script_data.language_id,
            meta_data=script_data.meta_data or {},
        )

        # Add validation metadata
        db_script.meta_data.update(
            {
                "word_count": validation_result.word_count,
                "character_count": validation_result.character_count,
                "estimated_duration": validation_result.estimated_duration,
            }
        )

        self.db.add(db_script)
        self.db.commit()
        self.db.refresh(db_script)
        return db_script

    def get_script_by_id(self, script_id: int) -> Optional[Script]:
        """Get script by ID."""
        return self.db.query(Script).filter(Script.id == script_id).first()

    def get_scripts(
        self,
        skip: int = 0,
        limit: int = 100,
        duration_category: Optional[DurationCategory] = None,
        language_id: Optional[int] = None,
    ) -> ScriptListResponse:
        """Get paginated list of scripts with optional filtering."""
        query = self.db.query(Script)

        # Apply filters
        if duration_category:
            query = query.filter(Script.duration_category == duration_category)
        if language_id:
            query = query.filter(Script.language_id == language_id)

        # Get total count
        total = query.count()

        # Apply pagination
        scripts = query.offset(skip).limit(limit).all()

        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        page = (skip // limit) + 1

        return ScriptListResponse(
            scripts=scripts,
            total=total,
            page=page,
            per_page=limit,
            total_pages=total_pages,
        )

    def update_script(self, script_id: int, script_data: ScriptUpdate) -> Script:
        """Update an existing script."""
        script = self.get_script_by_id(script_id)
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Script not found"
            )

        # Update fields if provided
        update_data = script_data.model_dump(exclude_unset=True)

        # Validate language if being updated
        if "language_id" in update_data:
            language = (
                self.db.query(Language)
                .filter(Language.id == update_data["language_id"])
                .first()
            )
            if not language:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Language with ID {update_data['language_id']} not found",
                )

        # Validate script content if text or duration category is being updated
        if "text" in update_data or "duration_category" in update_data:
            new_text = update_data.get("text", script.text)
            new_duration = update_data.get(
                "duration_category", script.duration_category
            )

            validation_result = self.validate_script_content(new_text, new_duration)
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Script validation failed: {', '.join(validation_result.errors)}",
                )

            # Update metadata with validation results
            if script.meta_data is None:
                script.meta_data = {}
            script.meta_data.update(
                {
                    "word_count": validation_result.word_count,
                    "character_count": validation_result.character_count,
                    "estimated_duration": validation_result.estimated_duration,
                }
            )

        # Apply updates
        for field, value in update_data.items():
            setattr(script, field, value)

        self.db.commit()
        self.db.refresh(script)
        return script

    def delete_script(self, script_id: int) -> bool:
        """Delete a script by ID."""
        script = self.get_script_by_id(script_id)
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Script not found"
            )

        # Check if script is being used in recordings
        from app.models.voice_recording import VoiceRecording

        recordings_count = (
            self.db.query(VoiceRecording)
            .filter(VoiceRecording.script_id == script_id)
            .count()
        )

        if recordings_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete script: {recordings_count} voice recordings are using this script",
            )

        self.db.delete(script)
        self.db.commit()
        return True

    def get_random_script(self, request: RandomScriptRequest) -> Optional[Script]:
        """Get a random script based on duration category and language."""
        # Default to Bangla if no language specified
        language_id = request.language_id
        if language_id is None:
            bangla_lang = self.db.query(Language).filter(Language.code == "bn").first()
            if bangla_lang:
                language_id = bangla_lang.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bangla language not found and no language_id specified",
                )

        # Query for scripts matching criteria
        scripts = (
            self.db.query(Script)
            .filter(
                and_(
                    Script.duration_category == request.duration_category,
                    Script.language_id == language_id,
                )
            )
            .all()
        )

        if not scripts:
            return None

        # Return random script
        return random.choice(scripts)

    def validate_script_content(
        self, text: str, duration_category: DurationCategory
    ) -> ScriptValidationResponse:
        """Validate script content and estimate reading duration."""
        errors = []
        warnings = []

        # Basic text validation
        if not text or not text.strip():
            errors.append("Script text cannot be empty")
            return ScriptValidationResponse(
                is_valid=False, errors=errors, word_count=0, character_count=0
            )

        text = text.strip()

        # Count words and characters
        # For Bangla text, we need to handle Unicode properly
        word_count = len(re.findall(r"\S+", text))
        character_count = len(text)

        # Estimate reading duration (average reading speed: 200 words per minute)
        estimated_duration = word_count / 200.0

        # Validate duration category alignment
        duration_ranges = {
            DurationCategory.SHORT: (1.5, 2.5),  # 2 minutes ± 30 seconds
            DurationCategory.MEDIUM: (4.0, 6.0),  # 5 minutes ± 1 minute
            DurationCategory.LONG: (8.0, 12.0),  # 10 minutes ± 2 minutes
        }

        expected_min, expected_max = duration_ranges[duration_category]

        if estimated_duration < expected_min:
            warnings.append(
                f"Script may be too short for {duration_category.value} category. "
                f"Estimated: {estimated_duration:.1f} min, Expected: {expected_min}-{expected_max} min"
            )
        elif estimated_duration > expected_max:
            warnings.append(
                f"Script may be too long for {duration_category.value} category. "
                f"Estimated: {estimated_duration:.1f} min, Expected: {expected_min}-{expected_max} min"
            )

        # Check for minimum content requirements
        if word_count < 10:
            errors.append("Script must contain at least 10 words")

        if character_count < 50:
            errors.append("Script must contain at least 50 characters")

        # Check for maximum content limits
        if word_count > 3000:
            errors.append("Script cannot exceed 3000 words")

        if character_count > 10000:
            errors.append("Script cannot exceed 10000 characters")

        return ScriptValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            estimated_duration=estimated_duration,
            word_count=word_count,
            character_count=character_count,
        )

    def get_script_statistics(self) -> Dict[str, Any]:
        """Get statistics about scripts in the database."""
        total_scripts = self.db.query(Script).count()

        # Count by duration category
        duration_stats = {}
        for category in DurationCategory:
            count = (
                self.db.query(Script)
                .filter(Script.duration_category == category)
                .count()
            )
            duration_stats[category.value] = count

        # Count by language
        language_stats = (
            self.db.query(
                Language.name,
                Language.code,
                func.count(Script.id).label("script_count"),
            )
            .join(Script)
            .group_by(Language.id, Language.name, Language.code)
            .all()
        )

        return {
            "total_scripts": total_scripts,
            "by_duration": duration_stats,
            "by_language": [
                {"language": lang.name, "code": lang.code, "count": lang.script_count}
                for lang in language_stats
            ],
        }
