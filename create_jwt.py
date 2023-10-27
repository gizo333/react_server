from fastapi import HTTPException
import jwt
from datetime import datetime, timedelta
from jwt.exceptions import PyJWTError

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_jwt_token(data: dict):
    expiration = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        "exp": expiration,
        **data,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return None