from database import SessionLocal
from models import Usuario

def testar():
    try:
        db = SessionLocal()
        # Faz uma consulta simples contando os usuários cadastrados
        total_usuarios = db.query(Usuario).count()
        print("\n✅ Conexão do Python com o MySQL realizada com sucesso!")
        print(f"👥 Usuários cadastrados no momento: {total_usuarios}\n")
        db.close()
    except Exception as erro:
        print("\n❌ Erro ao conectar com o banco:")
        print(erro)

if __name__ == "__main__":
    testar()