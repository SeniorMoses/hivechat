from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from db import get_db
from models import User
from schemas import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
)


router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
async def signup(
    data: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        print("SIGNUP: received request")

        result = await db.execute(
            select(User).where(
                (User.username == data.username) |
                (User.email == data.email)
            )
        )

        print("SIGNUP: database query completed")

        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username or email already exists"
            )

        print("SIGNUP: user does not exist")

        hashed_password = hash_password(data.password)

        print("SIGNUP: password hashed")

        user = User(
            username=data.username,
            email=data.email,
            password_hash=hashed_password,
        )

        db.add(user)

        print("SIGNUP: user added to session")

        await db.commit()

        print("SIGNUP: commit completed")

        await db.refresh(user)

        print("SIGNUP: refresh completed")

        token = create_access_token(user.id)

        print("SIGNUP: token created")

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise

    except Exception as e:
        print("SIGNUP ERROR:", repr(e))
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Signup failed: {str(e)}"
        )
@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            User.username == data.username
        )
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
    }

@router.get("/users/{user_id}/status")
async def get_user_status(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "user_id": user.id,
        "online": user.online
        }
