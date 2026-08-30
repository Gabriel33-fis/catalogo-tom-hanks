# 🎬 Catálogo de Filmes Tom Hanks - Microsserviços e RBAC

**Aluno:** Gabriel Castão Graciano  
**Disciplina:** Introdução à Computação em Nuvem  
**Professor:** [siriani](https://github.com/siriani)  

---

## 🔗 Acesso Rápido

* **Aplicação em Produção:** [https://gabriel-graciano-isw055.lapps.studio/](https://gabriel-graciano-isw055.lapps.studio/)
* **Repositório do Projeto:** [https://github.com/Gabriel33-fis/catalogo-tom-hanks](https://github.com/Gabriel33-fis/catalogo-tom-hanks)
* **Perfil do Professor:** [github.com/siriani](https://github.com/siriani)

---

## 📌 Visão Geral do Projeto

Aplicação web desenvolvida com arquitetura desacoplada de microsserviços em containers Docker, contemplando autenticação segura com JWT, recuperação de senhas via SMTP e **Controle de Acesso Baseado em Papel (RBAC - Role-Based Access Control)** com validação estrita no lado do servidor.

### Principais Componentes:
* **`catalogo_service`**: Interface web, integração com a API externa do The Movie Database (TMDB), proxy para rotas de autenticação, gerenciamento de favoritos e comentários com regras de permissão (RBAC).
* **`auth_service`**: Microsserviço isolado em rede privada responsável por cadastro, login com hash de senha (`Bcrypt`), emissão de tokens JWT (`PyJWT`) com claims de papel e fluxo de recuperação de senha via servidor SMTP (Mailtrap Sandbox).
* **Isolamento de Rede**: O `auth_service` roda estritamente dentro da rede interna `tom_hanks_net` sem expor portas ao host.

---

## 🔐 1. Matriz de Permissões por Papel (RBAC)

A autorização é aplicada no backend (`catalogo_service`), garantindo que ações privilegiadas não dependam de controles na interface.

| Recurso / Ação | Papel: `usuario` | Papel: `admin` | Validação no Backend |
| :--- | :---: | :---: | :--- |
| **Visualizar Catálogo (TMDB)** | ✅ Permitido | ✅ Permitido | Requer autenticação JWT válida |
| **Gerenciar Favoritos Próprios** | ✅ Permitido | ✅ Permitido | Isolado por `usuario_id` no banco |
| **Criar Comentários** | ✅ Permitido | ✅ Permitido | Requer autenticação JWT válida |
| **Apagar Próprio Comentário** | ✅ Permitido | ✅ Permitido | Valida `comentario.usuario_id == current_user.id` |
| **Apagar Comentário de Terceiros (Moderação)** | ❌ **Negado (403)** | ✅ Permitido | Valida claim `papel == 'admin'` |

---

## 🏗️ 2. Arquitetura de Autorização: Padrão A vs Padrão B

### Resposta Curta:
* **Padrão utilizado no projeto:** **PADRÃO B (Claims no Token JWT)**.
* **Como funciona hoje:** No momento do login, o `auth_service` inclui as claims de identificação e papel (`usuario_id`, `email`, `papel`) no payload do token JWT assinado criptograficamente com HMAC-SHA256 (`HS256`). O `catalogo_service` decodifica e valida a assinatura localmente através do middleware `auth_guard`, realizando o enforcement de permissões de forma *stateless* e sem tráfego de rede adicional.

### O que mudaria se fossemos para o PADRÃO A (Enforcement Centralizado)?
* **Alterações no `auth_service`:** Seria necessário criar um endpoint centralizado de autorização (ex: `POST /api/auth/authorize`) que receberia o token do usuário e a ação solicitada (ex: `acao: "apagar:comentario-de-outro"`), consultando as tabelas de papéis e permissões no banco a cada requisição.
* **Alterações no `catalogo_service`:** A rota `DELETE /api/comentarios/{comentario_id}` deixaria de inspecionar diretamente o payload decodificado e faria uma requisição síncrona HTTP/gRPC para o `auth_service` perguntando se o usuário possui a permissão requerida antes de executar a exclusão.
* **Trade-offs:** 
  * *Vantagem do Padrão A:* Mudanças de papéis ou revogações de acesso têm efeito imediato sem esperar expiração de token.
  * *Desvantagem do Padrão A:* Cada operação protegida gera requisições de rede extras internas, tornando o `auth_service` um gargalo de desempenho e ponto único de falha (*Single Point of Failure*).

---

## 🏗️ 3. Arquitetura e Rede Docker

```text
       [ Usuário / Navegador ]
                  │
                  ▼ Porta 8207 (Host)
      ┌───────────────────────┐
      │   catalogo_service    │  (FastAPI + UI + TMDB + MySQL)
      └───────────┬───────────┘
                  │  Rede interna: tom_hanks_net
                  │  (Sem porta pública pro host)
                  ▼
      ┌───────────────────────┐
      │     auth_service      │  (FastAPI + JWT + Mailtrap + MySQL)
      └───────────────────────┘
      version: '3.8'

services:
  catalogo_service:
    build: ./catalogo_service
    container_name: catalogo_service
    restart: always
    ports:
      - "8207:8000"
    environment:
      - DB_HOST=35.226.64.52
      - DB_PORT=3306
      - DB_USER=IAC_2026_02_gabriel_graciano
      - DB_PASSWORD=********
      - DB_NAME=IAC_2026_02_gabriel_graciano
      - TMDB_API_KEY=********
      - JWT_SECRET=********
      - AUTH_SERVICE_URL=http://auth_service:5000
    depends_on:
      - auth_service
    networks:
      - tom_hanks_net

  auth_service:
    build: ./auth_service
    container_name: auth_service
    restart: always
    environment:
      - DB_HOST=35.226.64.52
      - DB_PORT=3306
      - DB_USER=IAC_2026_02_gabriel_graciano
      - DB_PASSWORD=********
      - DB_NAME=IAC_2026_02_gabriel_graciano
      - JWT_SECRET=********
      - BASE_PUBLIC_URL=https://gabriel-graciano-isw055.lapps.studio
      - MAILTRAP_HOST=sandbox.smtp.mailtrap.io
      - MAILTRAP_PORT=2525
      - MAILTRAP_USER=********
      - MAILTRAP_PASS=********
    networks:
      - tom_hanks_net

networks:
  tom_hanks_net:
    driver: bridge