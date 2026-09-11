from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_index_retorna_200():
    """Valida se a página inicial SPA está respondendo com sucesso."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Catálogo Tom Hanks" in response.text

def test_docs_openapi_ativo():
    """Valida se o contrato OpenAPI/Swagger está operacional."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    dados = response.json()
    assert dados["info"]["title"] == "Catálogo Tom Hanks & Microsserviços"

def test_login_sem_credenciais_rejeitado():
    """Valida se a rota de login bloqueia requisição inválida com erro 422 ou 401."""
    response = client.post("/api/auth/login", json={})
    assert response.status_code in [400, 401, 422]