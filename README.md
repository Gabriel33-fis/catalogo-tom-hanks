# 🎬 Catálogo de Filmes Tom Hanks - Microsserviços e Autenticação

**Aluno:** Gabriel Castão Graciano  
**Disciplina:** Introdução à Computação em Nuvem  
**Professor:** [siriani](https://github.com/siriani)  

---

## 🔗 Acesso Rápido

* **Aplicação em Produção:** [https://gabriel-graciano-isw055.lapps.studio/](https://gabriel-graciano-isw055.lapps.studio/)
* **Repositório do Projeto:** [https://github.com/Gabriel33-fis/catalogo-tom-hanks](https://github.com/Gabriel33-fis/catalogo-tom-hanks)
* **Perfil do Professor:** [github.com/siriani](https://github.com/siriani)

---

## 📌 O que mudou nesta versão (Atividade 3)

A aplicação monolítica original foi refatorada e desacoplada em uma **Arquitetura de Microsserviços**:
* **Desacoplamento de Autenticação (`auth_service`)**: Microsserviço isolado responsável por cadastro, login com tokens JWT (`PyJWT` + `Bcrypt`) e fluxo de recuperação de senha via SMTP.
* **Isolamento de Rede (Segurança)**: O `auth_service` roda de forma privada dentro da rede interna Docker (`tom_hanks_net`), **sem portas expostas ao host**. Toda a comunicação externa é intermediada pelo `catalogo_service`.
* **Serviço de Catálogo (`catalogo_service`)**: Consome a API do TMDB para listar os filmes do ator Tom Hanks, atua como proxy do serviço de autenticação e gerencia favoritos e comentários com persistência no MySQL.
* **Recuperação de Senha com SMTP**: Fluxo de recuperação de senha com envio de e-mails via Mailtrap Sandbox e tokens com tempo de expiração de 30 minutos.

---

## 🏗️ Arquitetura e Rede Docker

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
      - JWT_SECRET=super_segredo_jwt_tom_hanks_fatec_2026
      - AUTH_SERVICE_URL=http://auth_service:5000
    depends_on:
      - auth_service
    networks:
      - tom_hanks_net

  auth_service:
    build: ./auth_service
    container_name: auth_service
    restart: always
    # Sem seção 'ports' exposta ao host — isolado na rede interna
    environment:
      - DB_HOST=35.226.64.52
      - DB_PORT=3306
      - DB_USER=IAC_2026_02_gabriel_graciano
      - DB_PASSWORD=********
      - DB_NAME=IAC_2026_02_gabriel_graciano
      - JWT_SECRET=super_segredo_jwt_tom_hanks_fatec_2026
      - BASE_PUBLIC_URL=[https://gabriel-graciano-isw055.lapps.studio](https://gabriel-graciano-isw055.lapps.studio)
      - MAILTRAP_HOST=sandbox.smtp.mailtrap.io
      - MAILTRAP_PORT=2525
      - MAILTRAP_USER=891b6bf689d033
      - MAILTRAP_PASS=********
    networks:
      - tom_hanks_net

networks:
  tom_hanks_net:
    driver: bridge