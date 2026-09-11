import os

# 1. Configura SQLite em memória antes de qualquer importação do projeto
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TMDB_API_KEY"] = "fake-tmdb-key-para-testes"

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# 2. Mock da inicialização da Base para evitar tentativa de conexão externa
with patch("database.engine"), patch("database.Base.metadata.create_all"):
    from main import app

client = TestClient(app)

def test_index_retorna_200():
    """Valida se a página inicial SPA está respondendo com sucesso (Requisito 1)."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Catálogo Tom Hanks" in response.text

def test_docs_openapi_ativo():
    """Valida se o contrato OpenAPI/Swagger está operacional."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    dados = response.json()
    assert "Catálogo Tom Hanks" in dados["info"]["title"]

def test_login_sem_credenciais_rejeitado():
    """Valida se a rota de login rejeita payload inválido."""
    response = client.post("/api/auth/login", json={})
    assert response.status_code in [400, 401, 422]