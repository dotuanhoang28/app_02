from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
import uvicorn
import datetime
from datetime import date
import os
import json
import re
from fastapi import Request
USER_FILE = os.path.join(os.path.dirname(__file__), "users.txt")

app = FastAPI(title="Basic User CRUD API")

class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    age: int
    dob: str
    address: str
    phone_number: str
    email: str
    username: str
    password: str = Field(..., exclude=True)


# DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:my-secret-pw@mysql_service/userdb")
DATABASE_URL = os.getenv("DATABASE_URL")
# check if database url not exit, print error and exit program
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable is not set!")
    print("Please set DATABASE_URL before running the application.")
    print("Example: export DATABASE_URL='sqlite:///./test.db'")
    exit(1)

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session


# In-memory store as indexable list by numeric ID. Use None for deleted slots to keep IDs stable.
def load_users_from_file():
    users = []
    if not os.path.exists(USER_FILE):
        return users
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line.strip())
                users.append(rec)
    except Exception:
        pass  # empty/corrupt file
    return users

user_store: List[Optional[Dict[str, Any]]] = load_users_from_file()

# write a functions to:
# 1. get all users
# 2. get a user by id
# 3. create a user, if user email or phone number already exists, return an error
# 4. update a user by id
# 5. delete a user by id



# Test 1: 11 so
# Test 2: 9 so
# Test 3: 10 so co chu cai
# Test 4: 10 so co ki tu dac biet
# Test 5: +84
# Test 6: Sdt hop le

def is_phone_number_valid(phone_number: str) -> bool:

    pattern = re.compile('^(?:\+84|0)\d{9}$')
    return bool(pattern.match(phone_number))

def is_email_valid(email: str) -> bool:
    # More specific validation using a regular expression for standard email formats
    if not isinstance(email, str):
        return False
    email_regex = re.compile(
    r"^[A-Za-z0-9._%+-]+@"                              # local part
    r"(?:[A-Za-z0-9]"                                   # domain label must start with alnum
    r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"           # optional middle chars, label end alnum, then dot
    r"[A-Za-z]{2,}$"                                    # TLD (2+ letters)
)
    return re.match(email_regex, email) is not None


def is_age_valid(age: int) -> bool:
    try:
        age_int = int(age)
        return 0 < age_int < 100
    except ValueError:
        return False

def is_dob_valid(dob: str) -> bool:
    try:
        dob_date = datetime.date.fromisoformat(dob)
        today = datetime.date.today()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        # Age must be > 0 and < 100 years
        return 0 < age < 100
    except ValueError:
        return False

# Age and dob synchronization
def check_age_matches_dob(cls, values):
        
        dob = values.get("date_of_birth")
        age = values.get("age")
        if dob and age is not None:
            today = date.today()
            calculated_age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
            if calculated_age != age:
                raise ValueError(f"Provided age ({age}) does not match date of birth ({dob}). Calculated age is {calculated_age}.")
            if age < 13:
                raise ValueError("User must be at least 13 years old.")
        return values

def is_username_valid(username: str) -> bool:
    if not isinstance(username, str):
        return False
    pattern = r'^[A-Za-z][A-Za-z0-9_]{2,19}$'
    return bool(re.match(pattern, username))

def save_users_to_file():
    # Only save non-None users
    with open(USER_FILE, "w", encoding="utf-8") as f:
        for user in user_store:
           if user is not None:
                # Save all fields
                f.write(json.dumps(user) + "\n")


@app.post("/users/")
def create_user(user: User, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")
    existing = session.exec(select(User).where(User.phone_number == user.phone_number)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Phone number already exists")
    existing = session.exec(select(User).where(User.username == user.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username is used")
    
    if not is_email_valid(user.email):
        raise HTTPException(status_code=422, detail="Invalid email format")
    if not is_phone_number_valid(user.phone_number):
        raise HTTPException(status_code=422, detail="Invalid phone number format")
    if not is_age_valid(user.age):
        raise HTTPException(status_code=422, detail="Invalid age format")
    if not is_dob_valid(user.dob):
        raise HTTPException(status_code=422, detail="Invalid dob format")
    if not is_username_valid(user.username):
        raise HTTPException(status_code=422, detail="Invalid username format")
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "User created successfully", "user_id": user.id}


# Get all users in database
@app.get("/users/")
def get_all_users(request: Request, session: Session = Depends(get_session)):
    client_ip = request.client.host
    print(f"Client IP: {client_ip}")  # log to console
    users = session.exec(select(User)).all()
    return {"client_ip": client_ip, "users": users}


# Get user by id
@app.get("/users/{user_id}")
def get_user_by_id(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Delete user by id
@app.delete("/users/{user_id}")
def delete_user_by_id(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"message": "User deleted successfully"}

# Update user by id
@app.patch("/users/{user_id}")
def update_user_by_id(user_id: int, user_update: User, session: Session = Depends(get_session)):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update only provided fields
    user_data = user_update.model_dump(exclude_unset=True, exclude={"id"})
    for field, value in user_data.items():
        setattr(db_user, field, value)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return {"message": "User updated successfully", "user": db_user}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
# print ip address of requests
