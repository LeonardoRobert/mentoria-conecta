-- ============================================================
--  MentoriaConecta - Banco de Dados (Supabase / PostgreSQL)
--  Execute este script no SQL Editor do Supabase
--  https://supabase.com/dashboard/project/SEU_PROJETO/sql
-- ============================================================

-- ============================================================
-- TABELA: usuarios (base para mentores e alunos)
-- ============================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    senha_hash VARCHAR(256) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('mentor', 'aluno', 'admin')),
    telefone VARCHAR(20),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    bio TEXT,
    foto_url TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- TABELA: habilidades (catálogo de habilidades/áreas)
-- ============================================================
CREATE TABLE IF NOT EXISTS habilidades (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    categoria VARCHAR(80),
    descricao TEXT
);

-- ============================================================
-- TABELA: usuario_habilidades (n:n - usuário <-> habilidade)
-- ============================================================
CREATE TABLE IF NOT EXISTS usuario_habilidades (
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    habilidade_id INT REFERENCES habilidades(id) ON DELETE CASCADE,
    nivel VARCHAR(20) CHECK (nivel IN ('basico', 'intermediario', 'avancado')),
    PRIMARY KEY (usuario_id, habilidade_id)
);

-- ============================================================
-- TABELA: mentorias (relacionamento n:n mentor <-> aluno)
-- Um mentor pode atender vários alunos e vice-versa
-- ============================================================
CREATE TABLE IF NOT EXISTS mentorias (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    mentor_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    aluno_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pendente' CHECK (status IN ('pendente', 'ativa', 'concluida', 'cancelada')),
    area_foco VARCHAR(150),
    objetivo TEXT,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(mentor_id, aluno_id)
);

-- ============================================================
-- TABELA: sessoes (agendamentos de encontros)
-- ============================================================
CREATE TABLE IF NOT EXISTS sessoes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    mentoria_id UUID REFERENCES mentorias(id) ON DELETE CASCADE,
    data_hora TIMESTAMP WITH TIME ZONE NOT NULL,
    duracao_minutos INT DEFAULT 60,
    formato VARCHAR(20) DEFAULT 'online' CHECK (formato IN ('online', 'presencial')),
    link_reuniao TEXT,
    local TEXT,
    status VARCHAR(20) DEFAULT 'agendada' CHECK (status IN ('agendada', 'realizada', 'cancelada', 'falta')),
    notas TEXT,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- TABELA: feedbacks (avaliações pós-sessão)
-- ============================================================
CREATE TABLE IF NOT EXISTS feedbacks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    sessao_id UUID REFERENCES sessoes(id) ON DELETE CASCADE,
    avaliador_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    avaliado_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    nota INT CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- TABELA: tokens_jwt (controle de tokens ativos)
-- ============================================================
CREATE TABLE IF NOT EXISTS tokens_jwt (
    id SERIAL PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expira_em TIMESTAMP WITH TIME ZONE NOT NULL,
    revogado BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- DADOS INICIAIS: habilidades
-- ============================================================
INSERT INTO habilidades (nome, categoria) VALUES
    ('Matemática', 'Exatas'),
    ('Física', 'Exatas'),
    ('Química', 'Exatas'),
    ('Programação Python', 'Tecnologia'),
    ('Programação Web', 'Tecnologia'),
    ('Banco de Dados', 'Tecnologia'),
    ('Redação', 'Humanas'),
    ('História', 'Humanas'),
    ('Inglês', 'Idiomas'),
    ('Espanhol', 'Idiomas'),
    ('Biologia', 'Naturais'),
    ('Orientação de Carreira', 'Profissional'),
    ('Lógica de Programação', 'Tecnologia'),
    ('Geometria', 'Exatas')
ON CONFLICT (nome) DO NOTHING;

-- ============================================================
-- USUÁRIO ADMIN INICIAL (senha: Admin@123)
-- Troque a senha após o primeiro login!
-- ============================================================
INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES
    ('Administrador', 'admin@mentoriaconecta.com',
     'pbkdf2:sha256:600000$admin_hash_placeholder',
     'admin')
ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- FUNÇÃO: atualiza timestamp automaticamente
-- ============================================================
CREATE OR REPLACE FUNCTION atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_usuarios_updated
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();

-- ============================================================
-- VIEW: ranking de mentores (algoritmo de recomendação base)
-- ============================================================
CREATE OR REPLACE VIEW vw_ranking_mentores AS
SELECT
    u.id,
    u.nome,
    u.email,
    u.cidade,
    u.estado,
    u.bio,
    u.foto_url,
    COUNT(DISTINCT m.id) AS total_mentorias,
    COUNT(DISTINCT s.id) AS total_sessoes,
    ROUND(AVG(f.nota)::NUMERIC, 2) AS media_avaliacao,
    COUNT(DISTINCT f.id) AS total_avaliacoes
FROM usuarios u
LEFT JOIN mentorias m ON m.mentor_id = u.id AND m.status IN ('ativa', 'concluida')
LEFT JOIN sessoes s ON s.mentoria_id = m.id AND s.status = 'realizada'
LEFT JOIN feedbacks f ON f.avaliado_id = u.id
WHERE u.tipo = 'mentor' AND u.ativo = TRUE
GROUP BY u.id, u.nome, u.email, u.cidade, u.estado, u.bio, u.foto_url
ORDER BY media_avaliacao DESC NULLS LAST, total_sessoes DESC;

-- ============================================================
-- ATUALIZAÇÃO: tabela de inscrições em sessões (vagas)
-- Execute este bloco se já rodou o SQL anterior
-- ============================================================

-- Remove coluna antiga de agendamento individual se existir
-- ALTER TABLE sessoes DROP COLUMN IF EXISTS aluno_id;

-- TABELA: inscricoes_sessao (aluno se inscreve em vagas abertas pelo mentor)
CREATE TABLE IF NOT EXISTS inscricoes_sessao (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    sessao_id UUID REFERENCES sessoes(id) ON DELETE CASCADE,
    aluno_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'inscrito' CHECK (status IN ('inscrito', 'presente', 'faltou', 'cancelado')),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(sessao_id, aluno_id)
);

-- Adiciona colunas de vagas e tema na tabela sessoes (se não existirem)
ALTER TABLE sessoes ADD COLUMN IF NOT EXISTS vagas_total INT DEFAULT 10;
ALTER TABLE sessoes ADD COLUMN IF NOT EXISTS tema VARCHAR(200);

-- RLS para nova tabela
ALTER TABLE inscricoes_sessao ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow_all_inscricoes" ON inscricoes_sessao FOR ALL USING (true) WITH CHECK (true);

-- VIEW: sessões com vagas disponíveis
CREATE OR REPLACE VIEW vw_sessoes_abertas AS
SELECT
    s.*,
    u.nome AS mentor_nome,
    u.email AS mentor_email,
    COUNT(i.id) AS inscritos,
    (s.vagas_total - COUNT(i.id)) AS vagas_livres
FROM sessoes s
JOIN mentorias m ON m.id = s.mentoria_id
JOIN usuarios u ON u.id = m.mentor_id
LEFT JOIN inscricoes_sessao i ON i.sessao_id = s.id AND i.status != 'cancelado'
WHERE s.status = 'agendada'
GROUP BY s.id, u.nome, u.email;
