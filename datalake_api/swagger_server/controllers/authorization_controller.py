from typing import List
import argparse

"""
controller generated to handled auth operation described at:
https://connexion.readthedocs.io/en/latest/security.html
"""
import time
from pathlib import Path
import uuid

import connexion
from jose import JWTError, jwt
from werkzeug.exceptions import Unauthorized

import os
from decouple import Config, RepositoryEnv

DOTENV_FILE = f"{os.getenv('HOME')}/.env"
env_config = Config(RepositoryEnv(DOTENV_FILE))

# Constants for JWT token generation and verification
JWT_ISSUER = env_config.get("JWT_ISSUER")
JWT_SECRET = env_config.get("JWT_SECRET").split()[0]
JWT_LIFETIME_SECONDS = int(env_config.get("JWT_LIFETIME_SECONDS"))
JWT_ALGORITHM = env_config.get("JWT_ALGORITHM")
MAC_HEX = uuid.getnode()


def decode_token(token):
    try:
        secret = int(JWT_SECRET, 16)
    except ValueError:
        raise ValueError("JWT_SECRET key must be a hexadecimal number.")

    try:
        decoded_token = jwt.decode(token, hex(secret * MAC_HEX), algorithms=[JWT_ALGORITHM])
        return decoded_token
    except JWTError as e:
        print(f"JWT Decode Error: {e}")
        raise Unauthorized from e


def generate_token(user_id, duration=JWT_LIFETIME_SECONDS):
    try:
        secret = int(JWT_SECRET, 16)
    except ValueError:
        raise ValueError("JWT_SECRET key must be a hexadecimal number.")

    timestamp = _current_timestamp()
    payload = {
        "iss": JWT_ISSUER,
        "iat": int(timestamp),
        "exp": int(timestamp + duration),
        "sub": str(user_id),
    }

    return jwt.encode(payload, hex(secret * MAC_HEX), algorithm=JWT_ALGORITHM)


def generate_token_cli():
    parser = argparse.ArgumentParser(description="Authentication token generation for Cineca's Data Lake as a Service.")

    parser.add_argument(
        "--user",
        help="Name of the user associated with the token",
        required=True,
    )

    parser.add_argument(
        "--duration",
        help="duration of the authentication token, in seconds",
        default=JWT_LIFETIME_SECONDS,
        required=False,
    )

    args = parser.parse_args()
    token = generate_token(user_id=args.user, duration=int(args.duration))

    print("\nGenerating authentication token. Please save the token and provide it to the intended user.")
    print("Default location for automatic token retrieval: ~/.config/dlaas/api-token.txt\n")

    print(f"  User: {args.user}")
    print(f"  Duration: {args.duration} seconds")
    print(f"  Token: {token}\n")


def get_secret(user, token_info) -> str:
    return f"""
    You are user_id {user}.
    Decoded token claims: {token_info}.
    The JWT secret is: {JWT_SECRET}.
    """


def _current_timestamp() -> int:
    return int(time.time())
