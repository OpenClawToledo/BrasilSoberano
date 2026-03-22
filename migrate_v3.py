"""
Brasil Soberano — Migração v3
- Feed: hora_local + envolvidos (JSON) + eventos_inerentes (JSON)
- Denúncias: lifecycle completo (recebida → processo → PL → votação → encerrada)
- DREX: gestor financeiro soberano por estado + cooperativismo nacional
"""
import sqlite3, os, json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brasil_soberano.db')
db = sqlite3.connect(DB_PATH)

# ─── 1. Adicionar colunas a feed_items ──────────────────────────────────────
cols = [r[1] for r in db.execute("PRAGMA table_info(feed_items)").fetchall()]
for col, dflt in [("hora_local","''"), ("envolvidos","'[]'"), ("eventos_inerentes","'[]'")]:
    if col not in cols:
        db.execute(f"ALTER TABLE feed_items ADD COLUMN {col} TEXT DEFAULT {dflt}")
print("✅ feed_items: colunas adicionadas")

# ─── 2. Adicionar colunas lifecycle a violations ─────────────────────────────
cols = [r[1] for r in db.execute("PRAGMA table_info(violations)").fetchall()]
new_cols = [
    ("lifecycle_status", "TEXT DEFAULT 'recebida'"),
    ("processo_numero", "TEXT"),
    ("pl_numero", "TEXT"),
    ("votes_approve", "INTEGER DEFAULT 0"),
    ("votes_reject", "INTEGER DEFAULT 0"),
    ("votes_audiencia", "INTEGER DEFAULT 0"),
    ("votes_reuniao", "INTEGER DEFAULT 0"),
    ("votes_assembleia", "INTEGER DEFAULT 0"),
    ("documentos", "TEXT DEFAULT '[]'"),
    ("lifecycle_log", "TEXT DEFAULT '[]'"),
]
for col, typedef in new_cols:
    if col not in cols:
        db.execute(f"ALTER TABLE violations ADD COLUMN {col} {typedef}")
print("✅ violations: lifecycle adicionado")

# ─── 3. Criar tabela drex_submissions ────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS drex_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT NOT NULL,
    renda REAL NOT NULL,
    irpf REAL NOT NULL,
    inss REAL NOT NULL,
    impostos_consumo REAL NOT NULL,
    total_impostos REAL NOT NULL,
    alocacao TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
)
""")
print("✅ drex_submissions: criada")

# ─── 4. Criar tabela state_economy ───────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS state_economy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    pib_bi REAL,
    custo_vida_mult REAL DEFAULT 1.0,
    setores_principais TEXT,
    energia_estatal INTEGER DEFAULT 1,
    agua_estatal INTEGER DEFAULT 1,
    transporte_mult REAL DEFAULT 1.0,
    populacao_mi REAL,
    hdi REAL,
    cooperativismo_fed_pct REAL DEFAULT 15.0,
    salario_medio REAL DEFAULT 2500.0,
    desemprego_pct REAL DEFAULT 12.0,
    gini REAL DEFAULT 0.55
)
""")

state_economy = [
    ("AC","Acre",19.0,0.82,'["extrativismo","agropecuária","serviços"]',1,1,0.95,0.92,0.663,12.0,1800,18.0,0.61),
    ("AL","Alagoas",73.0,0.78,'["açúcar","petróleo","serviços"]',1,1,0.88,3.34,0.631,14.0,1900,18.5,0.60),
    ("AM","Amazonas",108.0,0.90,'["zona franca","extrativismo","serviços"]',1,1,0.92,4.27,0.674,13.0,2200,16.0,0.59),
    ("AP","Amapá",19.0,0.85,'["mineração","extrativismo","serviços"]',1,1,0.90,0.88,0.708,11.0,2100,17.0,0.58),
    ("BA","Bahia",314.0,0.88,'["petroquímica","agronegócio","turismo"]',1,1,0.92,14.93,0.660,13.0,2000,15.0,0.60),
    ("CE","Ceará",189.0,0.82,'["indústria","serviços","turismo"]',1,1,0.88,9.24,0.682,14.0,1950,16.5,0.59),
    ("DF","Distrito Federal",295.0,1.50,'["governo","serviços","tecnologia"]',1,1,1.20,3.06,0.814,8.0,5200,9.0,0.63),
    ("ES","Espírito Santo",149.0,1.02,'["mineração","petróleo","logística"]',1,1,1.00,4.09,0.740,8.0,2900,9.5,0.53),
    ("GO","Goiás",241.0,0.92,'["agronegócio","indústria","serviços"]',1,1,0.95,7.21,0.735,9.0,2600,10.0,0.52),
    ("MA","Maranhão",107.0,0.75,'["soja","extrativismo","serviços"]',1,1,0.85,7.12,0.639,16.0,1700,20.0,0.62),
    ("MT","Mato Grosso",163.0,0.95,'["agronegócio","soja","pecuária"]',1,1,1.00,3.66,0.725,8.5,2800,9.0,0.54),
    ("MS","Mato Grosso do Sul",130.0,0.92,'["agronegócio","indústria","pecuária"]',1,1,0.98,2.81,0.729,8.0,2700,9.5,0.52),
    ("MG","Minas Gerais",715.0,1.00,'["mineração","indústria","agronegócio"]',1,1,1.00,21.41,0.731,9.0,2800,10.0,0.52),
    ("PA","Pará",222.0,0.88,'["mineração","agronegócio","extrativismo"]',1,1,0.90,8.69,0.646,13.5,2000,17.0,0.58),
    ("PB","Paraíba",72.0,0.80,'["serviços","comércio","agropecuária"]',1,1,0.88,4.04,0.658,15.0,1850,17.0,0.59),
    ("PR","Paraná",520.0,0.98,'["agronegócio","indústria","tecnologia"]',1,1,1.00,11.52,0.749,7.5,3000,8.5,0.49),
    ("PE","Pernambuco",233.0,0.88,'["tecnologia","açúcar","serviços"]',1,1,0.90,9.59,0.673,14.5,2100,16.0,0.59),
    ("PI","Piauí",55.0,0.78,'["agropecuária","soja","serviços"]',1,1,0.85,3.29,0.646,15.0,1750,18.0,0.60),
    ("RJ","Rio de Janeiro",851.0,1.25,'["petróleo","serviços","turismo"]',1,1,1.10,17.46,0.761,12.0,3500,11.0,0.55),
    ("RN","Rio Grande do Norte",80.0,0.85,'["petróleo","eólica","serviços"]',1,1,0.90,3.56,0.684,13.0,2050,15.5,0.56),
    ("RS","Rio Grande do Sul",498.0,1.00,'["agronegócio","indústria","vinho"]',1,1,1.00,11.42,0.746,8.0,3100,9.0,0.49),
    ("RO","Rondônia",48.0,0.90,'["agropecuária","mineração","madeira"]',1,1,0.95,1.80,0.690,9.5,2400,12.0,0.55),
    ("RR","Roraima",17.0,0.88,'["agropecuária","mineração","serviços"]',1,1,0.92,0.65,0.707,12.0,2200,15.0,0.57),
    ("SC","Santa Catarina",381.0,1.02,'["indústria","tecnologia","agronegócio"]',1,1,1.00,7.61,0.792,5.5,3400,7.0,0.45),
    ("SP","São Paulo",2391.0,1.20,'["indústria","serviços","tecnologia"]',1,1,1.10,45.92,0.783,9.0,3800,9.5,0.51),
    ("SE","Sergipe",47.0,0.82,'["petróleo","serviços","agropecuária"]',1,1,0.88,2.32,0.665,14.0,1950,17.0,0.58),
    ("TO","Tocantins",48.0,0.88,'["agronegócio","pecuária","soja"]',1,1,0.92,1.60,0.699,10.0,2300,13.0,0.55),
]
for s in state_economy:
    db.execute("""INSERT OR REPLACE INTO state_economy 
        (code,name,pib_bi,custo_vida_mult,setores_principais,energia_estatal,agua_estatal,
         transporte_mult,populacao_mi,hdi,cooperativismo_fed_pct,salario_medio,desemprego_pct,gini)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", s)
print("✅ state_economy: 27 estados")

# ─── 5. Atualizar feed_items com dados completos ──────────────────────────────
feed_updates = [
    (1, "2024-03-15 09:30",
     json.dumps(["IBGE", "Ministério das Cidades", "35 milhões de brasileiros"]),
     json.dumps(["Congresso vota ampliação do Marco do Saneamento",
                 "Municípios do Norte e Nordeste recebem verbas emergenciais",
                 "TCU publica relatório de fiscalização das obras de saneamento 2024-2025"])),
    (2, "2024-04-22 10:00",
     json.dumps(["STF", "FUNAI", "Associações indígenas", "Bancada ruralista"]),
     json.dumps(["Votação do marco temporal indígena no plenário",
                 "Movimentos indígenas organizam acampamento em Brasília",
                 "Presidência sanciona ou veta a legislação resultante"])),
    (3, "2025-01-02 08:00",
     json.dumps(["Receita Federal", "Ministério da Fazenda", "Empresas e contabilistas"]),
     json.dumps(["Alíquotas da CBS entram em vigor em 2026",
                 "Empresas adaptam sistemas fiscais ao novo modelo",
                 "Congresso revisa alíquotas do IBS por estado em 2027"])),
    (4, "2024-01-10 14:00",
     json.dumps(["INPE", "IBAMA", "Governo Federal", "Governadores amazônicos"]),
     json.dumps(["Fiscalização intensificada em áreas de risco identificadas pelo INPE",
                 "Cooperação internacional ampliada (Fundo Amazônia)",
                 "Meta de desmatamento zero debatida na COP30 em Belém (2025)"])),
    (5, "2024-09-01 07:30",
     json.dumps(["Sind-UTE/MG", "Secretaria de Educação de MG", "Professores estaduais", "Governo de MG"]),
     json.dumps(["Governo convoca mesa de negociação sob pressão judicial",
                 "Alunos e pais realizam manifestação na ALMG",
                 "TJMG decide sobre ilegalidade da greve e piso salarial"])),
    (6, "2024-06-10 11:00",
     json.dumps(["Prefeitura de Fortaleza", "Governo Federal", "Empresa construtora", "TCE-CE"]),
     json.dumps(["TCE-CE abre processo de prestação de contas da obra",
                 "Câmara Municipal convoca secretário para audiência pública",
                 "Novo prazo de retomada é negociado com o Ministério das Cidades"])),
    (7, "2024-05-05 08:00",
     json.dumps(["Ministério da Saúde", "OPS/OMS", "Secretarias estaduais", "200 municípios em emergência"]),
     json.dumps(["Decreto de emergência de saúde pública renovado por 90 dias",
                 "Congresso vota PL de obrigatoriedade da vacina da dengue no SUS",
                 "Pesquisadores divulgam novo estudo sobre sorotipo dominante em 2025"])),
    (8, "2024-08-20 09:00",
     json.dumps(["CLDF", "Governo Federal", "TCE-DF", "Governador do DF"]),
     json.dumps(["Ação judicial da CLDF para receber os valores em atraso",
                 "Ministério da Fazenda renegocia repasse para o próximo orçamento",
                 "STF é acionado para garantir cumprimento da obrigação constitucional"])),
    (9, "2024-07-15 10:00",
     json.dumps(["MEC", "Fundo Nacional de Desenvolvimento da Educação", "Municípios", "800.000 alunos afetados"]),
     json.dumps(["MEC lança programa emergencial de reforma com R$ 2 bilhões",
                 "TCU audita contratos de manutenção escolar nos 5 maiores estados",
                 "Congresso vota emenda constitucional vinculando 25% do FPM para infraestrutura escolar"])),
    (10, "2024-04-01 08:00",
     json.dumps(["IBAMA", "Polícia Federal", "FUNAI", "Comunidade Yanomami"]),
     json.dumps(["Tribunal de Haia analisa denúncia de crimes ambientais e humanitários",
                 "Governo federal apresenta plano de saúde integral para os Yanomami",
                 "STF decide sobre competência federal permanente de proteção das terras"])),
]
for fid, hora, envolvidos, eventos in feed_updates:
    db.execute("UPDATE feed_items SET hora_local=?, envolvidos=?, eventos_inerentes=? WHERE id=?",
               (hora, envolvidos, eventos, fid))
print("✅ feed_items: hora_local + envolvidos + eventos_inerentes atualizados (10 itens)")

db.commit()
db.close()
print("\n🇧🇷 Migração v3 concluída!")
