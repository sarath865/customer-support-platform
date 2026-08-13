from getpass import getpass

from sqlalchemy.orm import Session

from app.auth.roles import ADMIN
from app.auth.security import hash_password
from app.database import SessionLocal
from app.models import User


def reset_admin():
    db: Session = SessionLocal()

    try:
        admin = (
            db.query(User)
            .filter(User.id == 3)
            .first()
        )

        if admin is None:
            print("Admin user with ID 3 was not found.")
            return

        print(f"Current email: {admin.email}")
        print(f"Current role: {admin.role}")

        admin.email = "admin2@customer-support.com"
        admin.role = ADMIN
        admin.is_active = True

        password = getpass("Enter new admin password: ")

        if len(password) < 8:
            print("Password must contain at least 8 characters.")
            return

        admin.password_hash = hash_password(password)

        db.commit()
        db.refresh(admin)

        print()
        print("Admin account reset successfully!")
        print(f"ID: {admin.id}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")
        print(f"Active: {admin.is_active}")

    except Exception as e:
        db.rollback()
        print(f"Failed to reset admin: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    reset_admin()