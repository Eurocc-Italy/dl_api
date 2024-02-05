from typing import List

"""
controller generated to handled auth operation described at:
https://connexion.readthedocs.io/en/latest/security.html
"""
import time
from pathlib import Path

import connexion
from jose import JWTError, jwt
from werkzeug.exceptions import Unauthorized

import os
from decouple import Config, RepositoryEnv

DOTENV_FILE = f"{os.getenv('HOME')}/.env"
env_config = Config(RepositoryEnv(DOTENV_FILE))

# Constants for JWT token generation and verification
JWT_ISSUER = env_config.get("JWT_ISSUER")
JWT_SECRET = env_config.get("JWT_SECRET")
JWT_LIFETIME_SECONDS = env_config.get("JWT_LIFETIME_SECONDS")
JWT_ALGORITHM = env_config.get("JWT_ALGORITHM")


def decode_token(token):
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        # Here you can add additional token validation if needed
        return decoded_token
    except JWTError as e:
        # Optionally, log the error details for debugging
        print(f"JWT Decode Error: {e}")
        raise Unauthorized from e


def generate_token(user_id):
    timestamp = _current_timestamp()
    payload = {
        "iss": JWT_ISSUER,
        "iat": int(timestamp),
        "exp": int(timestamp + JWT_LIFETIME_SECONDS),
        "sub": str(user_id),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_secret(user, token_info) -> str:
    return f"""
    You are user_id {user} and the secret is 'wbevuec'.
    Decoded token claims: {token_info}.
    """


def _current_timestamp() -> int:
    return int(time.time())
