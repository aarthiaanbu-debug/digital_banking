from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from reportlab.pdfgen import canvas
import random
import smtplib
from email.mime.text import MIMEText
from fastapi import Header
from fastapi import BackgroundTasks

def get_current_user(authorization: str = Header()):
    token = authorization.split(" ")[1]

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload["sub"]

# ------------------ CONFIG ------------------

DATABASE_URL = "sqlite:///./bank.db"
SECRET_KEY = "secretkey"
ALGORITHM = "HS256"

app = FastAPI()

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ------------------ EMAIL CONFIG ------------------

EMAIL = "aarthiaanbu@gmail.com"
APP_PASSWORD = "pmmvyzxbunhposmn"

def send_otp_email(otp):
    try:
        print("📧 Sending OTP...")

        msg = MIMEText(f"Your OTP is: {otp}")
        msg["Subject"] = "Transaction OTP"
        msg["From"] = EMAIL
        msg["To"] = "aarthia290302@gmail.com"

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        print("🔐 Logging in...")
        server.login(EMAIL, APP_PASSWORD)

        print("📤 Sending mail...")
        server.sendmail(EMAIL, "aarthia290302@gmail.com", msg.as_string())

        server.quit()

        print("✅ EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        print("❌ EMAIL ERROR:", e)

# ------------------ OTP ------------------

otp_store = {}
OTP_LIMIT = 5000

def generate_otp():
    return str(random.randint(100000, 999999))

# ------------------ MODELS ------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    balance = Column(Integer, default=0)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    sender = Column(String)
    receiver = Column(String)
    amount = Column(Integer)

Base.metadata.create_all(bind=engine)

# ------------------ SCHEMAS ------------------

class UserCreate(BaseModel):
    username: str
    password: str

class TransferRequest(BaseModel):
    sender: str
    receiver: str
    amount: int
    otp: str | None = None   # optional OTP

class AddMoneyRequest(BaseModel):
    username: str
    amount: int

# ------------------ DB ------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------ AUTH ------------------

@app.post("/auth/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(username=user.username, password=user.password, balance=0)
    db.add(new_user)
    db.commit()

    return {"message": "User created successfully"}


@app.post("/auth/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()

    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode({"sub": user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}

# ------------------ ACCOUNT ------------------

@app.get("/account/balance")
def get_balance(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"username": username, "balance": user.balance}


@app.post("/account/add-money")
def add_money(data: AddMoneyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.balance += data.amount
    db.commit()

    return {"message": "Money added", "balance": user.balance}

# ------------------ TRANSFER WITH OTP + EMAIL ------------------

@app.post("/account/transfer")

def transfer(
    data: TransferRequest,
    background_tasks: BackgroundTasks,   # ✅ FIRST
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):

    sender = db.query(User).filter(User.username == data.sender).first()
    receiver = db.query(User).filter(User.username == data.receiver).first()

    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    if sender.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # -------- OTP LOGIC --------
    if data.amount > OTP_LIMIT:

        # STEP 1: SEND OTP
        if not data.otp:
            otp = generate_otp()

            print("🔥 OTP GENERATED:", otp)
            
            otp_store[data.sender] = {
    "otp": otp,
    "expiry": datetime.now() + timedelta(minutes=5),
    "attempts": 0   # ✅ ADD HERE
}

           
            send_otp_email(otp)

            return {"detail": "OTP sent to email"}

        # STEP 2: VERIFY OTP
        stored = otp_store.get(data.sender)

    if not stored:
     raise HTTPException(status_code=400, detail="OTP not found")

    if stored["attempts"] >= 3:
     raise HTTPException(status_code=400, detail="Too many attempts")

    if datetime.now() > stored["expiry"]:
     raise HTTPException(status_code=400, detail="OTP expired")

    if stored["otp"] != data.otp:
     stored["attempts"] += 1   # ✅ ADD THIS
    raise HTTPException(status_code=400, detail="Invalid OTP")

    # -------- TRANSFER --------
    sender.balance -= data.amount
    receiver.balance += data.amount

    txn = Transaction(
        sender=data.sender,
        receiver=data.receiver,
        amount=data.amount
    )

    db.add(txn)
    db.commit()

    return {"message": "Transfer successful"}

# ------------------ HISTORY ------------------

@app.get("/transactions/history")
def history(username: str, db: Session = Depends(get_db)):
    txns = db.query(Transaction).filter(
        (Transaction.sender == username) |
        (Transaction.receiver == username)
    ).all()

    return txns

# ------------------ STATEMENT ------------------

@app.get("/transactions/statement")
def statement(username: str, db: Session = Depends(get_db)):
    txns = db.query(Transaction).filter(
        (Transaction.sender == username) |
        (Transaction.receiver == username)
    ).all()

    file_name = f"{username}_statement.pdf"
    c = canvas.Canvas(file_name)

    c.drawString(100, 800, f"Statement for {username}")

    y = 750
    for t in txns:
        c.drawString(100, y, f"{t.sender} -> {t.receiver} : ₹{t.amount}")
        y -= 30

    c.save()

    return FileResponse(file_name, media_type="application/pdf", filename=file_name)