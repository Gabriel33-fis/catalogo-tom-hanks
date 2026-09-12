import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Header, Response, status
from pydantic import BaseModel
import redis
import jwt
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Log Service")

# Instrumentação Prometheus para expor métricas na rota /metrics (Requisito 3)
Instrumentator().instrument(app).expose(app)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
JWT_SECRET = os.getenv("JWT_SECRET", "sua_chave_secreta_jwt")

# Conexão com timeout curto para checagens de health check não travarem
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_connect_timeout=2)
STREAM_KEY = "audit_logs"

class LogEntry(BaseModel):
    usuario_id: Optional[int] = None
    acao: str
    ip_origem: Optional[str] = None
    detalhes: Optional[str] = None

@app.get("/health")
def health_check(response: Response):
    """
    Readiness probe real: testa dependência crítica (Redis).
    Retorna 200 se saudável, 503 se o Redis estiver inacessível (Requisito 1).
    """
    try:
        r.ping()
        return {
            "status": "healthy",
            "service": "log_service",
            "dependencies": {
                "redis": "up"
            }
        }
    except Exception as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "service": "log_service",
            "dependencies": {
                "redis": "down"
            },
            "error": str(exc)
        }

@app.post("/logs")
def registrar_log(entry: LogEntry):
    timestamp = datetime.now(timezone.utc).isoformat()
    log_data = {
        "usuario_id": str(entry.usuario_id) if entry.usuario_id is not None else "anonimo",
        "acao": entry.acao,
        "timestamp": timestamp,
        "ip_origem": entry.ip_origem or "desconhecido",
        "detalhes": entry.detalhes or ""
    }
    
    msg_id = r.xadd(STREAM_KEY, log_data)
    return {"status": "ok", "id": msg_id}

@app.get("/logs")
def consultar_logs(limit: int = 50, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente ou inválido")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if payload.get("papel") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")

    logs_raw = r.xrevrange(STREAM_KEY, max="+", min="-", count=limit)
    
    resultado = []
    for log_id, fields in logs_raw:
        fields["id"] = log_id
        resultado.append(fields)
        
    return {"total": len(resultado), "logs": resultado}