from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base

class Favorito(Base):
    __tablename__ = "favoritos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    tmdb_movie_id = Column(Integer, nullable=False)
    titulo = Column(String(255), nullable=False)
    poster_path = Column(String(255), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class Comentario(Base):
    __tablename__ = "comentarios"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False)
    tmdb_movie_id = Column(Integer, nullable=False)
    texto = Column(Text, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())