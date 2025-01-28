from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import text, create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from pydantic import BaseModel
import bcrypt 

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:adminpassword@postgres:5432/app_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class FirstUserCreate(BaseModel):
    user_name: str
    password: str

# Utility function to hash the password
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

class Role(Base):
    __tablename__ = 'roles'
    role_id = Column(Integer, primary_key=True)
    role_name = Column(String, unique=True)

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String, unique=True)
    password = Column(String)
    role_id = Column(Integer)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

def create_database_if_not_exists(database_url):
    # Extract default database connection string (using 'postgres' as the database name)
    default_db_url = database_url.split('/')[0] + '//' + database_url.split('/')[2] + '/' + 'postgres'
    db_name = database_url.split('/')[-1]

    # Create an engine for the default database
    default_engine = create_engine(default_db_url)

    # Connect to the default database with autocommit
    with default_engine.connect() as connection:
        # Explicitly enable autocommit for this connection
        connection = connection.execution_options(isolation_level="AUTOCOMMIT")

        # Check if the database already exists
        result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
        if not result.fetchone():
            # Create the database if it does not exist
            connection.execute(text(f"CREATE DATABASE {db_name}"))

@app.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI!"}

@app.post("/install")
async def install():
    # Check and create the database if it does not exist
    create_database_if_not_exists(DATABASE_URL)
    
    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)
    
    # Create an admin role if it does not exist
    with sessionmaker(bind=engine)() as session:
        if not session.query(Role).filter_by(role_name='admin').first():
            admin_role = Role(role_name='admin')
            session.add(admin_role)
            session.commit()
    
    return {"message": "Tables checked and created if not exist, admin role added."}

@app.post("/create-first-user")
async def create_first_user(user: FirstUserCreate, db: Session = Depends(get_db)):
    # Check if the users table already has an entry
    existing_user = db.query(User).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user already exists in the system.")

    # Check if the "admin" role exists
    admin_role = db.query(Role).filter_by(role_name="admin").first()
    if not admin_role:
        raise HTTPException(status_code=400, detail="Admin role does not exist. Please run the installation first.")

    # Hash the provided password
    hashed_password = hash_password(user.password)

    # Create the first user and assign the "admin" role
    first_user = User(user_name=user.user_name, password=hashed_password, role_id=admin_role.role_id)
    db.add(first_user)
    db.commit()
    db.refresh(first_user)

    return {"message": "First user created and assigned the admin role.", "user_id": first_user.user_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
