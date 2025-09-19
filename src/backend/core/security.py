from datetime import datetime, timedelta, timezone
from typing import Optional
import warnings

# Correção para problema de compatibilidade bcrypt/passlib
try:
    import bcrypt
    if not hasattr(bcrypt, '__about__'):
        # Monkey patch para versões mais novas do bcrypt
        class AboutCompat:
            __version__ = getattr(bcrypt, '__version__', '4.1.3')
        bcrypt.__about__ = AboutCompat()
except ImportError:
    pass

from jose import jwt, JWTError
from passlib.context import CryptContext

from .config import settings

# Suprimir warnings do bcrypt/passlib
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | int, expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
