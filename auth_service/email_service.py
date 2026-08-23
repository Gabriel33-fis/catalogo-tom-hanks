import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MAILTRAP_HOST = os.getenv("MAILTRAP_HOST", "sandbox.smtp.mailtrap.io")
MAILTRAP_PORT = int(os.getenv("MAILTRAP_PORT", 2525))
MAILTRAP_USER = os.getenv("MAILTRAP_USER", "")
MAILTRAP_PASS = os.getenv("MAILTRAP_PASS", "")

def enviar_email_recuperacao(destinatario: str, link_recuperacao: str, token: str):
    remetente = "nao-responda@tomhanks-catalogo.com"
    assunto = "Recuperação de Senha - Catálogo Tom Hanks"
    
    corpo = f"""
Olá!
Você solicitou a recuperação da sua senha.
Acesse o link abaixo para criar uma nova senha (válido por 30 minutos):
{link_recuperacao}

Se você não solicitou, ignore esta mensagem.
"""

    mensagem = MIMEMultipart()
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    mensagem["Subject"] = assunto
    mensagem.attach(MIMEText(corpo, "plain", "utf-8"))

    with smtplib.SMTP(MAILTRAP_HOST, MAILTRAP_PORT) as server:
        server.starttls()
        server.login(MAILTRAP_USER, MAILTRAP_PASS)
        server.sendmail(remetente, destinatario, mensagem.as_string())