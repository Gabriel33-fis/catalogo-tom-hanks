import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from database import get_db, engine, Base
import models
import schemas
import auth
import email_service
import requests

LOG_SERVICE_URL = os.getenv("LOG_SERVICE_URL", "http://log_service:6000")

def extrair_ip(request: Request) -> str:
    """Extrai o IP real considerando proxies reversos ou cliente direto."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"

def registrar_log(usuario_id, acao, ip=None, detalhes=None):
    try:
        requests.post(
            f"{LOG_SERVICE_URL}/logs",
            json={
                "usuario_id": usuario_id,
                "acao": acao,
                "ip_origem": ip,
                "detalhes": detalhes
            },
            timeout=1.0
        )
    except Exception as e:
        print(f"Aviso log_service: {e}")

# Cria as tabelas de autenticação no MySQL
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(usuario_in: schemas.UsuarioCriar, request: Request, db: Session = Depends(get_db)):
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == usuario_in.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado"
        )
    
    senha_hash = auth.gerar_hash_senha(usuario_in.senha)
    novo_usuario = models.Usuario(
        nome=usuario_in.nome,
        email=usuario_in.email,
        senha_hash=senha_hash,
        papel=usuario_in.papel or "usuario"
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    # Log de novo cadastro
    ip = extrair_ip(request)
    registrar_log(
        usuario_id=novo_usuario.id,
        acao="registro",
        ip=ip,
        detalhes=f"Novo usuário cadastrado com papel '{novo_usuario.papel}'"
    )

    return {"message": "Usuário cadastrado com sucesso", "usuario_id": novo_usuario.id}

@app.post("/login")
def login(dados: schemas.LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = extrair_ip(request)
    usuario = db.query(models.Usuario).filter(models.Usuario.email == dados.email).first()
    
    if not usuario or not auth.verificar_senha(dados.senha, usuario.senha_hash):
        registrar_log(
            usuario_id=usuario.id if usuario else None,
            acao="falha_login",
            ip=ip,
            detalhes=f"Tentativa de login frustrada para o e-mail: {dados.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    
    token = auth.criar_access_token(
        usuario_id=usuario.id,
        email=usuario.email,
        papel=usuario.papel,
        nome=usuario.nome
    )

    # Requisito 2: Log de login com sucesso
    registrar_log(
        usuario_id=usuario.id,
        acao="login",
        ip=ip,
        detalhes=f"Login realizado pelo usuário '{usuario.nome}' [{usuario.papel}]"
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario_nome": usuario.nome,
        "papel": usuario.papel
    }

@app.post("/forgot-password")
def forgot_password(dados: schemas.EsqueciSenhaRequest, request: Request, db: Session = Depends(get_db)):
    ip = extrair_ip(request)
    usuario = db.query(models.Usuario).filter(models.Usuario.email == dados.email).first()
    if not usuario:
        return {"message": "Se o e-mail existir, as instruções foram enviadas."}

    token_reset = auth.gerar_token_recuperacao()
    expiracao = datetime.utcnow() + timedelta(minutes=15)

    reset_entry = models.RecuperacaoSenha(
        usuario_id=usuario.id,
        token=token_reset,
        expira_em=expiracao
    )
    db.add(reset_entry)
    db.commit()

    email_service.enviar_email_recuperacao(usuario.email, token_reset)

    registrar_log(
        usuario_id=usuario.id,
        acao="solicitacao_recuperacao_senha",
        ip=ip,
        detalhes=f"Token de recuperação enviado para {usuario.email}"
    )

    return {"message": "E-mail de recuperação enviado com sucesso."}

@app.post("/reset-password")
def reset_password(dados: schemas.RedefinirSenhaRequest, request: Request, db: Session = Depends(get_db)):
    ip = extrair_ip(request)
    reset_entry = db.query(models.RecuperacaoSenha).filter(
        models.RecuperacaoSenha.token == dados.token,
        models.RecuperacaoSenha.usado == False
    ).first()

    if not reset_entry or reset_entry.expira_em < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )

    usuario = db.query(models.Usuario).filter(models.Usuario.id == reset_entry.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    usuario.senha_hash = auth.gerar_hash_senha(dados.nova_senha)
    reset_entry.usado = True
    db.commit()

    registrar_log(
        usuario_id=usuario.id,
        acao="redefinicao_senha",
        ip=ip,
        detalhes="Senha redefinida com sucesso com token de recuperação"
    )

    return {"message": "Senha redefinida com sucesso!"}