from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import models
from fastapi.middleware.cors import CORSMiddleware
from database import get_db
from typing import Dict
from datetime import datetime, timedelta
from starlette.middleware.base import BaseHTTPMiddleware
from create_jwt import create_jwt_token
from send_mail import router




app = FastAPI()

# Настройка CORS
origins = [
    "*",  # Разрешаем доступ с этого домена и порта
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ограничиваем количество регистраций с одного IP
REGISTRATION_LIMIT = 5
# Ограничиваем период времени, в течение которого допустимо указанное количество регистраций
LIMIT_PERIOD = timedelta(hours=1)

# Это in-memory хранилище. В продакшн-решении следует использовать БД или кеш
registrations: Dict[str, list] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "/users/" in request.url.path and request.method.lower() == "post":
            ip_address = request.client.host

            # Удалить устаревшие записи о регистрациях
            now = datetime.utcnow()
            if ip_address in registrations:
                registrations[ip_address] = [
                    time for time in registrations[ip_address]
                    if now - time <= LIMIT_PERIOD
                ]
            
            # Проверка, не превышен ли лимит
            if (
                ip_address in registrations and
                len(registrations[ip_address]) >= REGISTRATION_LIMIT
):
                print(f"IP: {ip_address}, Attempts: {len(registrations[ip_address])}, Reg Limit: {REGISTRATION_LIMIT}")
                raise HTTPException(
                    status_code=429,
                    detail="Too many registration attempts. Please try again later."
    )

            
            # Добавление записи о текущей попытке регистрации
            registrations.setdefault(ip_address, []).append(now)
            
        return await call_next(request)


app.add_middleware(RateLimitMiddleware)


# регистрация пользователя
@app.post("/users/", response_model=models.UserResponse)
async def create_user(user: models.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    

    db_user = models.User(**user.model_dump())
    #Хеширование пароля перед сохранением
    db_user.set_password(user.password)
    try:
        db.add(db_user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.refresh(db_user)

    token = create_jwt_token({"user_id": str(db_user.user_id)})

    return models.UserResponse(id=db_user.id, fullname=db_user.fullname, email=db_user.email, token=token)

    #вход уже существующего пользователя
@app.post("/login/")
async def login(user_login: models.UserLogin, db: Session = Depends(get_db)):
    # Шаг 2: Поиск пользователя в базе данных
    db_user = db.query(models.User).filter(models.User.email == user_login.email).first()

    # Пользователь не найден
    if not db_user:
        raise HTTPException(status_code=400, detail="Неверный email или пароль")

    # Шаг 3: Проверка пароля
    if not db_user.verify_password(user_login.password):
        raise HTTPException(status_code=421, detail="Неверный email или пароль")

    # Шаг 4: Генерация токена
    token = create_jwt_token({"user_id": str(db_user.user_id)})


    # Шаг 5: Отправка ответа
    return {"token": token}




app.include_router(router)
