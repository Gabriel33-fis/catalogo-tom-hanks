from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioCriar(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    papel: Optional[str] = "usuario"

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class EsqueciSenhaRequest(BaseModel):
    email: EmailStr

class RedefinirSenhaRequest(BaseModel):
    token: str
    nova_senha: str