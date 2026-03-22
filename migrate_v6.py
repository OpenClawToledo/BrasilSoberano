"""
Brasil Soberano — Migração v6
Governança aberta: votação ao vivo, 100% aprovação, notificações por zona e gravidade.
Aplica-se à plataforma e às funções cívicas internas.
"""
import sqlite3, os, json, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brasil_soberano.db')
db = sqlite3.connect(DB_PATH)

# ─── 1. PROPOSTAS DE MUDANÇA ──────────────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS app_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    tipo TEXT NOT NULL,
    gravidade INTEGER NOT NULL CHECK(gravidade BETWEEN 1 AND 5),
    proponente TEXT DEFAULT 'Cidadão Anônimo',
    github_pr TEXT,
    codigo_diff TEXT,
    funcao_afetada TEXT,
    zona TEXT DEFAULT 'federal',
    estado TEXT,
    status TEXT DEFAULT 'proposta',
    created_at TEXT DEFAULT (datetime('now')),
    aprovada_em TEXT,
    rejeitada_em TEXT,
    motivo_rejeicao TEXT
)
""")

# ─── 2. SESSÕES DE VOTAÇÃO AO VIVO ────────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS voting_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    gravidade INTEGER NOT NULL,
    zona TEXT NOT NULL,
    estado TEXT,
    inicio TEXT NOT NULL,
    fim TEXT NOT NULL,
    duracao_horas REAL NOT NULL,
    quorum_minimo INTEGER NOT NULL,
    votos_sim INTEGER DEFAULT 0,
    votos_nao INTEGER DEFAULT 0,
    votos_abstencao INTEGER DEFAULT 0,
    cidadaos_notificados INTEGER DEFAULT 0,
    status TEXT DEFAULT 'agendada',
    resultado TEXT,
    transmissao_url TEXT,
    notas_ao_vivo TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(change_id) REFERENCES app_changes(id)
)
""")

# ─── 3. REGISTROS INDIVIDUAIS DE VOTO ────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS voting_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voting_event_id INTEGER NOT NULL,
    session_hash TEXT NOT NULL,
    voto TEXT NOT NULL CHECK(voto IN ('sim','nao','abstencao')),
    zona TEXT,
    estado TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(voting_event_id, session_hash),
    FOREIGN KEY(voting_event_id) REFERENCES voting_events(id)
)
""")

# ─── 4. NOTIFICAÇÕES POR ZONA ─────────────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS zone_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voting_event_id INTEGER NOT NULL,
    zona TEXT NOT NULL,
    estado TEXT,
    canal TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    cidadaos_estimados INTEGER DEFAULT 0,
    enviada_em TEXT DEFAULT (datetime('now')),
    confirmadas INTEGER DEFAULT 0,
    FOREIGN KEY(voting_event_id) REFERENCES voting_events(id)
)
""")

print("✅ app_changes: criada")
print("✅ voting_events: criada")
print("✅ voting_records: criada")
print("✅ zone_notifications: criada")

# ─── ESCALA DE GRAVIDADE ──────────────────────────────────────────────────────
GRAVIDADE_CONFIG = {
    1: {"nome":"Correção","emoji":"🟢","duracao_horas":6,"zona":"bairro","quorum":5,"cor":"#43A047"},
    2: {"nome":"Melhoria","emoji":"🟡","duracao_horas":24,"zona":"cidade","quorum":10,"cor":"#FFB300"},
    3: {"nome":"Nova Função","emoji":"🟠","duracao_horas":72,"zona":"estado","quorum":25,"cor":"#F4511E"},
    4: {"nome":"Mudança Estrutural","emoji":"🔴","duracao_horas":168,"zona":"federal","quorum":50,"cor":"#C62828"},
    5: {"nome":"Regra Constitucional","emoji":"⛔","duracao_horas":720,"zona":"todos","quorum":100,"cor":"#4A148C"},
}

# ─── SEED: PROPOSTAS HISTÓRICAS DA PLATAFORMA ────────────────────────────────
now = datetime.datetime.utcnow()

def dt(delta_dias):
    return (now + datetime.timedelta(days=delta_dias)).strftime('%Y-%m-%d %H:%M:%S')

proposals = [
    # 1 - Já aprovada (histórica)
    ("Feed com hora_local + envolvidos + eventos_inerentes",
     "Adicionar ao Feed os campos: hora_local (timestamp do evento), envolvidos (lista de entidades) e eventos_inerentes (cadeia de até 3 eventos esperados). Melhora contexto jornalístico.",
     "funcao","2","Jarvis (sistema)",
     "https://github.com/OpenClawToledo/BrasilSoberano/commit/bc6e4ac",
     "templates/feed.html, database.py (migrate_v3.py)","Feed / Notícias","federal",None,"aprovada",dt(-15),dt(-14),None,None),

    # 2 - Já aprovada
    ("Ciclo de vida completo para Denúncias Constitucionais",
     "Denúncias devem poder avançar por 6 estágios: recebida → analisada → processo → projeto_lei → votação → encerrada. Com documentação, votação de modalidade e histórico público.",
     "funcao","3","Jarvis (sistema)",
     "https://github.com/OpenClawToledo/BrasilSoberano/commit/bc6e4ac",
     "templates/denuncia_detalhe.html, app.py","Denúncias","federal",None,"aprovada",dt(-15),dt(-12),None,None),

    # 3 - Ativa — votando agora
    ("Regra: toda mudança no app exige 100% de aprovação ao vivo",
     "Qualquer alteração na plataforma deve passar por votação pública ao vivo. A duração e zona de notificação são definidas pela escala de gravidade (1-5). 100% dos votos + quorum mínimo = aprovação. Esta própria regra está sujeita a ela mesma.",
     "regra_constitucional","5","Toledo / Jarvis",
     None,
     "app.py (todas as rotas), database.py, TODOS os templates","Governança da Plataforma","todos",None,"votando",None,None,None,None),

    # 4 - Proposta aberta
    ("Integração com dados reais do Portal da Transparência (API)",
     "Consumir automaticamente dados de compras, contratos e despesas da API pública federal. Atualização diária às 06:00. Manter seeds como fallback se API indisponível.",
     "funcao","4","Cidadão Anônimo",
     None,
     "app.py (novo cron), database.py","Compras do Governo","federal",None,"proposta",None,None,None,None),

    # 5 - Proposta aberta
    ("Mapa interativo de obras por geolocalização",
     "Adicionar mapa do Brasil onde cada projeto do Painel aparece com marcador colorido por status. Clique abre resumo e link para detalhe. Usa Leaflet.js (sem CDN externo — bundled).",
     "funcao","3","Cidadão Anônimo",
     None,
     "templates/painel.html, static/js","Painel de Projetos","federal",None,"proposta",None,None,None,None),
]

for p in proposals:
    db.execute("""INSERT INTO app_changes
        (titulo,descricao,tipo,gravidade,proponente,github_pr,codigo_diff,
         funcao_afetada,zona,estado,status,aprovada_em,rejeitada_em,motivo_rejeicao)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (p[0],p[1],p[2],int(p[3]),p[4],p[5],p[6],p[7],p[8],p[9],p[10],p[11],p[12],p[13]))

print(f"✅ app_changes: 5 propostas")

# ─── SEED: EVENTOS DE VOTAÇÃO ─────────────────────────────────────────────────
# Votação ao vivo ativa: Regra dos 100% (change_id=3, gravidade=5)
grav5 = GRAVIDADE_CONFIG[5]
inicio_voto = now.strftime('%Y-%m-%d %H:%M:%S')
fim_voto = (now + datetime.timedelta(hours=grav5['duracao_horas'])).strftime('%Y-%m-%d %H:%M:%S')

db.execute("""INSERT INTO voting_events
    (change_id,titulo,gravidade,zona,estado,inicio,fim,duracao_horas,
     quorum_minimo,votos_sim,votos_nao,votos_abstencao,cidadaos_notificados,
     status,resultado,notas_ao_vivo)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (3,"🔴 AO VIVO: Regra dos 100% para mudanças na plataforma",5,"todos",None,
     inicio_voto,fim_voto,grav5['duracao_horas'],grav5['quorum'],
     0,0,0,215000,"em_andamento",None,
     json.dumps([
         {"hora": now.strftime('%H:%M'), "nota": "🚨 Votação iniciada. Todos os cidadãos notificados."},
         {"hora": now.strftime('%H:%M'), "nota": "📢 Esta regra se aplica a si mesma — a aprovação desta proposta exige 100% de votos SIM."},
     ])))

# Votação histórica encerrada (aprovada): Feed v3 (change_id=1)
db.execute("""INSERT INTO voting_events
    (change_id,titulo,gravidade,zona,estado,inicio,fim,duracao_horas,
     quorum_minimo,votos_sim,votos_nao,votos_abstencao,cidadaos_notificados,
     status,resultado)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (1,"Feed v3: hora_local + envolvidos + eventos_inerentes",2,"cidade",None,
     dt(-16),dt(-15),24,10,
     18,0,2,8500,"encerrada","aprovada"))

# Notificações da votação ao vivo
notifications = [
    (1,"todos",None,"broadcast","🚨 VOTAÇÃO AO VIVO: Regra dos 100% para mudanças na plataforma Brasil Soberano. Duração: 30 dias. Seu voto determina as regras do app. soberano.fiosmj.com/governanca",215000),
    (1,"federal",None,"portal","📢 Nova votação constitucional aberta: Governa a plataforma Brasil Soberano. Prazo: 30 dias. 100% de aprovação necessária.",85000),
    (2,"cidade",None,"portal","✅ Votação encerrada: Feed v3 aprovado por unanimidade (18 sim, 0 não, 2 abstenções)",8500),
]
for n in notifications:
    db.execute("INSERT INTO zone_notifications (voting_event_id,zona,estado,canal,mensagem,cidadaos_estimados,confirmadas) VALUES (?,?,?,?,?,?,?)",
               (n[0],n[1],n[2],n[3],n[4],n[5],int(n[5]*0.72)))

print("✅ voting_events: 2 eventos (1 ao vivo, 1 histórico)")
print("✅ zone_notifications: 3 notificações")

# Gravar config de gravidade na DB para acesso pelo app
db.execute("CREATE TABLE IF NOT EXISTS gravity_config (gravidade INTEGER PRIMARY KEY, nome TEXT, emoji TEXT, duracao_horas REAL, zona TEXT, quorum INTEGER, cor TEXT)")
for g, cfg in GRAVIDADE_CONFIG.items():
    db.execute("INSERT OR REPLACE INTO gravity_config VALUES (?,?,?,?,?,?,?)",
               (g, cfg['nome'], cfg['emoji'], cfg['duracao_horas'], cfg['zona'], cfg['quorum'], cfg['cor']))
print("✅ gravity_config: 5 níveis")

db.commit()
db.close()
print("\n🇧🇷 Migração v6 concluída!")
