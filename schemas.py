from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"   # default user

class UserLogin(BaseModel):
    username: str
    password: str
