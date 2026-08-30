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

## 📸 Evidências de Funcionamento (Atividade 3)

### 1. E-mail de Recuperação Recebido no Mailtrap Sandbox
![Mailtrap Inbox](prints/print_1_mailtrap.png)

### 2. Confirmação de Senha Redefinida com Sucesso
![Sucesso Redefinição](prints/print_2_sucesso_redefinicao.png)

### 3. Bloqueio de Segurança com Token Inválido/Expirado
![Bloqueio Token Inválido](prints/print_3_token_invalido.png)

---

## 📌 O que mudou nesta versão (Atividade 3)

A aplicação monolítica original foi refatorada e desacoplada em uma **Arquitetura de Microsserviços**:
* **Desacoplamento de Autenticação (`auth_service`)**: Microsserviço isolado responsável por cadastro, login com tokens JWT (`PyJWT` + `Bcrypt`) e fluxo de recuperação de senha via SMTP.
* **Isolamento de Rede (Segurança)**: O `auth_service` roda de forma privada dentro da rede interna Docker (`tom_hanks_net`), **sem portas expostas ao host**. Toda a comunicação externa é intermediada pelo `catalogo_service`.
* **Serviço de Catálogo (`catalogo_service`)**: Consome a API do TMDB para listar os filmes do ator Tom Hanks, atua como proxy do serviço de autenticação e gerencia favoritos e comentários com persistência no MySQL.
* **Recuperação de Senha com SMTP**: Fluxo de recuperação de senha com envio de e-mails via Mailtrap Sandbox e tokens com tempo de expiração.

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
    # Sem seção 'ports' exposta ao host — isolado na rede interna
    environment:
      - DB_HOST=35.226.64.52
      - DB_PORT=3306
      - DB_USER=IAC_2026_02_gabriel_graciano
      - DB_PASSWORD=********
      - DB_NAME=IAC_2026_02_gabriel_graciano
      - JWT_SECRET=********
      - BASE_PUBLIC_URL=[https://gabriel-graciano-isw055.lapps.studio](https://gabriel-graciano-isw055.lapps.studio)
      - MAILTRAP_HOST=sandbox.smtp.mailtrap.io
      - MAILTRAP_PORT=2525
      - MAILTRAP_USER=********
      - MAILTRAP_PASS=********
    networks:
      - tom_hanks_net

networks:
  tom_hanks_net:
    driver: bridge

    # 🎬 Catálogo de Filmes Tom Hanks - Arquitetura de Microsserviços e RBAC

Aplicação web desenvolvida com arquitetura desacoplada de microsserviços em containers Docker, contemplando autenticação segura com JWT, recuperação de senhas via SMTP e **Controle de Acesso Baseado em Papel (RBAC - Role-Based Access Control)** aplicado no lado do servidor.

---

## 🔗 Links do Projeto
* **Aplicação em Produção:** [https://gabriel-graciano-isw055.lapps.studio/](https://gabriel-graciano-isw055.lapps.studio/)
* **Repositório GitHub:** [https://github.com/Gabriel33-fis/catalogo-tom-hanks](https://github.com/Gabriel33-fis/catalogo-tom-hanks)

---

## 🔐 1. Matriz de Permissões por Papel (RBAC)

A autorização é aplicada estritamente no backend (`catalogo_service` / `auth_service`), garantindo que nenhuma ação privilegiada dependa de validações puramente cosméticas na interface.

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
* **Como funciona hoje:** No momento do login, o `auth_service` inclui a claim de identificação e papel (`usuario_id`, `email`, `papel`) diretamente no payload do token JWT assinado criptograficamente com HMAC-SHA256 (`HS256`). O `catalogo_service` decodifica e valida a assinatura localmente através do middleware `auth_guard`, realizando o enforcement de permissões de forma stateless e sem latência de rede adicional.

### O que mudaria se fossemos para o PADRÃO A (Enforcement Centralizado)?
* **Alterações no `auth_service`:** Seria necessário criar um endpoint centralizado de autorização (ex: `POST /api/auth/authorize` ou `POST /api/auth/can-perform`) que receberia o token/identificador do usuário e o recurso/ação solicitada (ex: `acao: "apagar:comentario-de-outro"`), consultando as tabelas de papéis e permissões no banco a cada requisição.
* **Alterações no `catalogo_service`:** A rota `DELETE /api/comentarios/{comentario_id}` deixaria de inspecionar diretamente o payload decodificado e passaria a fazer uma requisição síncrona HTTP/gRPC para o `auth_service` perguntando se o usuário possui a permissão requerida antes de prosseguir com a exclusão.
* **Trade-offs:** 
  * *Vantagem do Padrão A:* Mudanças de papéis ou revogações teriam efeito imediato.
  * *Desvantagem do Padrão A:* Cada ação sensível geraria round-trips extras na rede Docker interna, tornando o `auth_service` um ponto central de gargalo de performance e ponto único de falha (*Single Point of Failure*).

---

## 📸 3. Evidências Práticas de Funcionamento

### Atividade 4 - RBAC (Enforcement no Backend)
1. **Tentativa de Usuário Comum apagando comentário de outro usuário (HTTP 403 Forbidden):**
   ![Erro 403 Forbidden](prints/print_rbac_403_usuario.png)

2. **Administrador moderando e apagando o comentário de outro usuário com sucesso (HTTP 200 OK):**
   ![Sucesso 200 Admin](prints/print_rbac_200_admin.png)
   ![Sucesso 200 Admin](prints/print_rbac_200_admin2.png)

---

### Atividade 3 - Autenticação e Recuperação de Senha
1. **E-mail de recuperação recebido no Mailtrap:**
   ![Mailtrap](prints/print_1_mailtrap.png)

2. **Sucesso na redefinição de senha:**
   ![Sucesso Redefinição](prints/print_2_sucesso_redefinicao.png)

3. **Bloqueio de segurança com token inválido/expirado:**
   ![Token Inválido](prints/print_3_token_invalido.png)