from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import (
    get_current_active_user, 
    require_admin, 
    require_admin_or_sworik
)
from app.models.user import User
from app.models.script import DurationCategory
from app.schemas.script import (
    ScriptCreate, ScriptUpdate, ScriptResponse, ScriptListResponse,
    RandomScriptRequest, ScriptValidationResponse
)
from app.services.script_service import ScriptService

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.get("/random", response_model=ScriptResponse)
async def get_random_script(
    duration_category: DurationCategory = Query(..., description="Duration category for the script"),
    language_id: Optional[int] = Query(None, description="Language ID (optional, defaults to Bangla)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a random script based on duration category.
    
    This endpoint serves random scripts to contributors for voice recording.
    Requires authentication but no special permissions.
    """
    script_service = ScriptService(db)
    
    request = RandomScriptRequest(
        duration_category=duration_category,
        language_id=language_id
    )
    
    script = script_service.get_random_script(request)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scripts found for duration category '{duration_category.value}'"
        )
    
    return script


@router.post("/validate", response_model=ScriptValidationResponse)
async def validate_script(
    text: str,
    duration_category: DurationCategory,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Validate script content and get estimated reading duration.
    
    Admin-only endpoint for validating scripts before creation.
    """
    script_service = ScriptService(db)
    return script_service.validate_script_content(text, duration_category)


@router.get("/", response_model=ScriptListResponse)
async def list_scripts(
    skip: int = Query(0, ge=0, description="Number of scripts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of scripts to return"),
    duration_category: Optional[DurationCategory] = Query(None, description="Filter by duration category"),
    language_id: Optional[int] = Query(None, description="Filter by language ID"),
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of scripts with optional filtering.
    
    Available to admins and Sworik developers for script management and review.
    """
    script_service = ScriptService(db)
    return script_service.get_scripts(
        skip=skip,
        limit=limit,
        duration_category=duration_category,
        language_id=language_id
    )


@router.get("/statistics")
async def get_script_statistics(
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Get statistics about scripts in the database.
    
    Available to admins and Sworik developers for monitoring and reporting.
    """
    script_service = ScriptService(db)
    return script_service.get_script_statistics()


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Get a specific script by ID.
    
    Available to admins and Sworik developers for script review and management.
    """
    script_service = ScriptService(db)
    script = script_service.get_script_by_id(script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    return script


@router.post("/", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_script(
    script_data: ScriptCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new script.
    
    Admin-only endpoint for adding new scripts to the repository.
    Includes automatic validation of script content and duration alignment.
    """
    script_service = ScriptService(db)
    return script_service.create_script(script_data)


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    script_data: ScriptUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update an existing script.
    
    Admin-only endpoint for modifying scripts in the repository.
    Includes automatic validation of updated content.
    """
    script_service = ScriptService(db)
    return script_service.update_script(script_id, script_data)


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a script.
    
    Admin-only endpoint for removing scripts from the repository.
    Prevents deletion if the script is referenced by existing voice recordings.
    """
    script_service = ScriptService(db)
    script_service.delete_script(script_id)
    return None