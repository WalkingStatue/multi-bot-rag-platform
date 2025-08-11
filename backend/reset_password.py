#!/usr/bin/env python3
"""
Script to reset a user's password
"""
import asyncio
import sys
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset_password(username: str, new_password: str):
    """Reset a user's password"""
    
    # Hash the new password
    password_hash = pwd_context.hash(new_password)
    
    # Create database connection
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Update the user's password
        result = conn.execute(
            text("UPDATE users SET password_hash = :password_hash WHERE username = :username"),
            {"password_hash": password_hash, "username": username}
        )
        conn.commit()
        
        if result.rowcount > 0:
            print(f"✅ Password reset successfully for user: {username}")
            print(f"🔑 New password: {new_password}")
        else:
            print(f"❌ User not found: {username}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <username> <new_password>")
        sys.exit(1)
    
    username = sys.argv[1]
    new_password = sys.argv[2]
    
    asyncio.run(reset_password(username, new_password))