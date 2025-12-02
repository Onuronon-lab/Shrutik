## Generate a JWT access token for manual API testing (HTTP Bearer) by user ID and email.

from __future__ import annotations

import argparse
import sys
from datetime import timedelta

from app.core.config import settings
from app.core.security import create_access_token
from app.db.database import SessionLocal
from app.models.user import User


def _find_user(db, user_id: int | None, email: str | None):
    q = db.query(User)
    if user_id is not None:
        return q.filter(User.id == user_id).first()
    if email is not None:
        return q.filter(User.email == email).first()
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate a JWT access token for an existing user (HTTP Bearer)."
    )
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--user-id", type=int)
    grp.add_argument("--email", type=str)
    parser.add_argument(
        "--minutes",
        type=int,
        default=None,
        help=f"Override expiry minutes (default: settings.ACCESS_TOKEN_EXPIRE_MINUTES={settings.ACCESS_TOKEN_EXPIRE_MINUTES})",
    )
    parser.add_argument("--raw", action="store_true")

    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = _find_user(db, args.user_id, args.email)
        if not user:
            target = (
                f"id={args.user_id}"
                if args.user_id is not None
                else f"email='{args.email}'"
            )
            print(f"User not found ({target})", file=sys.stderr)
            return 1

        token_data = {
            "sub": user.email,
            "user_id": user.id,
            "role": user.role.value,
        }

        expires = (
            timedelta(minutes=args.minutes)
            if args.minutes is not None
            else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        token = create_access_token(data=token_data, expires_delta=expires)

        if args.raw:
            print(token)
        else:
            print("JWT access token generated\n")
            print(
                f"User: {user.name} <{user.email}> (id={user.id}, role={user.role.value})"
            )
            print(
                f"Expires (minutes): {args.minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES}"
            )
            print("\nAuthorization header to use:")
            print(f"Bearer {token}\n")
            print("Example curl:")
            print(
                f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/api/auth/me"
            )

        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
