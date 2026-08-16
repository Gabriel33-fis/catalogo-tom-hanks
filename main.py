import os
import requests
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db
import models
import schemas
from auth import (
    gerar_hash_senha,
    verificar_senha,
    criar_token_acesso,
    obter_usuario_logado
)

load_dotenv()

app = FastAPI(title="Catálogo Tom Hanks - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"


# Rota para abrir o index.html direto no navegador
@app.get("/")
def home():
    return FileResponse("index.html")


# ==========================================
# 1. ROTAS DE AUTENTICAÇÃO (CADASTRO E LOGIN)
# ==========================================

@app.post("/api/cadastro", response_model=schemas.UsuarioResposta, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(usuario: schemas.UsuarioCriar, db: Session = Depends(get_db)):
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail já está cadastrado."
        )

    novo_usuario = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=gerar_hash_senha(usuario.senha)
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


@app.post("/api/login", response_model=schemas.TokenResposta)
def login(dados_login: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == dados_login.email).first()
    
    if not usuario or not verificar_senha(dados_login.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos."
        )

    token = criar_token_acesso(dados={"sub": str(usuario.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario_nome": usuario.nome
    }


# ==========================================
# 2. CONSUMO DA API DO TMDB (CATÁLOGO DINÂMICO)
# ==========================================

@app.get("/api/filmes")
def listar_filmes_tom_hanks():
    resp_person = requests.get(
        f"{TMDB_BASE_URL}/search/person",
        params={"api_key": TMDB_API_KEY, "query": "Tom Hanks", "language": "pt-BR"}
    )
    dados_person = resp_person.json()
    if not dados_person.get("results"):
        raise HTTPException(status_code=502, detail="Ator não encontrado no TMDB.")

    person_id = dados_person["results"][0]["id"]

    resp_credits = requests.get(
        f"{TMDB_BASE_URL}/person/{person_id}/movie_credits",
        params={"api_key": TMDB_API_KEY, "language": "pt-BR"}
    )
    dados_credits = resp_credits.json()
    filmes_brutos = dados_credits.get("cast", [])

    catalogo = []
    for filme in filmes_brutos:
        poster_path = filme.get("poster_path")
        catalogo.append({
            "tmdb_movie_id": filme.get("id"),
            "titulo": filme.get("title"),
            "sinopse": filme.get("overview") or "Sem sinopse disponível.",
            "data_lancamento": filme.get("release_date"),
            "poster_url": f"{IMG_BASE_URL}{poster_path}" if poster_path else None
        })

    return catalogo


# ==========================================
# 3. PERSISTÊNCIA: FAVORITOS (COM ISOLAMENTO)
# ==========================================

@app.get("/api/favoritos")
def listar_favoritos(
    usuario_atual: models.Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    return db.query(models.Favorito).filter(models.Favorito.usuario_id == usuario_atual.id).all()


@app.post("/api/favoritos", status_code=status.HTTP_201_CREATED)
def adicionar_favorito(
    item: schemas.FavoritoCriar,
    usuario_atual: models.Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    ja_favorito = db.query(models.Favorito).filter(
        models.Favorito.usuario_id == usuario_atual.id,
        models.Favorito.tmdb_movie_id == item.tmdb_movie_id
    ).first()

    if ja_favorito:
        raise HTTPException(status_code=400, detail="Filme já está nos favoritos.")

    novo_favorito = models.Favorito(
        usuario_id=usuario_atual.id,
        tmdb_movie_id=item.tmdb_movie_id,
        titulo=item.titulo,
        poster_path=item.poster_path
    )
    db.add(novo_favorito)
    db.commit()
    return {"mensagem": "Filme adicionado aos favoritos com sucesso!"}


@app.delete("/api/favoritos/{tmdb_movie_id}")
def remover_favorito(
    tmdb_movie_id: int,
    usuario_atual: models.Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    favorito = db.query(models.Favorito).filter(
        models.Favorito.usuario_id == usuario_atual.id,
        models.Favorito.tmdb_movie_id == tmdb_movie_id
    ).first()

    if not favorito:
        raise HTTPException(status_code=404, detail="Favorito não encontrado.")

    db.delete(favorito)
    db.commit()
    return {"mensagem": "Favorito removido com sucesso."}


# ==========================================
# 4. PERSISTÊNCIA: COMENTÁRIOS (COM ISOLAMENTO)
# ==========================================

@app.get("/api/comentarios/{tmdb_movie_id}")
def listar_comentarios_do_filme(
    tmdb_movie_id: int,
    usuario_atual: models.Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    return db.query(models.Comentario).filter(
        models.Comentario.usuario_id == usuario_atual.id,
        models.Comentario.tmdb_movie_id == tmdb_movie_id
    ).all()


@app.post("/api/comentarios", status_code=status.HTTP_201_CREATED)
def adicionar_comentario(
    item: schemas.ComentarioCriar,
    usuario_atual: models.Usuario = Depends(obter_usuario_logado),
    db: Session = Depends(get_db)
):
    novo_comentario = models.Comentario(
        usuario_id=usuario_atual.id,
        tmdb_movie_id=item.tmdb_movie_id,
        texto=item.texto
    )
    db.add(novo_comentario)
    db.commit()
    return {"mensagem": "Comentário salvo com sucesso!"}