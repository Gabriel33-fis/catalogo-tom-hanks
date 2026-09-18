from pydantic import BaseModel
from typing import Optional, List

class FavoritoCriar(BaseModel):
    tmdb_movie_id: int
    titulo: str
    poster_path: Optional[str] = None

class ComentarioCriar(BaseModel):
    tmdb_movie_id: int
    texto: str

class PerfilUpdate(BaseModel):
    bio: Optional[str] = ""

class PerfilResponse(BaseModel):
    usuario_id: int
    nome: Optional[str] = None
    bio: str
    foto_url: Optional[str] = None
    favoritos: List[dict] = []