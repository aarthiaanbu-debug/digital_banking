from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from reportlab.pdfgen import canvas

# ------------------ CONFIG ------------------

DATABASE_URL = "sqlite:///./bank.db"

SECRET_KEY = "secretkey"
ALGORITHM = "HS256"

app = FastAPI()

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

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

# ------------------ JWT ------------------

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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

    token = create_token({"sub": user.username})
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


@app.post("/account/transfer")
def transfer(data: TransferRequest, db: Session = Depends(get_db)):
    sender = db.query(User).filter(User.username == data.sender).first()
    receiver = db.query(User).filter(User.username == data.receiver).first()

    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    if sender.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

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

# ------------------ TRANSACTIONS ------------------

@app.get("/transactions/history")
def history(username: str, db: Session = Depends(get_db)):
    txns = db.query(Transaction).filter(
        (Transaction.sender == username) |
        (Transaction.receiver == username)
    ).all()

    result = []
    for t in txns:
        result.append({
            "sender": t.sender,
            "receiver": t.receiver,
            "amount": t.amount
        })

    return result


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
        line = f"{t.sender} -> {t.receiver} : ₹{t.amount}"
        c.drawString(100, y, line)
        y -= 30

    c.save()

    return FileResponse(file_name, media_type="application/pdf", filename=file_name)