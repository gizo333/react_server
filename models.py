
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
import bcrypt
from sqlalchemy.dialects.postgresql import UUID


Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, server_default=text("uuid_generate_v4()"))
    fullname = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)

        #хэширует
    def set_password(self, raw_password: str):
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(raw_password.encode('utf-8'), salt).decode('utf-8')
        

        #сравнивает хешированный пароль с введенным паролем
    def verify_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password.encode('utf-8'))



class UserCreate(BaseModel):
    fullname: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    fullname: str
    email: str
    token: str


class UserLogin(BaseModel):
    email: str
    password: str


class EmailSchema(BaseModel):
    email: str
    subject: str
    body: str
