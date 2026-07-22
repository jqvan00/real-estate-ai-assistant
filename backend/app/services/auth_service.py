from sqlalchemy.orm import Session

from app.core.security import generate_token
from app.models.user import User


def register_user(db: Session, email: str, password: str, full_name: str | None = None) -> tuple[User, str]:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return existing, generate_token()

    user = User(email=email, password=password, full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, generate_token()


def login_user(db: Session, email: str, password: str) -> str:
    user = db.query(User).filter(User.email == email).first()
    if not user or user.password != password:
        raise ValueError("Invalid credentials")
    return generate_token()
