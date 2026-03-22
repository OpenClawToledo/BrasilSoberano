"""
Brasil Soberano — Migração de Segurança
Audit log com hash chain, tokens CSRF, fingerprints de voto verificáveis.
"""
import sqlite3, os, hashlib, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brasil_soberano.db')
db = sqlite3.connect(DB_PATH)

# ─── 1. AUDIT LOG — IMUTÁVEL COM HASH CHAIN ───────────────────────────────────
# Cada evento registra o hash do evento anterior → qualquer adulteração quebra a cadeia
db.execute("""
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    tipo TEXT NOT NULL,
    ator TEXT,
    ip_hash TEXT,
    recurso TEXT,
    detalhe TEXT,
    hash_anterior TEXT,
    hash_proprio TEXT NOT NULL
)
""")
print("✅ audit_log: criada")

# ─── 2. RECIBOS DE VOTO VERIFICÁVEIS ─────────────────────────────────────────
# Cada voto gera um token público que o cidadão pode usar para verificar
# sem revelar identidade (hash do conteúdo do voto, não da sessão)
db.execute("""
CREATE TABLE IF NOT EXISTS vote_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voting_event_id INTEGER NOT NULL,
    receipt_token TEXT NOT NULL UNIQUE,
    voto_hash TEXT NOT NULL,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    verificado INTEGER DEFAULT 0,
    FOREIGN KEY(voting_event_id) REFERENCES voting_events(id)
)
""")
print("✅ vote_receipts: criada")

# ─── 3. RATE LIMIT LOG — TRANSPARENTE ────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS rate_limit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    ip_hash TEXT NOT NULL,
    rota TEXT NOT NULL,
    bloqueado INTEGER DEFAULT 1,
    motivo TEXT
)
""")
print("✅ rate_limit_log: criada")

# ─── 4. CSRFTOKENS TABLE (backup para sessões stateless) ─────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS csrf_tokens (
    token TEXT PRIMARY KEY,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    usado INTEGER DEFAULT 0,
    expirado INTEGER DEFAULT 0
)
""")

# Limpar tokens velhos automaticamente (> 1h)
db.execute("""
CREATE TRIGGER IF NOT EXISTS expire_csrf AFTER INSERT ON csrf_tokens
BEGIN
    UPDATE csrf_tokens SET expirado=1
    WHERE criado_em < datetime('now', '-1 hour') AND usado=0;
END
""")
print("✅ csrf_tokens: criada")

# ─── 5. SEED: PRIMEIRO EVENTO DO AUDIT LOG ───────────────────────────────────
genesis = "BRASIL_SOBERANO_GENESIS_BLOCK_v1_" + datetime.datetime.utcnow().isoformat()
genesis_hash = hashlib.sha256(genesis.encode()).hexdigest()

db.execute("""INSERT INTO audit_log (tipo,ator,ip_hash,recurso,detalhe,hash_anterior,hash_proprio)
    VALUES (?,?,?,?,?,?,?)""",
    ("genesis","sistema","0"*64,"sistema",
     "Bloco gênesis do log de auditoria — Brasil Soberano plataforma cívica",
     "0"*64, genesis_hash))
print(f"✅ audit_log: bloco gênesis criado ({genesis_hash[:16]}...)")

db.commit()
db.close()
print("\n🔒 Migração de segurança concluída!")
