from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.auth import get_password_hash, verify_password, create_access_token, get_current_user
import uuid
from datetime import datetime, timezone

router = APIRouter()

# In-memory mock DB for now (Replaced by Postgres in Phase 8)
fake_users_db = {}

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    if user.email in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    user_id = uuid.uuid4()
    
    user_dict = {
        "id": user_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": "user",
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc)
    }
    
    fake_users_db[user.email] = user_dict
    return user_dict

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(
        data={"sub": user_dict["email"], "role": user_dict["role"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=dict)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user, "message": "You are authenticated!"}
