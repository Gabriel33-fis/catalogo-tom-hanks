import os
import io
from minio import Minio
from datetime import timedelta
from fastapi import HTTPException, UploadFile

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "miniopassword123")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "perfil-fotos")

# Inicializa o cliente MinIO
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def assegurar_bucket():
    """Garante que o bucket dedicado do projeto existe no MinIO."""
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
            minio_client.make_bucket(MINIO_BUCKET_NAME)
    except Exception as e:
        print(f"Aviso MinIO ao criar/verificar bucket: {e}")

def validar_e_enviar_foto(usuario_id: int, file: UploadFile) -> str:
    """
    Valida tipo MIME, extensão e tamanho do ficheiro (limite de 2MB).
    Envia para o MinIO e devolve a chave do objeto[cite: 13, 14].
    """
    extensoes_permitidas = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp"
    }

    if file.content_type not in extensoes_permitidas:
        raise HTTPException(
            status_code=400,
            detail="Tipo de ficheiro inválido. Apenas imagens JPEG, PNG ou WEBP são permitidas."
        )

    conteudo = file.file.read()
    tamanho_bytes = len(conteudo)
    max_tamanho = 2 * 1024 * 1024  # 2 MB

    if tamanho_bytes > max_tamanho:
        raise HTTPException(
            status_code=400,
            detail="Ficheiro excede o tamanho máximo permitido de 2 MB."
        )

    ext = extensoes_permitidas[file.content_type]
    object_name = f"perfil_{usuario_id}.{ext}"

    # Envia o ficheiro binário para o MinIO
    minio_client.put_object(
        bucket_name=MINIO_BUCKET_NAME,
        object_name=object_name,
        data=io.BytesIO(conteudo),
        length=tamanho_bytes,
        content_type=file.content_type
    )

    return object_name

def obter_url_foto(object_name: str) -> str:
    """
    Devolve a rota relativa da API para exibição segura da imagem.
    """
    if not object_name:
        return ""
    return f"/api/perfil/foto/{object_name}"

def obter_stream_imagem(object_name: str):
    """Recupera o stream binário direto do MinIO."""
    try:
        return minio_client.get_object(MINIO_BUCKET_NAME, object_name)
    except Exception:
        raise HTTPException(status_code=404, detail="Imagem não encontrada no storage.")