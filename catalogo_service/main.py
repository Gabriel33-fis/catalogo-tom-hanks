import os
import json
import urllib.request
import urllib.error
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import get_db, engine, Base
import models
import schemas
import auth_guard

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Catálogo Tom Hanks")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:5000")
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

def chamar_auth_service(endpoint: str, payload: dict):
    url = f"{AUTH_SERVICE_URL}{endpoint}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return response.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            detail = json.loads(err_body).get("detail", "Erro no serviço de autenticação")
        except Exception:
            detail = err_body or "Erro no serviço de autenticação"
        raise HTTPException(status_code=e.code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha de conexão com Auth Service: {str(e)}")

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎬 Catálogo Tom Hanks</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #141414; color: #fff; min-height: 100vh; display: flex; flex-direction: column; }
        nav { background: #000; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e50914; }
        .nav-brand { display: flex; align-items: center; gap: 20px; }
        nav h1 { color: #e50914; font-size: 1.5rem; }
        .nav-links { display: flex; gap: 15px; }
        .nav-link { color: #aaa; text-decoration: none; font-weight: bold; cursor: pointer; font-size: 0.95rem; }
        .nav-link:hover, .nav-link.active { color: #fff; border-bottom: 2px solid #e50914; }
        .user-panel { display: flex; align-items: center; gap: 15px; }
        .btn-logout { background: #333; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; }
        .btn-logout:hover { background: #e50914; }
        .main-container { padding: 30px 20px; max-width: 1200px; margin: 0 auto; width: 100%; flex: 1; }
        .auth-card { max-width: 400px; margin: 40px auto; background: #1f1f1f; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .auth-card h2 { margin-bottom: 20px; color: #fff; text-align: center; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; color: #aaa; font-size: 0.9rem; }
        .form-group input, .form-group textarea { width: 100%; padding: 12px; background: #333; border: 1px solid #444; border-radius: 4px; color: white; outline: none; }
        .form-group input:focus, .form-group textarea:focus { border-color: #e50914; }
        button.btn-primary { width: 100%; padding: 12px; background: #e50914; border: none; border-radius: 4px; color: white; font-weight: bold; cursor: pointer; font-size: 1rem; margin-top: 10px; }
        button.btn-primary:hover { background: #f40612; }
        .links-group { margin-top: 15px; display: flex; justify-content: space-between; font-size: 0.85rem; }
        .link-text { color: #aaa; text-decoration: none; cursor: pointer; }
        .link-text:hover { color: #fff; text-decoration: underline; }
        .hidden { display: none !important; }
        .msg { padding: 10px; border-radius: 4px; margin-top: 15px; font-size: 0.9rem; text-align: center; }
        .msg.success { background: rgba(46, 125, 50, 0.2); border: 1px solid #2e7d32; color: #4caf50; }
        .msg.error { background: rgba(198, 40, 40, 0.2); border: 1px solid #c62828; color: #ef5350; }
        .movies-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 25px; margin-top: 25px; }
        .movie-card { background: #1f1f1f; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
        .movie-card img { width: 100%; height: 320px; object-fit: cover; }
        .movie-info { padding: 15px; flex: 1; display: flex; flex-direction: column; }
        .movie-title { font-weight: bold; font-size: 1.05rem; margin-bottom: 6px; color: #fff; }
        .movie-release { color: #aaa; font-size: 0.85rem; margin-bottom: 12px; }
        .movie-overview { font-size: 0.8rem; color: #bbb; line-height: 1.4; max-height: 80px; overflow-y: auto; margin-bottom: 15px; flex: 1; }
        .movie-actions { display: flex; gap: 8px; margin-top: auto; }
        .btn-action { flex: 1; padding: 8px 0; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem; font-weight: bold; }
        .btn-fav { background: #ffb703; color: #000; }
        .btn-fav:hover { background: #fb8500; }
        .btn-fav-remove { background: #d90429; color: #fff; }
        .btn-fav-remove:hover { background: #ef233c; }
        .btn-com { background: #0284c7; color: #fff; }
        .btn-com:hover { background: #0369a1; }
        
        .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.75); display: flex; justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: #1f1f1f; padding: 25px; border-radius: 8px; width: 90%; max-width: 550px; max-height: 85vh; display: flex; flex-direction: column; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 10px; }
        .modal-close { background: none; border: none; color: #aaa; font-size: 1.5rem; cursor: pointer; }
        .comments-list { flex: 1; overflow-y: auto; margin-bottom: 15px; max-height: 250px; }
        .comment-item { background: #2a2a2a; padding: 10px; border-radius: 4px; margin-bottom: 10px; }
        .comment-user { font-size: 0.85rem; font-weight: bold; color: #e50914; margin-bottom: 4px; }
        .comment-text { font-size: 0.9rem; color: #ddd; }
    </style>
</head>
<body>
    <nav>
        <div class="nav-brand">
            <h1>🎬 Catálogo Tom Hanks</h1>
            <div id="nav-tabs" class="nav-links hidden">
                <a id="tab-cat" class="nav-link active" onclick="mostrarAba('catalogo')">Catálogo</a>
                <a id="tab-fav" class="nav-link" onclick="mostrarAba('favoritos')">Meus Favoritos</a>
            </div>
        </div>
        <div class="user-panel">
            <span id="nav-user-info">Não conectado</span>
            <button id="btn-logout" class="btn-logout hidden" onclick="logout()">Sair</button>
        </div>
    </nav>
    <div class="main-container">
        <!-- LOGIN -->
        <div id="box-login" class="auth-card">
            <h2>Login</h2>
            <div class="form-group">
                <label>E-mail:</label>
                <input type="email" id="login-email" placeholder="seu@email.com">
            </div>
            <div class="form-group">
                <label>Senha:</label>
                <input type="password" id="login-senha" placeholder="Sua senha">
            </div>
            <button class="btn-primary" onclick="fazerLogin()">Entrar</button>
            <div class="links-group">
                <a class="link-text" onclick="alternarTela('box-forgot')">Esqueci a senha</a>
                <a class="link-text" onclick="alternarTela('box-register')">Cadastre-se</a>
            </div>
            <div id="msg-login" class="msg hidden"></div>
        </div>

        <!-- CADASTRO -->
        <div id="box-register" class="auth-card hidden">
            <h2>Criar Conta</h2>
            <div class="form-group">
                <label>Nome:</label>
                <input type="text" id="reg-nome" placeholder="Seu nome">
            </div>
            <div class="form-group">
                <label>E-mail:</label>
                <input type="email" id="reg-email" placeholder="seu@email.com">
            </div>
            <div class="form-group">
                <label>Senha:</label>
                <input type="password" id="reg-senha" placeholder="Crie uma senha">
            </div>
            <button class="btn-primary" onclick="fazerCadastro()">Cadastrar</button>
            <div class="links-group" style="justify-content: center;">
                <a class="link-text" onclick="alternarTela('box-login')">Voltar ao Login</a>
            </div>
            <div id="msg-reg" class="msg hidden"></div>
        </div>

        <!-- ESQUECI A SENHA -->
        <div id="box-forgot" class="auth-card hidden">
            <h2>Recuperar Senha</h2>
            <p style="color: #aaa; font-size: 0.85rem; margin-bottom: 15px; text-align: center;">Informe o e-mail para receber as instruções.</p>
            <div class="form-group">
                <label>E-mail cadastrado:</label>
                <input type="email" id="forgot-email" placeholder="seu@email.com">
            </div>
            <button class="btn-primary" onclick="solicitarRecuperacao()">Enviar E-mail</button>
            <div class="links-group">
                <a class="link-text" onclick="alternarTela('box-reset')">Já tenho um token</a>
                <a class="link-text" onclick="alternarTela('box-login')">Voltar ao Login</a>
            </div>
            <div id="msg-forgot" class="msg hidden"></div>
        </div>

        <!-- REDEFINIR SENHA -->
        <div id="box-reset" class="auth-card hidden">
            <h2>Redefinir Senha</h2>
            <div class="form-group">
                <label>Token recebido:</label>
                <input type="text" id="reset-token" placeholder="Cole o token recebido">
            </div>
            <div class="form-group">
                <label>Nova Senha:</label>
                <input type="password" id="reset-nova-senha" placeholder="Digite a nova senha">
            </div>
            <button class="btn-primary" onclick="redefinirSenha()">Alterar Senha</button>
            <div class="links-group" style="justify-content: center;">
                <a class="link-text" onclick="alternarTela('box-login')">Voltar ao Login</a>
            </div>
            <div id="msg-reset" class="msg hidden"></div>
        </div>

        <!-- CATÁLOGO GERAL -->
        <div id="box-catalogo" class="hidden">
            <h2>Catálogo de Filmes com Tom Hanks</h2>
            <div id="movies-container" class="movies-grid"></div>
        </div>

        <!-- ABA MEUS FAVORITOS -->
        <div id="box-favoritos" class="hidden">
            <h2>Meus Filmes Favoritos ⭐</h2>
            <div id="fav-movies-container" class="movies-grid"></div>
        </div>
    </div>

    <!-- MODAL DE COMENTÁRIOS -->
    <div id="modal-comentarios" class="modal hidden">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modal-movie-title">Comentários</h3>
                <button class="modal-close" onclick="fecharModalComentarios()">&times;</button>
            </div>
            <div id="comments-list" class="comments-list">
                <p style="color:#aaa;">Carregando comentários...</p>
            </div>
            <div class="form-group">
                <textarea id="novo-comentario-texto" rows="3" placeholder="Escreva seu comentário sobre o filme..."></textarea>
            </div>
            <button class="btn-primary" onclick="enviarComentario()">Enviar Comentário</button>
        </div>
    </div>

    <script>
        let filmeAtualComentario = null;

        function alternarTela(id) {
            ['box-login', 'box-register', 'box-forgot', 'box-reset', 'box-catalogo', 'box-favoritos'].forEach(b => {
                const el = document.getElementById(b);
                if (el) el.classList.add('hidden');
            });
            document.getElementById(id).classList.remove('hidden');
        }

        function mostrarAba(aba) {
            if (aba === 'catalogo') {
                document.getElementById('tab-cat').classList.add('active');
                document.getElementById('tab-fav').classList.remove('active');
                alternarTela('box-catalogo');
                carregarFilmes();
            } else if (aba === 'favoritos') {
                document.getElementById('tab-fav').classList.add('active');
                document.getElementById('tab-cat').classList.remove('active');
                alternarTela('box-favoritos');
                carregarFavoritos();
            }
        }

        function exibirAviso(elemId, texto, ehErro) {
            const el = document.getElementById(elemId);
            el.className = 'msg ' + (ehErro ? 'error' : 'success');
            el.innerText = texto;
            el.classList.remove('hidden');
        }

        async function carregarFilmes() {
            const token = localStorage.getItem('token');
            const container = document.getElementById('movies-container');
            container.innerHTML = '<p style="color:#aaa;">Carregando filmes...</p>';
            try {
                const res = await fetch('/api/filmes', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('Falha ao obter catálogo');
                const filmes = await res.json();
                container.innerHTML = '';
                filmes.forEach(f => {
                    const card = document.createElement('div');
                    card.className = 'movie-card';
                    card.innerHTML = `
                        <img src="${f.poster_path ? 'https://image.tmdb.org/t/p/w500' + f.poster_path : 'https://via.placeholder.com/300x450?text=Sem+Poster'}" alt="${f.title}">
                        <div class="movie-info">
                            <div class="movie-title">${f.title}</div>
                            <div class="movie-release">📅 ${f.release_date || 'N/A'}</div>
                            <div class="movie-overview">${f.overview || 'Sem descrição disponível.'}</div>
                            <div class="movie-actions">
                                <button class="btn-action btn-fav" onclick="favoritar(${f.id}, '${f.title.replace(/'/g, "\\\\'")}', '${f.poster_path || ''}')">⭐ Favorito</button>
                                <button class="btn-action btn-com" onclick="abrirModalComentarios(${f.id}, '${f.title.replace(/'/g, "\\\\'")}')">💬 Comentar</button>
                            </div>
                        </div>
                    `;
                    container.appendChild(card);
                });
            } catch (err) {
                container.innerHTML = `<p style="color:#ef5350;">Erro ao carregar catálogo: ${err.message}</p>`;
            }
        }

        async function carregarFavoritos() {
            const token = localStorage.getItem('token');
            const container = document.getElementById('fav-movies-container');
            container.innerHTML = '<p style="color:#aaa;">Carregando favoritos...</p>';
            try {
                const res = await fetch('/api/favoritos', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('Falha ao carregar favoritos');
                const favoritos = await res.json();
                if (favoritos.length === 0) {
                    container.innerHTML = '<p style="color:#888;">Você ainda não favoritou nenhum filme.</p>';
                    return;
                }
                container.innerHTML = '';
                favoritos.forEach(f => {
                    const card = document.createElement('div');
                    card.className = 'movie-card';
                    card.innerHTML = `
                        <img src="${f.poster_path ? 'https://image.tmdb.org/t/p/w500' + f.poster_path : 'https://via.placeholder.com/300x450?text=Sem+Poster'}" alt="${f.titulo}">
                        <div class="movie-info">
                            <div class="movie-title">${f.titulo}</div>
                            <div class="movie-release">⭐ Salvo nos seus favoritos</div>
                            <div class="movie-actions">
                                <button class="btn-action btn-fav-remove" onclick="removerFavorito(${f.id})">❌ Remover</button>
                                <button class="btn-action btn-com" onclick="abrirModalComentarios(${f.tmdb_movie_id}, '${f.titulo.replace(/'/g, "\\\\'")}')">💬 Comentar</button>
                            </div>
                        </div>
                    `;
                    container.appendChild(card);
                });
            } catch (err) {
                container.innerHTML = `<p style="color:#ef5350;">Erro: ${err.message}</p>`;
            }
        }

        async function favoritar(id, titulo, poster) {
            const token = localStorage.getItem('token');
            try {
                const res = await fetch('/api/favoritos', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ tmdb_movie_id: id, titulo, poster_path: poster })
                });
                if (!res.ok) throw new Error('Não foi possível favoritar');
                alert(`"${titulo}" adicionado aos favoritos!`);
            } catch (e) {
                alert(e.message);
            }
        }

        async function removerFavorito(favoritoId) {
            const token = localStorage.getItem('token');
            try {
                const res = await fetch(`/api/favoritos/${favoritoId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('Não foi possível remover o favorito');
                carregarFavoritos();
            } catch (e) {
                alert(e.message);
            }
        }

        async function abrirModalComentarios(movieId, movieTitle) {
            filmeAtualComentario = parseInt(movieId, 10);
            document.getElementById('modal-movie-title').innerText = `Comentários: ${movieTitle}`;
            document.getElementById('novo-comentario-texto').value = '';
            document.getElementById('modal-comentarios').classList.remove('hidden');
            await carregarComentariosDoFilme(filmeAtualComentario);
        }

        function fecharModalComentarios() {
            document.getElementById('modal-comentarios').classList.add('hidden');
            filmeAtualComentario = null;
        }

        async function carregarComentariosDoFilme(movieId) {
            const token = localStorage.getItem('token');
            const lista = document.getElementById('comments-list');
            lista.innerHTML = '<p style="color:#aaa;">Carregando...</p>';
            try {
                const res = await fetch(`/api/comentarios/${movieId}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                if (!Array.isArray(data) || data.length === 0) {
                    lista.innerHTML = '<p style="color:#888;">Nenhum comentário feito ainda. Seja o primeiro!</p>';
                    return;
                }
                lista.innerHTML = '';
                data.forEach(c => {
                    const item = document.createElement('div');
                    item.className = 'comment-item';
                    item.innerHTML = `
                        <div class="comment-user">${c.usuario_nome || 'Usuário #' + c.usuario_id}</div>
                        <div class="comment-text">${c.texto}</div>
                    `;
                    lista.appendChild(item);
                });
            } catch (e) {
                lista.innerHTML = '<p style="color:#ef5350;">Erro ao carregar comentários.</p>';
            }
        }

        async function enviarComentario() {
            const texto = document.getElementById('novo-comentario-texto').value.trim();
            if (!texto) {
                alert('Digite algo antes de enviar o comentário.');
                return;
            }
            const token = localStorage.getItem('token');
            try {
                const res = await fetch('/api/comentarios', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ tmdb_movie_id: filmeAtualComentario, texto })
                });
                if (!res.ok) throw new Error('Falha ao registrar comentário');
                document.getElementById('novo-comentario-texto').value = '';
                await carregarComentariosDoFilme(filmeAtualComentario);
            } catch (e) {
                alert(e.message);
            }
        }

        async function fazerLogin() {
            const email = document.getElementById('login-email').value;
            const senha = document.getElementById('login-senha').value;
            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, senha })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Falha no login');
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('usuario_nome', data.usuario_nome);
                localStorage.setItem('papel', data.papel);
                document.getElementById('nav-user-info').innerText = `${data.usuario_nome} [${data.papel}]`;
                document.getElementById('btn-logout').classList.remove('hidden');
                document.getElementById('nav-tabs').classList.remove('hidden');
                mostrarAba('catalogo');
            } catch (err) {
                exibirAviso('msg-login', err.message, true);
            }
        }

        async function fazerCadastro() {
            const nome = document.getElementById('reg-nome').value;
            const email = document.getElementById('reg-email').value;
            const senha = document.getElementById('reg-senha').value;
            try {
                const res = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nome, email, senha, papel: 'usuario' })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Falha no cadastro');
                exibirAviso('msg-reg', 'Conta criada com sucesso! Faça o login.');
                setTimeout(() => alternarTela('box-login'), 1200);
            } catch (err) {
                exibirAviso('msg-reg', err.message, true);
            }
        }

        async function solicitarRecuperacao() {
            const email = document.getElementById('forgot-email').value;
            try {
                const res = await fetch('/api/auth/forgot-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                const data = await res.json();
                exibirAviso('msg-forgot', data.message || 'Verifique sua caixa de entrada no Mailtrap!');
            } catch (err) {
                exibirAviso('msg-forgot', 'Erro ao enviar solicitação.', true);
            }
        }

        async function redefinirSenha() {
            const token = document.getElementById('reset-token').value;
            const nova_senha = document.getElementById('reset-nova-senha').value;
            try {
                const res = await fetch('/api/auth/reset-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token, nova_senha })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Token inválido ou expirado');
                exibirAviso('msg-reset', 'Senha alterada com sucesso!');
                setTimeout(() => alternarTela('box-login'), 1500);
            } catch (err) {
                exibirAviso('msg-reset', err.message, true);
            }
        }

        function logout() {
            localStorage.clear();
            document.getElementById('nav-user-info').innerText = 'Não conectado';
            document.getElementById('btn-logout').classList.add('hidden');
            document.getElementById('nav-tabs').classList.add('hidden');
            alternarTela('box-login');
        }

        window.onload = () => {
            const params = new URLSearchParams(window.location.search);
            const tokenParam = params.get('token');
            if (tokenParam) {
                alternarTela('box-reset');
                document.getElementById('reset-token').value = tokenParam;
                return;
            }

            const token = localStorage.getItem('token');
            const nome = localStorage.getItem('usuario_nome');
            const papel = localStorage.getItem('papel');
            if (token && nome) {
                document.getElementById('nav-user-info').innerText = `${nome} [${papel}]`;
                document.getElementById('btn-logout').classList.remove('hidden');
                document.getElementById('nav-tabs').classList.remove('hidden');
                mostrarAba('catalogo');
            }
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_PAGE)

@app.get("/redefinir-senha", response_class=HTMLResponse)
def redefinir_senha_pagina():
    return HTMLResponse(content=HTML_PAGE)

# --- PROXY AUTH ---

@app.post("/api/auth/register")
async def register(request: Request):
    dados = await request.json()
    status_code, resp = chamar_auth_service("/register", dados)
    return resp

@app.post("/api/auth/login")
async def login(request: Request):
    dados = await request.json()
    status_code, resp = chamar_auth_service("/login", dados)
    return resp

@app.post("/api/auth/forgot-password")
async def forgot_password(request: Request):
    dados = await request.json()
    status_code, resp = chamar_auth_service("/forgot-password", dados)
    return resp

@app.post("/api/auth/reset-password")
async def reset_password(request: Request):
    dados = await request.json()
    status_code, resp = chamar_auth_service("/reset-password", dados)
    return resp

# --- ENDPOINTS DO CATÁLOGO ---

@app.get("/api/filmes")
def listar_filmes(usuario: dict = Depends(auth_guard.obter_usuario_atual)):
    url = f"https://api.themoviedb.org/3/person/31/movie_credits?api_key={TMDB_API_KEY}&language=pt-BR"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            dados = json.loads(response.read().decode('utf-8'))
            cast = dados.get("cast", [])
            return sorted(cast, key=lambda x: x.get("release_date") or "", reverse=True)[:30]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar TMDB: {str(e)}")

@app.get("/api/favoritos")
def listar_favoritos(
    usuario: dict = Depends(auth_guard.obter_usuario_atual),
    db: Session = Depends(get_db)
):
    favs = db.query(models.Favorito).filter(models.Favorito.usuario_id == usuario["usuario_id"]).order_by(models.Favorito.criado_em.desc()).all()
    return [
        {
            "id": f.id,
            "tmdb_movie_id": f.tmdb_movie_id,
            "titulo": f.titulo,
            "poster_path": f.poster_path,
            "criado_em": str(f.criado_em)
        }
        for f in favs
    ]

@app.post("/api/favoritos", status_code=status.HTTP_201_CREATED)
def favoritar(
    dados: schemas.FavoritoCriar,
    usuario: dict = Depends(auth_guard.obter_usuario_atual),
    db: Session = Depends(get_db)
):
    novo_fav = models.Favorito(
        usuario_id=usuario["usuario_id"],
        tmdb_movie_id=dados.tmdb_movie_id,
        titulo=dados.titulo,
        poster_path=dados.poster_path
    )
    db.add(novo_fav)
    db.commit()
    return {"message": "Favoritado com sucesso"}

@app.delete("/api/favoritos/{favorito_id}")
def remover_favorito(
    favorito_id: int,
    usuario: dict = Depends(auth_guard.obter_usuario_atual),
    db: Session = Depends(get_db)
):
    fav = db.query(models.Favorito).filter(
        models.Favorito.id == favorito_id,
        models.Favorito.usuario_id == usuario["usuario_id"]
    ).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorito não encontrado")
    db.delete(fav)
    db.commit()
    return {"message": "Favorito removido"}

@app.get("/api/comentarios/{tmdb_movie_id}")
def listar_comentarios(
    tmdb_movie_id: int,
    usuario: dict = Depends(auth_guard.obter_usuario_atual),
    db: Session = Depends(get_db)
):
    comentarios = db.query(models.Comentario).filter(models.Comentario.tmdb_movie_id == tmdb_movie_id).order_by(models.Comentario.criado_em.desc()).all()
    return [
        {
            "id": c.id,
            "usuario_id": c.usuario_id,
            "usuario_nome": usuario.get("nome", f"Usuário #{c.usuario_id}") if c.usuario_id == usuario.get("usuario_id") else f"Usuário #{c.usuario_id}",
            "tmdb_movie_id": c.tmdb_movie_id,
            "texto": c.texto,
            "criado_em": str(c.criado_em)
        }
        for c in comentarios
    ]

@app.post("/api/comentarios", status_code=status.HTTP_201_CREATED)
def comentar(
    dados: schemas.ComentarioCriar,
    usuario: dict = Depends(auth_guard.obter_usuario_atual),
    db: Session = Depends(get_db)
):
    novo_comentario = models.Comentario(
        usuario_id=usuario["usuario_id"],
        tmdb_movie_id=dados.tmdb_movie_id,
        texto=dados.texto
    )
    db.add(novo_comentario)
    db.commit()
    return {"message": "Comentário adicionado com sucesso"}