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

# Constants for JWT token generation and verification
JWT_ISSUER = "cineca_or_ifab"
JWT_SECRET = "samurai"  # Make sure to use a secure, unique secret in production
JWT_LIFETIME_SECONDS = 600
JWT_ALGORITHM = "HS256"

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

