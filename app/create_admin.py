from getpass import getpass

from sqlalchemy.orm import Session

from app.auth.roles import ADMIN
from app.auth.security import hash_password
from app.database import SessionLocal
from app.models import User


def create_admin():
    db: Session = SessionLocal()

    try:
        email = input("Admin email: ").strip()
        full_name = input("Admin full name: ").strip()
        password = getpass("Admin password: ")

        if not email or not full_name or not password:
            print("All fields are required.")
            return

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("A user with this email already exists.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=ADMIN,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print()
        print("Admin user created successfully!")
        print(f"ID: {admin.id}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")

    except Exception as e:
        db.rollback()
        print(f"Failed to create admin: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()