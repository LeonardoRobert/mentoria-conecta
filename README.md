# MentoriaConecta 🎓

> Plataforma de Mentorias para Alunos de Baixa Renda  
> Projeto Extensionista — UNIG EAD — Tema Integrador IV  
> **ODS 4: Educação de Qualidade**

---

## 📋 Sobre o Projeto

O **MentoriaConecta** é uma plataforma web que conecta voluntários (mentores) com alunos de baixa renda, democratizando o acesso à orientação profissional e acadêmica. O sistema utiliza um algoritmo de recomendação baseado no Coeficiente de Jaccard (Matemática Discreta) para sugerir os mentores mais compatíveis com o perfil de cada aluno.

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia |
|--------|-----------|
| Back-end | Python 3.11 + Flask |
| Banco de Dados | Supabase (PostgreSQL) |
| Autenticação | JWT (JSON Web Tokens) |
| Front-end | HTML5 + CSS3 + JavaScript |
| Versionamento | Git + GitHub |

---

## ⚙️ Como rodar o projeto

### 1. Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/mentoria-conecta.git
cd mentoria-conecta
```

### 2. Crie e ative o ambiente virtual
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas chaves do Supabase:
```bash
cp .env.example .env
```

Edite o arquivo `.env`:
```env
SUPABASE_URL=https://SEU_PROJETO.supabase.co
SUPABASE_KEY=sua_anon_key_aqui
SUPABASE_SECRET=sua_service_role_key_aqui
SECRET_KEY=qualquer-string-aleatoria
JWT_SECRET_KEY=outra-string-aleatoria
```

> **Onde encontrar as chaves no Supabase:**  
> Acesse: `https://supabase.com/dashboard/project/SEU_PROJETO/settings/api`

### 5. Configure o banco de dados no Supabase

No painel do Supabase, vá em **SQL Editor** e execute o conteúdo do arquivo:
```
docs/database.sql
```

### 6. Inicie o servidor
```bash
python run.py
```

Acesse: **http://localhost:5000**

---

## 📊 Estrutura do Projeto

```
mentoria-conecta/
├── app/
│   ├── __init__.py          # Factory do Flask
│   ├── routes/
│   │   ├── main_routes.py   # Landing page e dashboard redirect
│   │   ├── auth_routes.py   # Login, registro, logout + API JWT
│   │   ├── mentor_routes.py # Dashboard e CRUD do mentor
│   │   ├── aluno_routes.py  # Dashboard, recomendações do aluno
│   │   ├── sessao_routes.py # Agendamento e feedback
│   │   └── admin_routes.py  # Painel administrativo
│   └── utils/
│       ├── auth.py          # JWT, hash, algoritmo de recomendação
│       └── supabase_client.py # Conexão com Supabase
├── templates/               # HTML (Jinja2)
├── static/
│   ├── css/main.css
│   └── js/main.js
├── docs/
│   └── database.sql         # MER + DDL completo
├── config.py                # Configurações (Supabase keys aqui)
├── run.py                   # Ponto de entrada
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 🧠 Algoritmo de Recomendação (Matemática Discreta)

O sistema utiliza o **Coeficiente de Jaccard** para calcular compatibilidade:

```
J(A, B) = |A ∩ B| / |A ∪ B|
```

Onde:
- **A** = conjunto de habilidades do mentor
- **B** = conjunto de habilidades buscadas pelo aluno

O **score final** combina:
- 60% compatibilidade de habilidades (Jaccard)
- 30% média de avaliações recebidas
- 10% experiência (quantidade de sessões realizadas)

---

## 🗃️ Modelo Entidade-Relacionamento (MER)

```
usuarios (1) ──── (n) usuario_habilidades (n) ──── (1) habilidades
usuarios (1) ──── (n) mentorias (n) ──── (1) usuarios
                        |
                        (n) sessoes (1) ──── (n) feedbacks
```

Relacionamento **n:n** entre mentor e aluno via tabela `mentorias`:
- Um mentor pode atender vários alunos
- Um aluno pode ter vários mentores

---

## 🎯 ODS 4 — Educação de Qualidade

> *"Garantir educação inclusiva, equitativa e de qualidade e promover oportunidades de aprendizagem ao longo da vida para todos."*

O projeto contribui para o ODS 4 ao:
- Eliminar a barreira financeira ao acesso à mentoria
- Conectar pessoas em situação de vulnerabilidade com profissionais qualificados
- Promover o voluntariado e o impacto social através da tecnologia

---

## 👥 Autores

- **[Seu Nome]** — [RA]
- Orientadora: **Prof. Denise Moraes**
- Curso: Ciência da Computação — 4º Período
- Instituição: UNIG EAD — 2025

---

## 📄 Licença

Projeto acadêmico — uso educacional.
