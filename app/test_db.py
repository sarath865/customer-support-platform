from sqlalchemy import text

from app.database import engine


try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.fetchone()

        print("Database connection successful!")
        print(version[0])

except Exception as e:
    print("Database connection failed!")
    print(e)