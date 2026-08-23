from pydantic import BaseModel
from typing import Optional

class FavoritoCriar(BaseModel):
    tmdb_movie_id: int
    titulo: str
    poster_path: Optional[str] = None

class ComentarioCriar(BaseModel):
    tmdb_movie_id: int
    texto: str