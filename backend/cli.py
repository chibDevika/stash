"""
Bootstrap CLI — create the first admin user and optionally claim existing data.

Usage (Railway shell or local):
  python cli.py create-user --username admin --password secret --admin --claim-existing

Options:
  --username         Username for the new account
  --password         Password for the new account
  --admin            Grant admin privileges
  --claim-existing   Reassign all items/categories with user_id=NULL to this user
                     (preserves existing data when migrating from single-user setup)
"""

import asyncio
import argparse
import sys

from sqlalchemy import text

from database import AsyncSessionLocal
from services import db as db_service
from services.auth import hash_password


async def main(username: str, password: str, is_admin: bool, claim_existing: bool):
    async with AsyncSessionLocal() as db:
        existing = await db_service.get_user_by_username(db, username)
        if existing:
            print(f"Error: user '{username}' already exists.", file=sys.stderr)
            sys.exit(1)

        user = await db_service.create_user(
            db, username, hash_password(password), is_admin
        )

        if claim_existing:
            # Reassign all NULL user_id rows to this admin (existing data before multi-user)
            r_items = await db.execute(
                text("UPDATE items SET user_id = CAST(:uid AS uuid) WHERE user_id IS NULL"),
                {"uid": user["id"]},
            )
            r_cats = await db.execute(
                text(
                    "UPDATE categories SET user_id = CAST(:uid AS uuid) WHERE user_id IS NULL"
                ),
                {"uid": user["id"]},
            )
            await db.commit()
            print(
                f"Claimed {r_items.rowcount} items and {r_cats.rowcount} categories "
                f"for user '{username}'."
            )
        else:
            await db_service.seed_default_categories(db, user["id"])

        role = "admin" if is_admin else "user"
        print(f"Created {role}: {username}  (id: {user['id']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stash bootstrap CLI")
    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_parser.add_argument("--username", required=True)
    create_parser.add_argument("--password", required=True)
    create_parser.add_argument("--admin", action="store_true", default=False)
    create_parser.add_argument(
        "--claim-existing",
        action="store_true",
        default=False,
        help="Reassign NULL user_id rows to this user",
    )

    args = parser.parse_args()

    if args.command == "create-user":
        asyncio.run(
            main(
                username=args.username,
                password=args.password,
                is_admin=args.admin,
                claim_existing=args.claim_existing,
            )
        )
    else:
        parser.print_help()
        sys.exit(1)
