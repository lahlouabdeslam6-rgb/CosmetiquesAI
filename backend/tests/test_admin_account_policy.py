import pytest
from fastapi import HTTPException, status

from app.api.admin import _guard_managed_account, _require_primary_admin
from app.models.user import User


def make_admin(*, user_id: int, primary: bool) -> User:
    return User(
        id=user_id,
        email=f"admin{user_id}@mielmar.test",
        full_name=f"Admin {user_id}",
        hashed_password="hash",
        role="admin",
        is_super_admin=primary,
        is_active=True,
    )


def test_primary_admin_can_manage_secondary_admin() -> None:
    _guard_managed_account(
        make_admin(user_id=1, primary=True),
        make_admin(user_id=2, primary=False),
    )


def test_secondary_admin_cannot_manage_another_admin() -> None:
    with pytest.raises(HTTPException) as raised:
        _guard_managed_account(
            make_admin(user_id=2, primary=False),
            make_admin(user_id=3, primary=False),
        )
    assert raised.value.status_code == status.HTTP_403_FORBIDDEN


def test_primary_admin_account_is_always_protected() -> None:
    with pytest.raises(HTTPException) as raised:
        _guard_managed_account(
            make_admin(user_id=2, primary=False),
            make_admin(user_id=1, primary=True),
        )
    assert raised.value.status_code == status.HTTP_409_CONFLICT


def test_only_primary_admin_can_create_administrators() -> None:
    with pytest.raises(HTTPException) as raised:
        _require_primary_admin(make_admin(user_id=2, primary=False))
    assert raised.value.status_code == status.HTTP_403_FORBIDDEN

