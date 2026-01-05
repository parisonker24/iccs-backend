from fastapi import APIRouter, Depends
from app.db.session import get_db

router = APIRouter()

@router.get("/")
async def get_users(db=Depends(get_db)):
    return {"message": "Users fetched successfully"}