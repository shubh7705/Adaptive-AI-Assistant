from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database.session import get_db
from app.models.registry import ModelRegistry
from app.schemas.registry import ModelRegistryCreate, ModelRegistryResponse
from app.services.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[ModelRegistryResponse])
async def get_all_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelRegistry).where(ModelRegistry.is_active))
    models = result.scalars().all()
    
    # If the DB is empty (e.g. fresh start), we can return a mocked list based on the original requirements
    if not models:
        return [
            {
                "id": "mock-deepseek",
                "name": "deepseek/deepseek-chat-v3-0324",
                "provider": "OpenRouter",
                "description": "Optimized for programming, debugging, and code generation.",
                "cost_per_1k_tokens": 0.002,
                "supports_streaming": True,
                "supports_vision": False,
                "supports_tools": True,
                "is_active": True,
                "created_at": "2026-06-30T00:00:00Z",
                "updated_at": "2026-06-30T00:00:00Z"
            }
        ]
    return models

@router.post("/", response_model=ModelRegistryResponse, status_code=status.HTTP_201_CREATED)
async def add_model(
    model_data: ModelRegistryCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to add models")
        
    # Check if model already exists
    result = await db.execute(select(ModelRegistry).where(ModelRegistry.name == model_data.name))
    existing_model = result.scalars().first()
    if existing_model:
        raise HTTPException(status_code=400, detail="Model already registered")
        
    new_model = ModelRegistry(**model_data.model_dump())
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)
    
    return new_model
