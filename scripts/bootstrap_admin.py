"""Premier administrateur local: aucune valeur secrète dans les arguments ou logs."""
import asyncio
from getpass import getpass
from sqlalchemy import select, func
from app.core.security import hash_password
from app.db.sqlite import SqliteSession
from app.models.user import User
from email_validator import validate_email

async def main():
    async with SqliteSession() as session:
        if await session.scalar(select(func.count()).select_from(User).where(User.role == 'admin')):
            raise SystemExit('Un administrateur existe deja. Utilisez la gestion des comptes.')
        email = validate_email(input('Adresse email administrateur : ').strip(), check_deliverability=False).normalized
        password = getpass('Nouveau mot de passe (16 caracteres minimum) : ')
        if len(password) < 16 or password != getpass('Confirmer le mot de passe : '):
            raise SystemExit('Mot de passe trop court ou confirmation differente.')
        session.add(User(email=email, full_name='Administration', hashed_password=hash_password(password), role='admin', is_active=True, is_email_verified=True))
        await session.commit()
        print('Administrateur cree. Connectez-vous sur http://localhost:5180/login')

if __name__ == '__main__':
    asyncio.run(main())
