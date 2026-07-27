"""
Secure Administrator Creation CLI Script.

Run this script to initialize the first admin account or create additional admins.
Usage:
    python create_admin.py --name "Admin Name" --email "admin@srsense.ai" --password "SecurePass123!"
or run interactively:
    python create_admin.py
"""

import argparse
import asyncio
import getpass
import sys
import re

from sqlalchemy import select

from app.core.security import hash_password
from app.database.session import async_session_factory
from app.models.user import User, UserRole


def validate_email(email: str) -> bool:
    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True


async def create_admin(name: str, email: str, password: str) -> None:
    async with async_session_factory() as session:
        # Check if email exists
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"❌ Error: A user with email '{email}' already exists.")
            sys.exit(1)

        admin_user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )

        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)

        print("=" * 60)
        print("✅ Administrator account created successfully!")
        print(f"   ID:       {admin_user.id}")
        print(f"   Name:     {admin_user.name}")
        print(f"   Email:    {admin_user.email}")
        print(f"   Role:     {admin_user.role.value}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Securely create an administrator account for SRSense AI."
    )
    parser.add_argument("--name", help="Admin full name")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument("--password", help="Admin password")

    args = parser.parse_args()

    name = args.name
    email = args.email
    password = args.password

    print("🔐 SRSense AI — Administrator Creation CLI\n")

    if not name:
        name = input("Enter Admin Full Name: ").strip()
        while not name:
            print("Name cannot be empty.")
            name = input("Enter Admin Full Name: ").strip()

    if not email:
        email = input("Enter Admin Email: ").strip()
        while not validate_email(email):
            print("Invalid email format.")
            email = input("Enter Admin Email: ").strip()
    elif not validate_email(email):
        print("❌ Error: Invalid email format provided in arguments.")
        sys.exit(1)

    if not password:
        password = getpass.getpass("Enter Admin Password (min 8 chars, 1 uppercase, 1 lowercase, 1 digit): ")
        while not validate_password(password):
            print("❌ Password must be >=8 chars and contain uppercase, lowercase, and a digit.")
            password = getpass.getpass("Enter Admin Password: ")
    elif not validate_password(password):
        print("❌ Error: Provided password does not meet security requirements.")
        sys.exit(1)

    asyncio.run(create_admin(name, email, password))


if __name__ == "__main__":
    main()
