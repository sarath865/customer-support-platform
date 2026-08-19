from getpass import getpass

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models import User


CUSTOMER = "customer"


def create_customer():
    db: Session = SessionLocal()

    try:
        email = input("Customer email: ").strip()
        full_name = input("Customer full name: ").strip()
        password = getpass("Customer password: ")

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

        customer = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=CUSTOMER,
            is_active=True,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        print()
        print("Customer user created successfully!")
        print(f"ID: {customer.id}")
        print(f"Email: {customer.email}")
        print(f"Role: {customer.role}")

    except Exception as e:
        db.rollback()
        print(f"Failed to create customer: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    create_customer()