from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import crud, schemas, models, auth
from database import SessionLocal, engine
from datetime import timedelta, datetime
import redis
import json
import os
import logging
import platform
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц в базе данных
models.Base.metadata.create_all(bind=engine)

# Инициализация FastAPI приложения
app = FastAPI(
    title="User Service API",
    description="API для управления пользователями с аутентификацией и кешированием",
    version="1.1.0",
    docs_url="/docs",
    redoc_url=None
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация Redis
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=6379,
        decode_responses=True
    )
    # Проверка соединения с Redis
    redis_client.ping()
except Exception as e:
    logger.error(f"Ошибка подключения к Redis: {str(e)}")
    redis_client = None

# Схема аутентификации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис Redis недоступен"
        )
    return redis_client

@app.on_event("startup")
async def startup_event():
    logger.info("Запуск User Service")
    logger.info(f"Версия Python: {platform.python_version()}")
    logger.info(f"Система: {platform.system()} {platform.release()}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Остановка User Service")
    if redis_client:
        redis_client.close()

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Мониторинг"])
@app.get("/healthcheck", tags=["Мониторинг"])
async def health_check():
    """Проверка работоспособности сервиса"""
    db_ok = False
    redis_ok = False
    
    # Проверка базы данных
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья БД: {str(e)}")
    
    # Проверка Redis
    if redis_client:
        try:
            redis_client.ping()
            redis_ok = True
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья Redis: {str(e)}")
    
    if not db_ok or not redis_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Зависимости сервиса недоступны",
            headers={"Retry-After": "10"}
        )
    
    return {
        "status": "OK",
        "service": "user_service",
        "version": "1.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "database": "connected" if db_ok else "disconnected",
            "redis": "connected" if redis_ok else "disconnected"
        }
    }

@app.post("/users/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Создание нового пользователя"""
    try:
        db_user = crud.create_user(db=db, user=user)
        if redis_client:
            redis_client.delete("all_users")
        return db_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/", response_model=List[schemas.UserOut])
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получение списка пользователей"""
    try:
        return crud.get_users(db, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка сервера")

@app.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Аутентификация и получение токена"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/uncached", tags=["Тестирование"])
async def uncached_data(db: Session = Depends(get_db)):
    """Эндпоинт без кеширования (для тестирования производительности)"""
    start_time = time.time()
    # Имитация запроса к БД
    time.sleep(0.01)
    return {
        "message": "Данные без кеширования",
        "query_time": time.time() - start_time
    }

@app.get("/api/cached", tags=["Тестирование"])
async def cached_data(redis: redis.Redis = Depends(get_redis)):
    """Эндпоинт с кешированием (для тестирования производительности)"""
    start_time = time.time()
    
    cached = redis.get("test_cache")
    if not cached:
        # Имитация долгого запроса
        time.sleep(0.01)
        data = {"message": "Кешированные данные", "query_time": time.time() - start_time}
        redis.setex("test_cache", 30, json.dumps(data))  # Кеш на 30 секунд
        return data
    
    return json.loads(cached)