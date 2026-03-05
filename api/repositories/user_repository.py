from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import User


def get_or_create_default_user(db: Session) -> User:
    user = db.execute(select(User).order_by(User.created_at).limit(1)).scalar_one_or_none()
    if user is None:
        user = User(email="athlete@training-lab.local", timezone="America/New_York")
        db.add(user)
        db.flush()
    return user
