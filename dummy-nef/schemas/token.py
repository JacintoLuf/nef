from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    email: EmailStr = None
    token: str = None
    timestamp: int = None