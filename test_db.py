import os
import pymysql

DB_HOST = os.getenv("DB_HOST", "35.226.64.52")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "IAC_2026_02_gabriel_graciano")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "IAC_2026_02_gabriel_graciano")

conn = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

try:
    with conn.cursor() as cursor:
        print("1. Adicionando coluna 'papel' na tabela usuarios...")
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN papel VARCHAR(20) DEFAULT 'usuario' NOT NULL;")
            print(" -> Coluna 'papel' adicionada com sucesso!")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print(" -> Coluna 'papel' já existe.")
            else:
                raise e

        print("2. Criando tabela 'reset_tokens'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reset_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                token VARCHAR(64) NOT NULL UNIQUE,
                usuario_id INT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expira_em TIMESTAMP NOT NULL,
                usado BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            );
        """)
        print(" -> Tabela 'reset_tokens' criada com sucesso!")

    conn.commit()
    print("\nBanco de dados atualizado com sucesso!")
finally:
    conn.close()