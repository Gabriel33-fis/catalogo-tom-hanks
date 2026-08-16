from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Estrutura para Cadastro de Usuário
class UsuarioCriar(BaseModel):
    nome: str
    email: EmailStr
    senha: str

# Resposta após cadastro (sem devolver a senha)
class UsuarioResposta(BaseModel):
    id: int
    nome: str
    email: EmailStr
    criado_em: datetime

    class Config:
        from_attributes = True

# Estrutura para Login
class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str

# Resposta do Token
class TokenResposta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario_nome: str

# Estrutura para Favoritar um Filme
class FavoritoCriar(BaseModel):
    tmdb_movie_id: int
    titulo: str
    poster_path: Optional[str] = None

# Estrutura para Enviar um Comentário
class ComentarioCriar(BaseModel):
    tmdb_movie_id: int
    texto: str