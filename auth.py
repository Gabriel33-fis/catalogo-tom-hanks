import os
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario

# Configuração do algoritmo de hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Chave secreta para assinar o JWT (pode colocar no .env se preferir)
SECRET_KEY = os.getenv("JWT_SECRET", "super_chave_secreta_tom_hanks_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # Token válido por 24h

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def gerar_hash_senha(senha: str) -> str:
    """Criptografa a senha antes de salvar no banco."""
    return pwd_context.hash(senha)

def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    """Compara a senha enviada no login com o hash gravado."""
    return pwd_context.verify(senha_pura, senha_hash)

def criar_token_acesso(dados: dict) -> str:
    """Gera o token JWT assinado contendo os dados do usuário."""
    dados_para_codificar = dados.copy()
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_para_codificar.update({"exp": expiracao})
    return jwt.encode(dados_para_codificar, SECRET_KEY, algorithm=ALGORITHM)

def obter_usuario_logado(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    """Extrai o usuário atual a partir do token enviado no cabeçalho."""
    excecao_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id: str = payload.get("sub")
        if usuario_id is None:
            raise excecao_credenciais
    except JWTError:
        raise excecao_credenciais

    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if usuario is None:
        raise excecao_credenciais
    return usuario