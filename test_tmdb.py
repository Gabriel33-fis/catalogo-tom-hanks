import os
import requests
from dotenv import load_dotenv

# Carrega a chave do arquivo .env
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

def buscar_filmes_tom_hanks():
    if not API_KEY or API_KEY == "sua_chave_do_tmdb_aqui":
        print("❌ Por favor, adicione sua TMDB_API_KEY no arquivo .env!")
        return

    # 1. Pega o person_id de Tom Hanks
    url_person = f"{BASE_URL}/search/person"
    params_person = {
        "api_key": API_KEY,
        "query": "Tom Hanks",
        "language": "pt-BR"
    }
    
    resp_person = requests.get(url_person, params=params_person)
    dados_person = resp_person.json()
    
    if not dados_person.get("results"):
        print("Ator não encontrado.")
        return

    person_id = dados_person["results"][0]["id"]
    print(f"✅ ID do Tom Hanks encontrado: {person_id}")

    # 2. Pega a lista de filmes do ator
    url_credits = f"{BASE_URL}/person/{person_id}/movie_credits"
    params_credits = {
        "api_key": API_KEY,
        "language": "pt-BR"
    }
    
    resp_credits = requests.get(url_credits, params=params_credits)
    dados_credits = resp_credits.json()
    
    filmes = dados_credits.get("cast", [])
    print(f"🎬 Total de filmes encontrados: {len(filmes)}\n")

    # 3. Exibe os 5 primeiros filmes com poster montado
    for filme in filmes[:5]:
        tmdb_id = filme.get("id")
        titulo = filme.get("title")
        poster_path = filme.get("poster_path")
        poster_url = f"{IMG_BASE_URL}{poster_path}" if poster_path else "Sem pôster"
        
        print(f"ID: {tmdb_id} | Título: {titulo}")
        print(f"Pôster: {poster_url}")
        print("-" * 50)

if __name__ == "__main__":
    buscar_filmes_tom_hanks()