import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from database import get_db, engine, Base
import models
import schemas
import auth
import email_service

# Cria as tabelas de autenticação no MySQL
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(usuario_in: schemas.UsuarioCriar, db: Session = Depends(get_db)):
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
    return {"message": "Usuário cadastrado com sucesso", "usuario_id": novo_usuario.id}

@app.post("/login")
def login(dados: schemas.LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == dados.email).first()
    if not usuario or not auth.verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    
    token = auth.criar_access_token(
        usuario_id=usuario.id,
        papel=usuario.papel,
        nome=usuario.nome
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario_nome": usuario.nome,
        "papel": usuario.papel
    }

@app.post("/forgot-password")
def forgot_password(dados: schemas.EsqueciSenhaRequest, db: Session = Depends(get_db)):
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
    return {"message": "E-mail de recuperação enviado com sucesso."}

@app.post("/reset-password")
def reset_password(dados: schemas.RedefinirSenhaRequest, db: Session = Depends(get_db)):
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

    return {"message": "Senha redefinida com sucesso!"}