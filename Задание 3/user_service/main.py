from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import crud, schemas, models, auth
from database import get_db, engine
from datetime import timedelta

models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="User Service API",
    description="API для управления пользователями",
    version="1.0.0"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "user_service",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.post("/users/", 
          response_model=schemas.UserOut,
          status_code=status.HTTP_201_CREATED,
          tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    return crud.create_user(db=db, user=user)


@app.get("/users/", 
         response_model=List[schemas.UserOut],
         tags=["Users"])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):

    return crud.get_users(db, skip=skip, limit=limit)


@app.post("/token", 
          response_model=schemas.Token,
          tags=["Authentication"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):

    try:

        db.execute("SELECT 1")
        return {
            "status": "OK",
            "database": "connected",
            "service": "user_service"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )