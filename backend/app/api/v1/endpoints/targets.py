"""
Target endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.target import Target
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


class TargetCreate(BaseModel):
    url: str
    name: Optional[str] = None
    description: Optional[str] = None
    asset_value: Optional[str] = None  # 'critical', 'high', 'low'


class TargetResponse(BaseModel):
    id: int
    url: str
    name: Optional[str] = None
    description: Optional[str] = None
    asset_value: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new target or return existing one"""
    from sqlalchemy.exc import IntegrityError
    
    # Normalize URL (remove trailing slash, lowercase, etc.)
    normalized_url = target_data.url.strip().rstrip('/')
    
    # Check if target URL already exists for this user
    existing = db.query(Target).filter(
        Target.url == normalized_url,
        Target.user_id == current_user.id
    ).first()
    
    if existing:
        # Target already exists for this user, return it
        return existing
    
    # Check if URL exists globally (for any user)
    existing_global = db.query(Target).filter(Target.url == normalized_url).first()
    if existing_global:
        # URL exists but for different user - return it anyway (allow sharing)
        # Or you could raise an error if you want to prevent sharing
        return existing_global
    
    # Create new target
    try:
        target = Target(
            user_id=current_user.id,
            url=normalized_url,
            name=target_data.name or normalized_url,
            description=target_data.description,
            asset_value=target_data.asset_value or "low"
        )
        
        db.add(target)
        db.commit()
        db.refresh(target)
        
        return target
    except IntegrityError as e:
        # Handle unique constraint violation
        db.rollback()
        # Try to get the existing target
        existing_global = db.query(Target).filter(Target.url == normalized_url).first()
        if existing_global:
            return existing_global
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target URL '{normalized_url}' already exists"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create target: {str(e)}"
        )


@router.get("", response_model=List[TargetResponse])
async def get_targets(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all targets for current user"""
    targets = db.query(Target)\
        .filter(Target.user_id == current_user.id)\
        .order_by(Target.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return targets


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific target by ID"""
    target = db.query(Target)\
        .filter(Target.id == target_id, Target.user_id == current_user.id)\
        .first()
    
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found"
        )
    
    return target


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a target"""
    target = db.query(Target)\
        .filter(Target.id == target_id, Target.user_id == current_user.id)\
        .first()
    
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found"
        )
    
    db.delete(target)
    db.commit()
    
    return None

