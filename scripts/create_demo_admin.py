"""Create or reset a secondary administrator for a temporary client demo."""

import asyncio
import json
import secrets

from app.core.security import hash_password
from app.db.sqlite import SqliteSession
from app.repositories.user import UserRepository


DEMO_EMAIL = "demo.client@mielmar.ma"


async def main() -> None:
    password = "Demo-" + secrets.token_urlsafe(12)
    async with SqliteSession() as session:
        repository = UserRepository(session)
        user = await repository.get_by_email(DEMO_EMAIL)
        if user is None:
            user = await repository.create(
                email=DEMO_EMAIL,
                hashed_password=hash_password(password),
                full_name="Client Demo",
                role="admin",
                is_super_admin=False,
            )
        else:
            if user.is_super_admin:
                raise RuntimeError("The demo account cannot be the primary administrator")
            user.full_name = "Client Demo"
            user.role = "admin"
            user.is_super_admin = False
            user.is_active = True
            user.is_deleted = False
            user.hashed_password = hash_password(password)
            user.token_version += 1
            await session.commit()
            await session.refresh(user)
        print(
            json.dumps(
                {
                    "email": user.email,
                    "password": password,
                    "role": user.role,
                    "is_super_admin": user.is_super_admin,
                }
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
