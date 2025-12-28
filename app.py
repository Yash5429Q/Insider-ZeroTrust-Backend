from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_current_user, admin_required
from database import Base, engine, SessionLocal
import models    # ← very important
from schemas import UserCreate, UserLogin
from auth import hash_password, verify_password, create_access_token
from models import Log

app = FastAPI()

# Create tables in database automatically
Base.metadata.create_all(bind=engine)


# Create DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------ REGISTER USER ------------------
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check existing user
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(user.password)
    new_user = models.User(username=user.username, password=hashed_pw, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user": new_user.username}


# ------------------ LOGIN USER ------------------
@app.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "role": user.role}


# Protected Route (User must be logged in)
@app.get("/profile")
def profile(current_user = Depends(get_current_user)):
    return {"message": "Welcome!", "user": current_user.username, "role": current_user.role}


# Admin-only route (Only for admins)
@app.get("/admin/dashboard")
def admin_dashboard(current_user = Depends(admin_required)):
    return {"message": "Admin Panel Access Granted", "user": current_user.username}



# ---------------------- Log Collection ----------------------
@app.post("/collect-log")
def collect_log(data: dict, db: Session = Depends(get_db)):
    log = Log(
        username=data.get("username"),
        action=data.get("action"),
        details=data.get("details", ""),
        ip_address=data.get("ip_address"),
        device=data.get("device")
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"message": "Log received", "log_id": log.id}


# ---------------------- View Logs (Admin Only) ----------------------
@app.get("/logs")
def get_logs(db: Session = Depends(get_db), current_user = Depends(admin_required)):
    logs = db.query(Log).all()
    return logs