import os
import bcrypt
import jwt
from datetime import datetime, timedelta
import secrets

JWT_SECRET = os.getenv("JWT_SECRET", "default_secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def gerar_hash_senha(senha: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha: str, hash_senha: str) -> bool:
    return bcrypt.checkpw(senha.encode('utf-8'), hash_senha.encode('utf-8'))

def gerar_token_recuperacao() -> str:
    """Gera um token seguro e aleatório para recuperação de senha."""
    return secrets.token_urlsafe(32)

def criar_access_token(usuario_id: int, nome: str, email: str, papel: str) -> str:
    expiracao = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "usuario_id": usuario_id,
        "nome": nome,
        "email": email,
        "papel": papel,
        "exp": expiracao
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None