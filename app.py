"""
Brasil Soberano — Plataforma de Educação Cívica
Flask app principal
"""

import sqlite3
import os
import json
import hashlib
from flask import Flask, render_template, request, jsonify, g, send_from_directory

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brasil_soberano.db')

# Import v2 content
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes_v2 import CRIMES_FINANCEIROS, MERCADO_CONTENT

# ─── SEGURANÇA ───────────────────────────────────────────────────────────────
from security import (
    apply_security_headers, session_fingerprint, ip_hash,
    csrf_generate, csrf_validate,
    rate_limit, audit, audit_verify, gerar_recibo_voto
)

app.after_request(apply_security_headers)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# ─── TIMELINE ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    category = request.args.get('category', '')
    search = request.args.get('search', '')

    base_query = '''
        SELECT e.*, p.name as pattern_name
        FROM events e
        LEFT JOIN patterns p ON e.pattern_id = p.id
        WHERE 1=1
    '''
    args = []
    if category:
        base_query += ' AND e.category = ?'
        args.append(category)
    if search:
        base_query += ' AND (e.title LIKE ? OR e.description LIKE ? OR e.key_figures LIKE ?)'
        args += [f'%{search}%', f'%{search}%', f'%{search}%']
    base_query += ' ORDER BY e.year ASC, e.date ASC'

    events = query_db(base_query, args)
    categories = query_db('SELECT DISTINCT category FROM events ORDER BY category')
    return render_template('index.html',
                           events=events,
                           categories=categories,
                           selected_category=category,
                           search=search)


# ─── PADRÕES ────────────────────────────────────────────────────────────────

@app.route('/padroes')
def padroes():
    patterns = query_db('SELECT * FROM patterns ORDER BY id')
    pattern_events = {}
    for p in patterns:
        evts = query_db(
            'SELECT * FROM events WHERE pattern_id = ? ORDER BY year ASC', (p['id'],)
        )
        pattern_events[p['id']] = evts
    return render_template('padroes.html', patterns=patterns, pattern_events=pattern_events)


# ─── ESTADOS ────────────────────────────────────────────────────────────────

@app.route('/estados')
def estados():
    states = query_db('SELECT * FROM states ORDER BY name')
    return render_template('estados.html', states=states)


@app.route('/estados/<code>')
def estado_detail(code):
    state = query_db('SELECT * FROM states WHERE code = ?', (code.upper(),), one=True)
    if not state:
        return render_template('404.html'), 404
    events = query_db(
        'SELECT * FROM events WHERE state LIKE ? ORDER BY year ASC', (f'%{code.upper()}%',)
    )
    return render_template('estado_detail.html', state=state, events=events)


# ─── FAMÍLIAS ────────────────────────────────────────────────────────────────

@app.route('/familias')
def familias():
    category = request.args.get('category', '')
    if category:
        families = query_db('SELECT * FROM families WHERE category = ? ORDER BY name', (category,))
    else:
        families = query_db('SELECT * FROM families ORDER BY category, name')
    categories = query_db('SELECT DISTINCT category FROM families ORDER BY category')
    return render_template('familias.html',
                           families=families,
                           categories=categories,
                           selected_category=category)


# ─── SIMULADOR ──────────────────────────────────────────────────────────────

@app.route('/simulador')
def simulador():
    scenarios = query_db('SELECT * FROM scenarios ORDER BY year ASC')
    return render_template('simulador.html', scenarios=scenarios)


@app.route('/simulador/vote', methods=['POST'])
def simulador_vote():
    data = request.get_json()
    scenario_id = data.get('scenario_id')
    vote = data.get('vote')  # 'a' or 'b'
    scenario = query_db('SELECT * FROM scenarios WHERE id = ?', (scenario_id,), one=True)
    if not scenario:
        return jsonify({'error': 'Cenário não encontrado'}), 404
    return jsonify({
        'what_happened': scenario['what_happened'],
        'consequence': scenario['consequence'],
        'lesson': scenario['lesson'],
        'option_a': scenario['option_a'],
        'option_b': scenario['option_b'],
        'vote': vote
    })


# ─── CONSTITUIÇÃO — ver versão v2 abaixo ─────────────────────────────────────


# ─── TRANSPARÊNCIA ──────────────────────────────────────────────────────────

@app.route('/transparencia')
def transparencia():
    # Compute content hashes for all tables
    db = get_db()
    tables = ['events', 'patterns', 'states', 'families', 'scenarios', 'constitution_articles']
    hashes = {}
    counts = {}
    for table in tables:
        rows = db.execute(f'SELECT * FROM {table} ORDER BY id').fetchall()
        counts[table] = len(rows)
        content = json.dumps([dict(r) for r in rows], ensure_ascii=False, sort_keys=True)
        hashes[table] = hashlib.sha256(content.encode()).hexdigest()
    return render_template('transparencia.html', hashes=hashes, counts=counts)


# ─── API endpoints ───────────────────────────────────────────────────────────

@app.route('/api/events')
def api_events():
    events = query_db('SELECT * FROM events ORDER BY year ASC')
    return jsonify([dict(e) for e in events])


@app.route('/api/stats')
def api_stats():
    counts = {}
    for table in ['events', 'patterns', 'states', 'families', 'scenarios', 'constitution_articles']:
        row = query_db(f'SELECT COUNT(*) as c FROM {table}', one=True)
        counts[table] = row['c']
    return jsonify(counts)


# ─── ERROR HANDLERS ──────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# ─── ESTUDO ──────────────────────────────────────────────────────────────────

TRILHAS = [
    {"id": 1, "title": "Entenda o Brasil em 7 Lições", "icon": "🇧🇷", "nivel": "Iniciante",
     "descricao": "Do descobrimento ao presente em 7 passos diretos.",
     "lessons": [
         {"id":1,"title":"Como o Brasil virou colônia","content":"Em 1500, Portugal chegou não como visitante mas como dono. O Tratado de Tordesilhas (1494) já havia dividido o mundo entre Portugal e Espanha — sem consultar ninguém que já vivia aqui. 5 milhões de indígenas foram reduzidos a 300 mil em 200 anos. A colônia servia para UMA coisa: exportar riqueza para Lisboa.","quiz":"Quem assinou o Tratado de Tordesilhas?","quiz_options":["Portugal e Espanha","França e Inglaterra","Brasil e Portugal","Holanda e Espanha"],"quiz_answer":0},
         {"id":2,"title":"Por que a escravidão durou 350 anos","content":"O Brasil foi o maior importador de escravos do mundo: 4,9 milhões de africanos (40% de todo o tráfico atlântico). Durou tanto porque ERA O MODELO ECONÔMICO. Açúcar, ouro, café — tudo feito com trabalho escravo. A abolição em 1888 foi a ÚLTIMA das Américas, após pressão britânica e guerras internas.","quiz":"Quantos africanos foram trazidos para o Brasil?","quiz_options":["500 mil","1 milhão","4,9 milhões","10 milhões"],"quiz_answer":2},
         {"id":3,"title":"A independência que não mudou nada","content":"Em 1822, o FILHO do rei português declarou independência do pai. Sem guerra, sem revolução popular. Os donos das terras continuaram donos. Os escravos continuaram escravos. A estrutura de poder ficou IDÊNTICA — mudou a bandeira, não o sistema.","quiz":"Quem declarou a independência do Brasil?","quiz_options":["O povo brasileiro","Pedro I, príncipe português","José Bonifácio","Tiradentes"],"quiz_answer":1},
         {"id":4,"title":"República: o povo assistiu bestializado","content":"Em 1889, Deodoro da Fonseca e militares derrubaram Pedro II. O jornalista Aristides Lobo descreveu: 'o povo assistiu bestializado, sem entender o que se passava'. A república não veio de eleição, de revolução popular, ou de constituinte. Veio de quartel.","quiz":"Como foi proclamada a República brasileira?","quiz_options":["Eleição popular","Referendo","Golpe militar","Assembleia constituinte"],"quiz_answer":2},
         {"id":5,"title":"Vargas: o pai dos pobres que torturou opositores","content":"Getúlio Vargas (1930-1954) criou a CLT, o salário mínimo, a Petrobras. E também: instaurou ditadura (Estado Novo, 1937), fechou o Congresso, censurou a imprensa, torturou opositores, entregou Olga Benário grávida aos nazistas. O Brasil ainda não decidiu se ele foi herói ou vilão.","quiz":"O que foi o Estado Novo?","quiz_options":["Uma constituição democrática","A ditadura de Vargas (1937-1945)","O período pós-guerra","O governo Dutra"],"quiz_answer":1},
         {"id":6,"title":"A ditadura militar e o milagre que cobrou caro","content":"1964-1985: 21 anos. Tortura de pelo menos 20.000 pessoas, 434 mortos/desaparecidos. E também: crescimento de 10% ao ano (Milagre Econômico, 1968-73). A dívida externa explodiu de $3bi para $100bi. Os juros dessa dívida pagamos até hoje.","quiz":"Quantos anos durou a ditadura militar brasileira?","quiz_options":["10 anos","15 anos","21 anos","30 anos"],"quiz_answer":2},
         {"id":7,"title":"Democracia: o projeto inacabado","content":"A Constituição de 1988 garantiu os direitos mais avançados da história brasileira. 35 anos depois: 33 milhões passam fome, 900 mil presos (maioria negra), desmatamento recorde, educação precária. A Constituição existe — falta implementar.","quiz":"Em que ano foi promulgada a Constituição brasileira atual?","quiz_options":["1985","1986","1988","1990"],"quiz_answer":2},
     ]},
    {"id": 2, "title": "Seus Direitos que Você Não Sabe que Tem", "icon": "⚖️", "nivel": "Básico",
     "descricao": "O que a Constituição garante a você — e como cobrar.",
     "lessons": [
         {"id":1,"title":"Direito à saúde: como usar o SUS de verdade","content":"Art. 196: saúde é direito de todos e dever do Estado. Na prática: você pode exigir qualquer tratamento pelo SUS. Se negado, você pode entrar com mandado de segurança GRATUITAMENTE via Defensoria Pública. Judicialização da saúde funciona — milhares fazem isso por ano.","quiz":"Quem pode te ajudar gratuitamente a exigir tratamento pelo SUS?","quiz_options":["Só advogado particular","Defensoria Pública","OAB","Ninguém"],"quiz_answer":1},
         {"id":2,"title":"Você não é obrigado a falar nada se preso","content":"Art. 5°, LXIII: o preso tem direito a permanecer calado. Isso não é sinal de culpa. Tudo que você disser pode ser usado contra você. Direito a advogado IMEDIATO — se não tiver, Defensoria Pública é obrigada a atender. NUNCA assine nada sem advogado.","quiz":"O que você deve fazer se for preso e não tiver advogado?","quiz_options":["Falar tudo logo","Assinar o depoimento","Pedir a Defensoria Pública","Esperar em silêncio sem pedir nada"],"quiz_answer":2},
         {"id":3,"title":"Mandado de segurança: sua arma contra o Estado","content":"Se um órgão público violar seu direito líquido e certo, você tem 120 dias para entrar com mandado de segurança — sem custas, se for para defender direito individual. A Defensoria Pública pode entrar com você. É rápido: o juiz tem até 10 dias para dar liminar.","quiz":"Qual o prazo para entrar com mandado de segurança?","quiz_options":["30 dias","60 dias","90 dias","120 dias"],"quiz_answer":3},
     ]},
    {"id": 3, "title": "Como Funciona o Dinheiro do Brasil", "icon": "💰", "nivel": "Intermediário",
     "descricao": "Orçamento federal, impostos, dívida pública — sem economês.",
     "lessons": [
         {"id":1,"title":"O orçamento federal em linguagem simples","content":"O Brasil arrecada ~R$ 2,2 trilhões por ano. Onde vai? 45% para juros e dívida pública. 25% para previdência. 15% para saúde e educação. 15% para todo o resto (segurança, infraestrutura, ciência, cultura). Ou seja: 45 centavos de cada real vão para bancos e credores antes de chegar na população.","quiz":"Qual o maior gasto do orçamento federal brasileiro?","quiz_options":["Educação","Saúde","Juros e dívida pública","Previdência"],"quiz_answer":2},
         {"id":2,"title":"Por que o brasileiro paga tanto imposto e recebe tão pouco","content":"Carga tributária: ~33% do PIB (igual à Dinamarca). Mas a Dinamarca tem saúde universal de qualidade, educação gratuita até a universidade, transporte público excelente. O Brasil tem a mesma carga e serviços piores — porque 45% vai pra juros da dívida, e o sistema tributário é regressivo: o pobre paga proporcionalmente mais que o rico.","quiz":"O que significa sistema tributário regressivo?","quiz_options":["Ricos pagam mais","Pobres pagam mais proporcionalmente","Todos pagam igual","Empresas pagam mais"],"quiz_answer":1},
         {"id":3,"title":"A dívida pública: quem deve, para quem, e por quê","content":"Dívida pública bruta: ~R$ 8 trilhões (87% do PIB). Quem é o credor? 60% são fundos de investimento e bancos brasileiros. 20% são fundos de previdência (FGTS, INSS). 20% são estrangeiros. Os juros (Selic) são os mais altos do mundo em termos reais. Por que? Teoria oficial: controle da inflação. Teoria alternativa: transferência de renda do Estado para rentistas.","quiz":"Quem são os principais credores da dívida pública brasileira?","quiz_options":["Países estrangeiros","FMI e Banco Mundial","Fundos e bancos brasileiros","Governo americano"],"quiz_answer":2},
     ]},
]


@app.route('/estudo')
def estudo():
    return render_template('estudo.html', trilhas=TRILHAS)


@app.route('/estudo/<int:trilha_id>')
def estudo_trilha(trilha_id):
    trilha = next((t for t in TRILHAS if t['id'] == trilha_id), None)
    if not trilha:
        return render_template('404.html'), 404
    return render_template('estudo_trilha.html', trilha=trilha)


# ─── GOVERNAR ────────────────────────────────────────────────────────────────

ORCAMENTO_SETORES = [
    {"setor": "Saúde", "atual": 180, "cor": "#E53935"},
    {"setor": "Educação", "atual": 160, "cor": "#1E88E5"},
    {"setor": "Previdência", "atual": 550, "cor": "#8E24AA"},
    {"setor": "Segurança Pública", "atual": 90, "cor": "#F4511E"},
    {"setor": "Infraestrutura", "atual": 70, "cor": "#43A047"},
    {"setor": "Ciência e Tecnologia", "atual": 25, "cor": "#00ACC1"},
    {"setor": "Cultura e Esporte", "atual": 5, "cor": "#FFB300"},
    {"setor": "Meio Ambiente", "atual": 8, "cor": "#2E7D32"},
    {"setor": "Habitação", "atual": 30, "cor": "#6D4C41"},
    {"setor": "Juros da Dívida", "atual": 800, "cor": "#757575"},
]
ORCAMENTO_TOTAL = 2000  # R$ bilhões


@app.route('/governar')
def governar():
    proposals = query_db('SELECT * FROM proposals ORDER BY created_at DESC')
    judgments = query_db('SELECT * FROM judgments ORDER BY id')
    return render_template('governar.html',
                           proposals=proposals,
                           judgments=judgments,
                           setores=ORCAMENTO_SETORES,
                           total=ORCAMENTO_TOTAL)


@app.route('/governar/proposta/votar', methods=['POST'])
def votar_proposta():
    data = request.get_json()
    pid = data.get('id')
    voto = data.get('voto')  # 'yes', 'no', 'abstain'
    col = {'yes': 'votes_yes', 'no': 'votes_no', 'abstain': 'votes_abstain'}.get(voto)
    if not col:
        return jsonify({'error': 'voto inválido'}), 400
    get_db().execute(f'UPDATE proposals SET {col} = {col} + 1 WHERE id = ?', (pid,))
    get_db().commit()
    row = query_db('SELECT votes_yes, votes_no, votes_abstain FROM proposals WHERE id = ?', (pid,), one=True)
    return jsonify(dict(row))


@app.route('/governar/julgamento/votar', methods=['POST'])
def votar_julgamento():
    data = request.get_json()
    jid = data.get('id')
    voto = data.get('voto')  # 'culpado', 'inocente', 'parcial'
    col = {'culpado': 'votes_culpado', 'inocente': 'votes_inocente', 'parcial': 'votes_parcial'}.get(voto)
    if not col:
        return jsonify({'error': 'voto inválido'}), 400
    get_db().execute(f'UPDATE judgments SET {col} = {col} + 1 WHERE id = ?', (jid,))
    get_db().commit()
    row = query_db('SELECT votes_culpado, votes_inocente, votes_parcial FROM judgments WHERE id = ?', (jid,), one=True)
    return jsonify(dict(row))


@app.route('/governar/orcamento/salvar', methods=['POST'])
def salvar_orcamento():
    import uuid
    data = request.get_json()
    session_id = str(uuid.uuid4())
    db = get_db()
    for setor, valor in data.get('alocacoes', {}).items():
        db.execute('INSERT INTO budget_allocations (session_id, setor, valor_bilhoes) VALUES (?,?,?)',
                   (session_id, setor, valor))
    db.commit()
    # Calc averages
    avgs = query_db('SELECT setor, AVG(valor_bilhoes) as avg FROM budget_allocations GROUP BY setor')
    return jsonify({'session_id': session_id, 'medias': {r['setor']: round(r['avg'], 1) for r in avgs}})


# ─── PAINEL DE GOVERNO ───────────────────────────────────────────────────────

PROJECT_TYPES = {"civil":"🏗️ Civil","escola":"🏫 Escola","militar":"⚔️ Militar","tecnologia":"💻 Tecnologia","saude":"🏥 Saúde","infraestrutura":"🛣️ Infraestrutura"}
PROJECT_STATUS = {"proposta":"📋 Proposta","aprovado":"✅ Aprovado","em_execucao":"🔨 Em Execução","pausado":"⏸️ Pausado","concluido":"🏁 Concluído","cancelado":"❌ Cancelado"}
LAW_PHASES = {"proposta":"📋 Proposta","comissao":"🔍 Comissão","votacao":"🗳️ Votação","sancionada":"✅ Sancionada","vetada":"🚫 Vetada","promulgada":"⚖️ Promulgada","arquivada":"📁 Arquivada"}
PROCESS_STATUS = {"abertura":"📂 Abertura","instrucao":"🔍 Instrução","julgamento":"⚖️ Julgamento","sentenca":"📜 Sentença","recurso":"🔄 Recurso","encerrado":"🏁 Encerrado"}
PRIORITIES = {"baixa":"🟢 Baixa","media":"🟡 Média","alta":"🔴 Alta","critica":"🚨 Crítica"}


@app.route('/painel')
def painel():
    ftype = request.args.get('type','')
    fstatus = request.args.get('status','')
    tab = request.args.get('tab','projetos')

    pq = 'SELECT * FROM projects WHERE 1=1'
    pa = []
    if ftype: pq += ' AND type=?'; pa.append(ftype)
    if fstatus: pq += ' AND status=?'; pa.append(fstatus)
    projects = query_db(pq + ' ORDER BY priority DESC, created_at DESC', pa)

    laws = query_db('SELECT * FROM laws ORDER BY created_at DESC')
    processes = query_db('SELECT * FROM processes ORDER BY created_at DESC')

    # Stats
    stats = {
        'projects_total': query_db('SELECT COUNT(*) as c FROM projects', one=True)['c'],
        'projects_exec': query_db("SELECT COUNT(*) as c FROM projects WHERE status='em_execucao'", one=True)['c'],
        'laws_total': query_db('SELECT COUNT(*) as c FROM laws', one=True)['c'],
        'laws_active': query_db("SELECT COUNT(*) as c FROM laws WHERE phase NOT IN ('promulgada','vetada','arquivada')", one=True)['c'],
        'processes_total': query_db('SELECT COUNT(*) as c FROM processes', one=True)['c'],
        'processes_open': query_db("SELECT COUNT(*) as c FROM processes WHERE status NOT IN ('encerrado')", one=True)['c'],
    }

    return render_template('painel.html',
        projects=projects, laws=laws, processes=processes,
        stats=stats, tab=tab,
        project_types=PROJECT_TYPES, project_status=PROJECT_STATUS,
        law_phases=LAW_PHASES, process_status=PROCESS_STATUS,
        priorities=PRIORITIES,
        ftype=ftype, fstatus=fstatus)


@app.route('/painel/registrar', methods=['GET','POST'])
def painel_registrar():
    if request.method == 'POST':
        kind = request.form.get('kind')
        db = get_db()
        if kind == 'project':
            db.execute('''INSERT INTO projects (title,type,description,status,budget_bi,responsible,priority,state)
                          VALUES (?,?,?,?,?,?,?,?)''', (
                request.form['title'], request.form['type'], request.form['description'],
                request.form.get('status','proposta'), float(request.form.get('budget_bi') or 0),
                request.form.get('responsible',''), request.form.get('priority','media'),
                request.form.get('state','')
            ))
        elif kind == 'law':
            db.execute('''INSERT INTO laws (number,title,description,phase,author,type,impact)
                          VALUES (?,?,?,?,?,?,?)''', (
                request.form.get('number',''), request.form['title'], request.form['description'],
                request.form.get('phase','proposta'), request.form.get('author',''),
                request.form.get('type','ordinaria'), request.form.get('impact','')
            ))
        elif kind == 'process':
            db.execute('''INSERT INTO processes (case_number,title,type,description,defendant,charge,status,court)
                          VALUES (?,?,?,?,?,?,?,?)''', (
                request.form.get('case_number',''), request.form['title'], request.form['type'],
                request.form['description'], request.form.get('defendant',''),
                request.form.get('charge',''), request.form.get('status','abertura'),
                request.form.get('court','')
            ))
        db.commit()
        return jsonify({'ok': True})
    return render_template('painel_registrar.html',
        project_types=PROJECT_TYPES, project_status=PROJECT_STATUS,
        law_phases=LAW_PHASES, process_status=PROCESS_STATUS, priorities=PRIORITIES)


@app.route('/painel/votar', methods=['POST'])
def painel_votar():
    data = request.get_json()
    kind = data.get('kind')
    vid = data.get('id')
    voto = data.get('voto')
    db = get_db()
    if kind == 'project':
        col = 'votes_yes' if voto == 'yes' else 'votes_no'
        db.execute(f'UPDATE projects SET {col}={col}+1 WHERE id=?', (vid,))
        db.commit()
        row = query_db('SELECT votes_yes, votes_no FROM projects WHERE id=?', (vid,), one=True)
    else:
        col = 'votes_yes' if voto == 'yes' else 'votes_no'
        db.execute(f'UPDATE laws SET {col}={col}+1 WHERE id=?', (vid,))
        db.commit()
        row = query_db('SELECT votes_yes, votes_no FROM laws WHERE id=?', (vid,), one=True)
    return jsonify(dict(row))


@app.route('/painel/resumo')
def painel_resumo():
    projects = query_db('SELECT * FROM projects ORDER BY priority DESC')
    laws = query_db('SELECT * FROM laws ORDER BY phase')
    processes = query_db('SELECT * FROM processes ORDER BY status')
    budget_total = query_db('SELECT SUM(budget_bi) as s FROM projects WHERE status != "cancelado"', one=True)['s'] or 0
    budget_exec = query_db('SELECT SUM(budget_bi) as s FROM projects WHERE status="em_execucao"', one=True)['s'] or 0
    return render_template('painel_resumo.html',
        projects=projects, laws=laws, processes=processes,
        budget_total=budget_total, budget_exec=budget_exec,
        project_status=PROJECT_STATUS, law_phases=LAW_PHASES,
        process_status=PROCESS_STATUS, priorities=PRIORITIES)


# ─── FEED ────────────────────────────────────────────────────────────────────

@app.route('/feed')
def feed():
    level = request.args.get('level', '')
    state = request.args.get('state', '')
    category = request.args.get('category', '')
    q = 'SELECT * FROM feed_items WHERE 1=1'
    args = []
    if level: q += ' AND level=?'; args.append(level)
    if state: q += ' AND state=?'; args.append(state)
    if category: q += ' AND category=?'; args.append(category)
    q += ' ORDER BY created_at DESC'
    raw_items = query_db(q, args)
    # Parse JSON fields
    items = []
    for it in raw_items:
        d = dict(it)
        try: d['envolvidos'] = json.loads(it['envolvidos'] or '[]')
        except: d['envolvidos'] = []
        try: d['eventos_inerentes'] = json.loads(it['eventos_inerentes'] or '[]')
        except: d['eventos_inerentes'] = []
        items.append(d)
    cats = query_db('SELECT DISTINCT category FROM feed_items ORDER BY category')
    states_list = query_db('SELECT DISTINCT state FROM feed_items WHERE state IS NOT NULL ORDER BY state')
    # Feed também inclui cenários do simulador e denúncias ativas
    sim_items = query_db('SELECT id, title, context, year FROM scenarios ORDER BY id DESC LIMIT 5')
    active_violations = query_db("SELECT id, article_number, description, level, lifecycle_status, created_at FROM violations WHERE lifecycle_status != 'encerrada' ORDER BY created_at DESC LIMIT 5")
    return render_template('feed.html', items=items, cats=cats, states_list=states_list,
                           level=level, state=state, category=category,
                           sim_items=sim_items, active_violations=active_violations)


# ─── CIDADÃO ─────────────────────────────────────────────────────────────────

SKILL_AREAS = {
    "saude": "🏥 Saúde",
    "educacao": "🎓 Educação",
    "engenharia": "⚙️ Engenharia",
    "direito": "⚖️ Direito",
    "administracao": "📊 Administração",
    "ti": "💻 TI / Tecnologia",
    "comunicacao": "📢 Comunicação",
    "campo": "🌾 Campo / Agricultura",
    "seguranca": "🛡️ Segurança",
    "cultura": "🎨 Cultura / Arte"
}

LEVELS = {"bairro": "🏘️ Bairro", "cidade": "🏙️ Cidade", "estado": "🗺️ Estado", "federal": "🇧🇷 Federal", "reserva": "🌿 Reserva"}


@app.route('/cidadao')
def cidadao():
    skill_area = request.args.get('skill', '')
    roles = []
    if skill_area:
        roles = query_db('SELECT * FROM citizen_roles WHERE skill_area=? ORDER BY level', (skill_area,))
    all_roles = query_db('SELECT * FROM citizen_roles ORDER BY skill_area, level')
    assemblies = query_db("SELECT * FROM assemblies ORDER BY created_at DESC LIMIT 10")
    violations_count = query_db('SELECT COUNT(*) as c FROM violations', one=True)['c']
    return render_template('cidadao.html', skill_areas=SKILL_AREAS, levels=LEVELS,
                           roles=roles, all_roles=all_roles, selected_skill=skill_area,
                           assemblies=assemblies, violations_count=violations_count)


@app.route('/cidadao/assembleia', methods=['POST'])
def criar_assembleia():
    data = request.get_json()
    get_db().execute(
        'INSERT INTO assemblies (title, type, level, location, description) VALUES (?,?,?,?,?)',
        (data['title'], data['type'], data['level'], data.get('location', ''), data['description'])
    )
    get_db().commit()
    return jsonify({'ok': True})


@app.route('/cidadao/assembleia/assinar', methods=['POST'])
def assinar_assembleia():
    aid = request.get_json().get('id')
    db = get_db()
    db.execute('UPDATE assemblies SET signatures=signatures+1 WHERE id=?', (aid,))
    db.commit()
    row = query_db('SELECT signatures, min_signatures, status FROM assemblies WHERE id=?', (aid,), one=True)
    new_status = 'aprovada' if row['signatures'] >= row['min_signatures'] else row['status']
    if new_status == 'aprovada':
        db.execute("UPDATE assemblies SET status='aprovada' WHERE id=?", (aid,))
        db.commit()
    return jsonify({'signatures': row['signatures'], 'status': new_status})


# ─── DENÚNCIA CONSTITUCIONAL v3 — Ciclo de vida completo ────────────────────

LIFECYCLE_STAGES = {
    'recebida':      {'label': '📥 Recebida',          'next': 'analisada',    'color': '#78909C'},
    'analisada':     {'label': '🔍 Em Análise',         'next': 'processo',     'color': '#1E88E5'},
    'processo':      {'label': '⚖️ Virou Processo',    'next': 'projeto_lei',  'color': '#F4511E'},
    'projeto_lei':   {'label': '📋 Projeto de Lei',    'next': 'votacao',      'color': '#8E24AA'},
    'votacao':       {'label': '🗳️ Em Votação',        'next': 'encerrada',    'color': '#FFB300'},
    'encerrada':     {'label': '🏁 Encerrada',          'next': None,           'color': '#43A047'},
}


@app.route('/denuncia')
def denuncia():
    violations = query_db('SELECT * FROM violations ORDER BY created_at DESC')
    articles = query_db('SELECT article_number, simple_explanation FROM constitution_articles ORDER BY id')
    # parse lifecycle_log JSON
    vlist = []
    for v in violations:
        vd = dict(v)
        try: vd['lifecycle_log'] = json.loads(v['lifecycle_log'] or '[]')
        except: vd['lifecycle_log'] = []
        try: vd['documentos'] = json.loads(v['documentos'] or '[]')
        except: vd['documentos'] = []
        vd['stage_info'] = LIFECYCLE_STAGES.get(vd.get('lifecycle_status','recebida'), LIFECYCLE_STAGES['recebida'])
        vlist.append(vd)
    return render_template('denuncia.html', violations=vlist, articles=articles, levels=LEVELS,
                           lifecycle_stages=LIFECYCLE_STAGES)


@app.route('/denuncia/<int:vid>')
def denuncia_detalhe(vid):
    v = query_db('SELECT * FROM violations WHERE id=?', (vid,), one=True)
    if not v:
        return render_template('404.html'), 404
    vd = dict(v)
    try: vd['lifecycle_log'] = json.loads(v['lifecycle_log'] or '[]')
    except: vd['lifecycle_log'] = []
    try: vd['documentos'] = json.loads(v['documentos'] or '[]')
    except: vd['documentos'] = []
    vd['stage_info'] = LIFECYCLE_STAGES.get(vd.get('lifecycle_status','recebida'), LIFECYCLE_STAGES['recebida'])
    article = query_db('SELECT * FROM constitution_articles WHERE article_number=?',
                       (vd['article_number'],), one=True)
    total_votes = (vd['votes_approve'] or 0) + (vd['votes_reject'] or 0)
    modality_votes = {
        'audiencia': vd.get('votes_audiencia', 0),
        'reuniao': vd.get('votes_reuniao', 0),
        'assembleia': vd.get('votes_assembleia', 0),
    }
    stages_list = list(LIFECYCLE_STAGES.items())
    current_idx = next((i for i, (k, _) in enumerate(stages_list) if k == vd.get('lifecycle_status','recebida')), 0)
    return render_template('denuncia_detalhe.html', v=vd, article=article,
                           total_votes=total_votes, modality_votes=modality_votes,
                           lifecycle_stages=LIFECYCLE_STAGES, stages_list=stages_list,
                           current_idx=current_idx)


@app.route('/denuncia/nova', methods=['POST'])
def nova_denuncia():
    data = request.get_json()
    import datetime
    log_entry = json.dumps([{'status': 'recebida', 'data': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'nota': 'Denúncia registrada pelo cidadão'}])
    get_db().execute(
        'INSERT INTO violations (article_number, description, level, location, evidence, lifecycle_status, lifecycle_log) VALUES (?,?,?,?,?,?,?)',
        (data['article_number'], data['description'], data['level'],
         data.get('location', ''), data.get('evidence', ''), 'recebida', log_entry)
    )
    get_db().commit()
    count = query_db('SELECT COUNT(*) as c FROM violations WHERE article_number=?',
                     (data['article_number'],), one=True)['c']
    return jsonify({'ok': True, 'total_violations': count})


@app.route('/denuncia/apoiar', methods=['POST'])
def apoiar_denuncia():
    vid = request.get_json().get('id')
    get_db().execute('UPDATE violations SET support_count=support_count+1 WHERE id=?', (vid,))
    get_db().commit()
    row = query_db('SELECT support_count FROM violations WHERE id=?', (vid,), one=True)
    return jsonify({'support_count': row['support_count']})


@app.route('/denuncia/<int:vid>/promover', methods=['POST'])
def promover_denuncia(vid):
    import datetime
    data = request.get_json() or {}
    v = query_db('SELECT * FROM violations WHERE id=?', (vid,), one=True)
    if not v:
        return jsonify({'error': 'Não encontrada'}), 404
    current = v['lifecycle_status'] or 'recebida'
    stage = LIFECYCLE_STAGES.get(current, {})
    next_status = stage.get('next')
    if not next_status:
        return jsonify({'error': 'Já encerrada'}), 400
    # Update log
    try: log = json.loads(v['lifecycle_log'] or '[]')
    except: log = []
    log.append({
        'status': next_status,
        'data': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'nota': data.get('nota', f'Avançou para: {LIFECYCLE_STAGES[next_status]["label"]}')
    })
    # Assign processo/pl numbers if applicable
    extras = {}
    if next_status == 'processo':
        extras['processo_numero'] = data.get('numero', f'PROC-{vid:04d}/2025')
    elif next_status == 'projeto_lei':
        extras['pl_numero'] = data.get('numero', f'PL-{vid:04d}/2025')
    # Add document if provided
    try: docs = json.loads(v['documentos'] or '[]')
    except: docs = []
    if data.get('documento'):
        docs.append({'titulo': data['documento'], 'data': datetime.datetime.now().strftime('%Y-%m-%d'), 'tipo': next_status})
    db = get_db()
    db.execute('UPDATE violations SET lifecycle_status=?, lifecycle_log=?, documentos=? WHERE id=?',
               (next_status, json.dumps(log), json.dumps(docs), vid))
    for col, val in extras.items():
        db.execute(f'UPDATE violations SET {col}=? WHERE id=?', (val, vid))
    db.commit()
    return jsonify({'ok': True, 'new_status': next_status, 'label': LIFECYCLE_STAGES[next_status]['label']})


@app.route('/denuncia/<int:vid>/votar', methods=['POST'])
def votar_denuncia(vid):
    data = request.get_json() or {}
    tipo = data.get('tipo')  # 'approve', 'reject', 'audiencia', 'reuniao', 'assembleia'
    valid = ['approve', 'reject', 'audiencia', 'reuniao', 'assembleia']
    if tipo not in valid:
        return jsonify({'error': 'tipo inválido'}), 400
    col = f'votes_{tipo}'
    get_db().execute(f'UPDATE violations SET {col}={col}+1 WHERE id=?', (vid,))
    get_db().commit()
    row = query_db('SELECT votes_approve,votes_reject,votes_audiencia,votes_reuniao,votes_assembleia FROM violations WHERE id=?', (vid,), one=True)
    return jsonify(dict(row))


# ─── GOVERNANÇA ABERTA — Votações ao vivo, 100% aprovação ───────────────────

import datetime as _dt
import hashlib as _hashlib

GRAVIDADE_CFG = {
    1: {"nome":"Correção",             "emoji":"🟢","duracao_horas":6,   "zona":"bairro", "quorum":5,   "cor":"#43A047","desc":"Bug fix ou texto errado"},
    2: {"nome":"Melhoria",             "emoji":"🟡","duracao_horas":24,  "zona":"cidade", "quorum":10,  "cor":"#FFB300","desc":"Melhoria de interface ou conteúdo"},
    3: {"nome":"Nova Função",          "emoji":"🟠","duracao_horas":72,  "zona":"estado", "quorum":25,  "cor":"#F4511E","desc":"Nova seção ou funcionalidade"},
    4: {"nome":"Mudança Estrutural",   "emoji":"🔴","duracao_horas":168, "zona":"federal","quorum":50,  "cor":"#C62828","desc":"Altera regras ou arquitetura do app"},
    5: {"nome":"Regra Constitucional", "emoji":"⛔","duracao_horas":720, "zona":"todos",  "quorum":100, "cor":"#4A148C","desc":"Muda a governança do próprio app"},
}


def _session_hash(request):
    """Hash anônimo da sessão para evitar duplo voto."""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'anon')
    ua = request.headers.get('User-Agent', '')
    return _hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()[:32]


def _is_voting_open(event):
    try:
        now = _dt.datetime.utcnow()
        inicio = _dt.datetime.fromisoformat(event['inicio'])
        fim = _dt.datetime.fromisoformat(event['fim'])
        return inicio <= now <= fim and event['status'] == 'em_andamento'
    except:
        return False


def _tempo_restante(fim_str):
    try:
        fim = _dt.datetime.fromisoformat(fim_str)
        delta = fim - _dt.datetime.utcnow()
        total = int(delta.total_seconds())
        if total <= 0:
            return "Encerrado"
        d, r = divmod(total, 86400)
        h, r = divmod(r, 3600)
        m, s = divmod(r, 60)
        if d > 0:
            return f"{d}d {h}h {m}m"
        elif h > 0:
            return f"{h}h {m}m {s}s"
        else:
            return f"{m}m {s}s"
    except:
        return "—"


def _check_approval(event):
    """100% SIM + quorum mínimo = aprovada."""
    total = (event['votos_sim'] or 0) + (event['votos_nao'] or 0)
    quorum = event['quorum_minimo'] or 1
    if total < quorum:
        return None  # quorum não atingido
    if (event['votos_nao'] or 0) > 0:
        return False  # qualquer NÃO rejeita
    return True  # 100% SIM + quorum


@app.route('/governanca')
def governanca():
    changes = query_db("""
        SELECT ac.*, ve.id as ve_id, ve.votos_sim, ve.votos_nao, ve.votos_abstencao,
               ve.inicio, ve.fim, ve.status as ve_status, ve.quorum_minimo,
               ve.cidadaos_notificados, ve.resultado as ve_resultado
        FROM app_changes ac
        LEFT JOIN voting_events ve ON ve.change_id = ac.id
        ORDER BY ac.gravidade DESC, ac.created_at DESC
    """)
    changes_list = []
    for c in changes:
        cd = dict(c)
        cd['gcfg'] = GRAVIDADE_CFG.get(c['gravidade'], GRAVIDADE_CFG[1])
        cd['tempo_restante'] = _tempo_restante(c['fim']) if c['fim'] else None
        cd['aberto'] = _is_voting_open(c) if c['fim'] else False
        total_v = (c['votos_sim'] or 0) + (c['votos_nao'] or 0)
        cd['pct_sim'] = round(c['votos_sim'] / total_v * 100, 1) if total_v > 0 else 0
        cd['total_votos'] = total_v
        changes_list.append(cd)

    # Votação ao vivo ativa
    ao_vivo = [c for c in changes_list if c.get('ve_status') == 'em_andamento']
    encerradas = [c for c in changes_list if c.get('ve_status') == 'encerrada']
    propostas = [c for c in changes_list if c['status'] == 'proposta']

    notifs = query_db('SELECT * FROM zone_notifications ORDER BY enviada_em DESC LIMIT 10')
    return render_template('governanca.html',
                           changes=changes_list, ao_vivo=ao_vivo,
                           encerradas=encerradas, propostas=propostas,
                           gravidade_cfg=GRAVIDADE_CFG,
                           notifs=notifs)


@app.route('/governanca/voto/<int:vid>')
def governanca_voto(vid):
    event = query_db('SELECT * FROM voting_events WHERE id=?', (vid,), one=True)
    if not event:
        return render_template('404.html'), 404
    change = query_db('SELECT * FROM app_changes WHERE id=?', (event['change_id'],), one=True)
    gcfg = GRAVIDADE_CFG.get(event['gravidade'], GRAVIDADE_CFG[1])
    aberto = _is_voting_open(event)
    tempo_r = _tempo_restante(event['fim'])
    total_v = (event['votos_sim'] or 0) + (event['votos_nao'] or 0)
    pct_sim = round(event['votos_sim'] / total_v * 100, 1) if total_v > 0 else 0
    quorum_ok = total_v >= (event['quorum_minimo'] or 1)
    aprovacao = _check_approval(event)
    session_hash = _session_hash(request)
    ja_votou = query_db('SELECT voto FROM voting_records WHERE voting_event_id=? AND session_hash=?',
                        (vid, session_hash), one=True)
    notas = []
    try: notas = json.loads(event['notas_ao_vivo'] or '[]')
    except: pass
    notifs = query_db('SELECT * FROM zone_notifications WHERE voting_event_id=? ORDER BY enviada_em DESC', (vid,))
    registros_recentes = query_db("""
        SELECT voto, zona, estado, created_at FROM voting_records
        WHERE voting_event_id=? ORDER BY created_at DESC LIMIT 20
    """, (vid,))
    return render_template('governanca_voto.html',
                           event=dict(event), change=change, gcfg=gcfg,
                           aberto=aberto, tempo_r=tempo_r,
                           total_v=total_v, pct_sim=pct_sim,
                           quorum_ok=quorum_ok, aprovacao=aprovacao,
                           ja_votou=ja_votou, notas=notas,
                           notifs=notifs, registros_recentes=registros_recentes)


@app.route('/governanca/voto/<int:vid>/votar', methods=['POST'])
@rate_limit(max_hits=3, window_secs=300, per='session')   # 3 tentativas por 5min por sessão
def governanca_votar(vid):
    event = query_db('SELECT * FROM voting_events WHERE id=?', (vid,), one=True)
    if not event:
        return jsonify({'error': 'Votação não encontrada'}), 404
    if not _is_voting_open(event):
        return jsonify({'error': 'Votação encerrada ou não iniciada'}), 400

    data = request.get_json() or {}
    voto = data.get('voto')  # 'sim', 'nao', 'abstencao'
    if voto not in ('sim', 'nao', 'abstencao'):
        audit('voto_invalido', f'voting_event/{vid}', f'voto={voto}')
        return jsonify({'error': 'Voto inválido'}), 400

    fp = session_fingerprint()
    zona = data.get('zona', 'federal')
    estado = data.get('estado', '')

    # Impede duplo voto (fingerprint mais robusto)
    ja = query_db('SELECT voto FROM voting_records WHERE voting_event_id=? AND session_hash=?',
                  (vid, fp), one=True)
    if ja:
        audit('duplo_voto_bloqueado', f'voting_event/{vid}', f'zona={zona}')
        return jsonify({'error': 'Você já votou nesta sessão', 'ja_votou': True}), 400

    ts = _dt.datetime.utcnow().isoformat()
    db_conn = get_db()
    db_conn.execute('INSERT INTO voting_records (voting_event_id,session_hash,voto,zona,estado) VALUES (?,?,?,?,?)',
                    (vid, fp, voto, zona, estado))

    col = {'sim': 'votos_sim', 'nao': 'votos_nao', 'abstencao': 'votos_abstencao'}[voto]
    db_conn.execute(f'UPDATE voting_events SET {col}={col}+1 WHERE id=?', (vid,))

    # Verificar se agora está aprovada ou rejeitada
    updated = query_db('SELECT * FROM voting_events WHERE id=?', (vid,), one=True)
    aprovacao = _check_approval(updated)
    novo_status = None
    if aprovacao is True:
        db_conn.execute("UPDATE voting_events SET status='encerrada',resultado='aprovada' WHERE id=?", (vid,))
        db_conn.execute("UPDATE app_changes SET status='aprovada',aprovada_em=datetime('now') WHERE id=?",
                        (updated['change_id'],))
        novo_status = 'aprovada'
        audit('votacao_aprovada', f'voting_event/{vid}', f'unanimidade atingida | {updated["votos_sim"]+1} votos')
    elif aprovacao is False:
        db_conn.execute("UPDATE voting_events SET status='encerrada',resultado='rejeitada' WHERE id=?", (vid,))
        db_conn.execute("UPDATE app_changes SET status='rejeitada',rejeitada_em=datetime('now'),motivo_rejeicao='Voto NÃO recebido — regra dos 100%' WHERE id=?",
                        (updated['change_id'],))
        novo_status = 'rejeitada'
        audit('votacao_rejeitada', f'voting_event/{vid}', 'voto NÃO recebido — regra dos 100%')

    db_conn.commit()

    # Gerar recibo verificável para o cidadão
    recibo = gerar_recibo_voto(vid, fp, voto, ts)

    # Registrar no audit log
    audit('voto_registrado', f'voting_event/{vid}',
          f'voto={voto} zona={zona} recibo={recibo[:8]}...')

    total_v = (updated['votos_sim'] or 0) + (updated['votos_nao'] or 0)
    pct_sim = round(updated['votos_sim'] / total_v * 100, 1) if total_v > 0 else 0
    return jsonify({
        'ok': True,
        'votos_sim': updated['votos_sim'],
        'votos_nao': updated['votos_nao'],
        'votos_abstencao': updated['votos_abstencao'],
        'total': total_v,
        'pct_sim': pct_sim,
        'quorum_ok': total_v >= (updated['quorum_minimo'] or 1),
        'novo_status': novo_status,
        'recibo': recibo,  # cidadão guarda este token para verificação pública
    })


@app.route('/governanca/voto/<int:vid>/live')
def governanca_live(vid):
    """Endpoint de polling para atualização ao vivo."""
    event = query_db('SELECT * FROM voting_events WHERE id=?', (vid,), one=True)
    if not event:
        return jsonify({'error': 'não encontrado'}), 404
    total_v = (event['votos_sim'] or 0) + (event['votos_nao'] or 0)
    pct_sim = round(event['votos_sim'] / total_v * 100, 1) if total_v > 0 else 0
    try: notas = json.loads(event['notas_ao_vivo'] or '[]')
    except: notas = []
    recentes = query_db("""
        SELECT voto, zona, estado, created_at FROM voting_records
        WHERE voting_event_id=? ORDER BY created_at DESC LIMIT 10
    """, (vid,))
    return jsonify({
        'votos_sim': event['votos_sim'] or 0,
        'votos_nao': event['votos_nao'] or 0,
        'votos_abstencao': event['votos_abstencao'] or 0,
        'total': total_v,
        'pct_sim': pct_sim,
        'quorum_minimo': event['quorum_minimo'],
        'quorum_ok': total_v >= (event['quorum_minimo'] or 1),
        'status': event['status'],
        'resultado': event['resultado'],
        'tempo_restante': _tempo_restante(event['fim']),
        'aberto': _is_voting_open(event),
        'notas': notas[-5:],
        'recentes': [dict(r) for r in recentes],
    })


@app.route('/governanca/proposta/nova', methods=['GET', 'POST'])
def governanca_nova_proposta():
    if request.method == 'POST':
        data = request.form
        gravidade = int(data.get('gravidade', 1))
        gcfg = GRAVIDADE_CFG.get(gravidade, GRAVIDADE_CFG[1])
        db_conn = get_db()
        db_conn.execute("""
            INSERT INTO app_changes (titulo,descricao,tipo,gravidade,proponente,github_pr,funcao_afetada,zona,estado)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (data['titulo'], data['descricao'], data.get('tipo','funcao'),
             gravidade, data.get('proponente','Cidadão Anônimo'),
             data.get('github_pr',''), data.get('funcao_afetada',''),
             gcfg['zona'], data.get('estado','')))
        new_id = db_conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Criar votação automática
        now = _dt.datetime.utcnow()
        fim = now + _dt.timedelta(hours=gcfg['duracao_horas'])
        db_conn.execute("""
            INSERT INTO voting_events
            (change_id,titulo,gravidade,zona,estado,inicio,fim,duracao_horas,quorum_minimo,cidadaos_notificados,status,notas_ao_vivo)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (new_id, data['titulo'], gravidade, gcfg['zona'], data.get('estado',''),
             now.strftime('%Y-%m-%d %H:%M:%S'), fim.strftime('%Y-%m-%d %H:%M:%S'),
             gcfg['duracao_horas'], gcfg['quorum'],
             _estimar_cidadaos(gcfg['zona'], data.get('estado','')),
             'em_andamento',
             json.dumps([{"hora": now.strftime('%H:%M'), "nota": f"🚨 Votação aberta. Gravidade {gravidade}: {gcfg['nome']}. Prazo: {gcfg['duracao_horas']}h."}])))
        ve_id = db_conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Notificação automática
        cidadaos = _estimar_cidadaos(gcfg['zona'], data.get('estado',''))
        msg = f"🗳️ Nova votação: {data['titulo']} | Prazo: {gcfg['duracao_horas']}h | soberano.fiosmj.com/governanca/voto/{ve_id}"
        db_conn.execute("""INSERT INTO zone_notifications (voting_event_id,zona,estado,canal,mensagem,cidadaos_estimados,confirmadas)
            VALUES (?,?,?,?,?,?,?)""",
            (ve_id, gcfg['zona'], data.get('estado',''), 'portal', msg, cidadaos, int(cidadaos * 0.68)))
        db_conn.commit()
        return jsonify({'ok': True, 'voting_event_id': ve_id, 'redirect': f'/governanca/voto/{ve_id}'})

    return render_template('governanca_proposta.html', gravidade_cfg=GRAVIDADE_CFG)


# ─── AUDITORIA PÚBLICA ────────────────────────────────────────────────────────

@app.route('/auditoria')
def auditoria():
    """Página pública de auditoria — qualquer cidadão pode verificar a integridade."""
    ok, total, falhas = audit_verify()
    logs = query_db('SELECT id,ts,tipo,recurso,detalhe,hash_proprio FROM audit_log ORDER BY id DESC LIMIT 50')
    rate_blocks = query_db('SELECT * FROM rate_limit_log ORDER BY ts DESC LIMIT 20')
    return render_template('auditoria.html',
                           chain_ok=ok, total_eventos=total, falhas=falhas,
                           logs=logs, rate_blocks=rate_blocks)


@app.route('/auditoria/verificar-recibo', methods=['POST'])
@rate_limit(max_hits=20, window_secs=60, per='ip')
def verificar_recibo():
    """Cidadão cola o token do recibo e verifica se seu voto foi registrado."""
    data = request.get_json() or {}
    token = (data.get('token') or '').strip()[:32]
    if not token:
        return jsonify({'erro': 'Token inválido'}), 400
    row = query_db('SELECT * FROM vote_receipts WHERE receipt_token=?', (token,), one=True)
    if not row:
        return jsonify({'encontrado': False, 'msg': 'Recibo não encontrado na base.'})
    return jsonify({
        'encontrado': True,
        'voting_event_id': row['voting_event_id'],
        'ts': row['ts'],
        'msg': 'Recibo verificado. Seu voto foi registrado com integridade.'
    })


@app.route('/auditoria/chain.json')
@rate_limit(max_hits=10, window_secs=60, per='ip')
def auditoria_chain_json():
    """Exporta o audit log completo para verificação externa."""
    logs = query_db('SELECT id,ts,tipo,recurso,hash_anterior,hash_proprio FROM audit_log ORDER BY id ASC')
    return jsonify([dict(r) for r in logs])


def _estimar_cidadaos(zona, estado=''):
    """Estimativa de cidadãos notificados por zona."""
    estimativas = {
        'bairro': 2500, 'cidade': 85000, 'estado': 1200000,
        'federal': 85000000, 'todos': 215000000
    }
    return estimativas.get(zona, 85000000)


# ─── PREVIDÊNCIA — Simulador de Aposentadoria ────────────────────────────────

REGRAS_APOS = {
    'por_idade': {
        'nome': 'Aposentadoria por Idade',
        'desc': 'Regra principal após Reforma 2019. Mais simples.',
        'requisitos_h': {'idade': 65, 'contrib_anos': 20},
        'requisitos_m': {'idade': 62, 'contrib_anos': 15},
        'calculo': 'Média de 100% das contribuições desde jul/1994. Benefício = 60% + 2% por ano acima do mínimo.',
    },
    'pontos': {
        'nome': 'Regra de Pontos (Transição)',
        'desc': 'Soma da idade + anos de contribuição. Melhor para quem tem muito tempo de serviço.',
        'pontos_h_2024': 99,  # sobe 1 por ano até 105
        'pontos_m_2024': 96,  # sobe 1 por ano até 100
        'contrib_min_h': 35,
        'contrib_min_m': 30,
        'calculo': 'Benefício = 60% + 2% por ano acima do mínimo (35H/30M).',
    },
    'incapacidade': {
        'nome': 'Aposentadoria por Incapacidade Permanente',
        'desc': 'Para quem não consegue mais trabalhar por doença ou acidente.',
        'calculo': '100% da média das contribuições. Exige perícia médica do INSS.',
    },
}


def calcular_aposentadoria(idade, sexo, salario, anos_contrib):
    """Calcula cenários de aposentadoria para o cidadão."""
    results = {}
    eh_homem = sexo.lower() in ('m', 'masculino', 'h')

    # Média do salário de benefício estimada (simplificado)
    # Assume contribuição constante sobre salário atual
    sal_beneficio_base = salario * 0.95  # ajuste para teto/índice

    def calc_beneficio(anos_acima_min, anos_min):
        pct = 0.60 + (max(0, anos_acima_min) * 0.02)
        return min(sal_beneficio_base * pct, 7786.02)  # teto INSS 2024

    # ── Regra 1: Por Idade ───────────────────────────────────────────────────
    idade_ret_1 = 65 if eh_homem else 62
    contrib_min_1 = 20 if eh_homem else 15
    anos_faltam_idade = max(0, idade_ret_1 - idade)
    anos_faltam_contrib_1 = max(0, contrib_min_1 - anos_contrib)
    anos_faltam_1 = max(anos_faltam_idade, anos_faltam_contrib_1)
    anos_acima_1 = max(0, (anos_contrib + anos_faltam_1) - contrib_min_1)
    beneficio_1 = calc_beneficio(anos_acima_1, contrib_min_1)
    results['por_idade'] = {
        'nome': 'Aposentadoria por Idade',
        'anos_faltam': round(anos_faltam_1, 1),
        'idade_aposentadoria': idade + anos_faltam_1,
        'contrib_na_aposentadoria': anos_contrib + anos_faltam_1,
        'beneficio_mensal': round(beneficio_1, 2),
        'requisito_bloqueante': 'Idade' if anos_faltam_idade >= anos_faltam_contrib_1 else 'Contribuição',
        'elegivel_hoje': anos_faltam_1 == 0,
        'alerta': None if beneficio_1 >= 1412 else '⚠️ Benefício próximo ao salário mínimo',
    }

    # ── Regra 2: Pontos (Transição) ──────────────────────────────────────────
    pontos_necessarios = 99 if eh_homem else 96  # 2024
    contrib_min_2 = 35 if eh_homem else 30
    pontos_atuais = idade + anos_contrib

    if pontos_atuais >= pontos_necessarios and anos_contrib >= contrib_min_2:
        anos_faltam_2 = 0
    else:
        deficit_pontos = max(0, pontos_necessarios - pontos_atuais)
        deficit_contrib = max(0, contrib_min_2 - anos_contrib)
        # Cada ano adiciona 2 pontos (1 de idade + 1 de contribuição)
        anos_faltam_2 = max(deficit_pontos / 2, deficit_contrib)

    anos_acima_2 = max(0, (anos_contrib + anos_faltam_2) - contrib_min_2)
    beneficio_2 = calc_beneficio(anos_acima_2, contrib_min_2)
    results['pontos'] = {
        'nome': 'Regra de Pontos (Transição 2024)',
        'pontos_necessarios': pontos_necessarios,
        'pontos_atuais': round(pontos_atuais, 1),
        'anos_faltam': round(anos_faltam_2, 1),
        'idade_aposentadoria': round(idade + anos_faltam_2, 1),
        'contrib_na_aposentadoria': round(anos_contrib + anos_faltam_2, 1),
        'beneficio_mensal': round(beneficio_2, 2),
        'elegivel_hoje': anos_faltam_2 == 0,
        'alerta': '✅ Melhor opção' if beneficio_2 > beneficio_1 else None,
    }

    # ── Melhor opção ──────────────────────────────────────────────────────────
    melhor = 'pontos' if results['pontos']['beneficio_mensal'] > results['por_idade']['beneficio_mensal'] else 'por_idade'
    results[melhor]['alerta'] = '🏆 Melhor benefício'

    # ── Análise financeira vitalícia ──────────────────────────────────────────
    anos_faltam_melhor = results[melhor]['anos_faltam']
    beneficio_melhor = results[melhor]['beneficio_mensal']

    # Total contribuído até aposentadoria
    contribuicao_mensal = salario * 0.14  # alíquota máxima simplificada
    meses_restantes = anos_faltam_melhor * 12
    total_contrib_restante = contribuicao_mensal * meses_restantes
    total_contrib_passado = (anos_contrib * 12) * (salario * 0.12)  # estimado
    total_contribuido = total_contrib_passado + total_contrib_restante

    # Expectativa de vida: 75 (H) / 79 (M)
    exp_vida = 75 if eh_homem else 79
    idade_apos = idade + anos_faltam_melhor
    anos_recebendo = max(0, exp_vida - idade_apos)
    total_recebera = beneficio_melhor * 12 * anos_recebendo

    saldo = total_recebera - total_contribuido

    return {
        'regras': results,
        'melhor_regra': melhor,
        'analise': {
            'total_contribuido': round(total_contribuido, 2),
            'total_recebera': round(total_recebera, 2),
            'saldo_liquido': round(saldo, 2),
            'anos_recebendo': round(anos_recebendo, 1),
            'idade_aposentadoria': round(idade_apos, 1),
            'expectativa_vida': exp_vida,
        }
    }


@app.route('/previdencia')
def previdencia():
    # Dados agregados das simulações
    total_sims = query_db('SELECT COUNT(*) as c FROM inss_simulations', one=True)['c']
    media_saldo = query_db('SELECT AVG(saldo_liquido) as s FROM inss_simulations', one=True)['s'] or 0
    return render_template('previdencia.html',
                           regras=REGRAS_APOS,
                           total_sims=total_sims,
                           media_saldo=round(media_saldo, 2))


@app.route('/previdencia/simular', methods=['POST'])
def previdencia_simular():
    data = request.get_json() or {}
    try:
        idade = int(data.get('idade', 0))
        sexo = data.get('sexo', 'M')
        salario = float(data.get('salario', 0))
        anos_contrib = float(data.get('anos_contrib', 0))
        state_code = data.get('estado', 'SP')
    except (ValueError, TypeError):
        return jsonify({'error': 'Dados inválidos'}), 400

    if not (18 <= idade <= 70) or salario <= 0 or anos_contrib < 0:
        return jsonify({'error': 'Verifique os dados informados'}), 400

    result = calcular_aposentadoria(idade, sexo, salario, anos_contrib)

    # Salvar simulação
    melhor = result['melhor_regra']
    melhor_r = result['regras'][melhor]
    analise = result['analise']
    get_db().execute("""
        INSERT INTO inss_simulations (state_code,idade,sexo,salario,anos_contribuicao,
        regra_ativa,anos_faltam,beneficio_estimado,total_contribuido,total_recebera,saldo_liquido)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (state_code, idade, sexo, salario, anos_contrib,
         melhor, melhor_r['anos_faltam'], melhor_r['beneficio_mensal'],
         analise['total_contribuido'], analise['total_recebera'], analise['saldo_liquido']))
    get_db().commit()

    return jsonify(result)


# ─── COMPRAS DO GOVERNO ───────────────────────────────────────────────────────

MODALIDADES = {
    'pregao_eletronico':      '🖥️ Pregão Eletrônico',
    'dispensa_licitacao':     '⚡ Dispensa de Licitação',
    'tomada_precos':          '📋 Tomada de Preços',
    'concorrencia':           '🏆 Concorrência',
    'concorrencia_internacional': '🌍 Concorrência Internacional',
    'ata_registro_precos':    '📑 Ata de Registro de Preços',
    'inexigibilidade':        '🔒 Inexigibilidade',
}
STATUS_COMPRA = {
    'contratado':    '📝 Contratado',
    'em_execucao':   '🔄 Em Execução',
    'entregue':      '✅ Entregue',
    'pago':          '💰 Pago',
    'cancelado':     '❌ Cancelado',
    'em_auditoria':  '🔍 Em Auditoria',
}


@app.route('/compras')
def compras():
    q = request.args.get('q', '')
    modalidade = request.args.get('modalidade', '')
    status = request.args.get('status', '')
    suspeita = request.args.get('suspeita', '')
    projeto_id = request.args.get('projeto', '')

    query = 'SELECT * FROM government_purchases WHERE 1=1'
    args = []
    if q:
        query += ' AND (produto LIKE ? OR comprador_orgao LIKE ? OR fornecedor LIKE ? OR numero_processo LIKE ?)'
        args += [f'%{q}%']*4
    if modalidade:
        query += ' AND modalidade=?'; args.append(modalidade)
    if status:
        query += ' AND status=?'; args.append(status)
    if suspeita:
        query += ' AND suspeita_irregularidade=1'
    if projeto_id:
        query += ' AND projeto_id=?'; args.append(projeto_id)
    query += ' ORDER BY data_hora DESC'

    purchases = query_db(query, args)

    # Stats
    stats = {
        'total': query_db('SELECT COUNT(*) as c FROM government_purchases', one=True)['c'],
        'valor_total': query_db('SELECT SUM(valor_total) as s FROM government_purchases', one=True)['s'] or 0,
        'suspeitas': query_db('SELECT COUNT(*) as c FROM government_purchases WHERE suspeita_irregularidade=1', one=True)['c'],
        'entregues': query_db("SELECT COUNT(*) as c FROM government_purchases WHERE status IN ('entregue','pago')", one=True)['c'],
    }
    projetos = query_db('SELECT id, title FROM projects ORDER BY title')
    return render_template('compras.html',
                           purchases=purchases, stats=stats,
                           modalidades=MODALIDADES, status_map=STATUS_COMPRA,
                           projetos=projetos,
                           q=q, modalidade=modalidade, status=status,
                           suspeita=suspeita, projeto_id=projeto_id)


@app.route('/compras/<int:pid>')
def compra_detalhe(pid):
    p = query_db('SELECT * FROM government_purchases WHERE id=?', (pid,), one=True)
    if not p:
        return render_template('404.html'), 404
    projeto = None
    if p['projeto_id']:
        projeto = query_db('SELECT * FROM projects WHERE id=?', (p['projeto_id'],), one=True)
    return render_template('compra_detalhe.html', p=p, projeto=projeto,
                           modalidades=MODALIDADES, status_map=STATUS_COMPRA)


# ─── RASTREABILIDADE FISCAL ──────────────────────────────────────────────────

@app.route('/rastreabilidade')
def rastreabilidade():
    taxes = query_db('SELECT * FROM tax_types ORDER BY arrecadacao_anual_bi DESC')
    extraordinary = query_db('SELECT * FROM extraordinary_spending ORDER BY exercicio DESC, valor_bi DESC')
    total_arrecadado = query_db('SELECT SUM(arrecadacao_anual_bi) as s FROM tax_types', one=True)['s'] or 0
    total_extra = query_db('SELECT SUM(valor_bi) as s FROM extraordinary_spending WHERE positivo=1', one=True)['s'] or 0
    total_suspeito = query_db("SELECT SUM(valor_bi) as s FROM extraordinary_spending WHERE positivo=0", one=True)['s'] or 0
    return render_template('rastreabilidade.html',
                           taxes=taxes, extraordinary=extraordinary,
                           total_arrecadado=total_arrecadado,
                           total_extra=total_extra, total_suspeito=total_suspeito)


@app.route('/rastreabilidade/imposto/<codigo>')
def rastreabilidade_imposto(codigo):
    tax = query_db('SELECT * FROM tax_types WHERE codigo=?', (codigo.upper(),), one=True)
    if not tax:
        return render_template('404.html'), 404
    td = dict(tax)
    try: td['destino_legal'] = json.loads(tax['destino_legal'] or '{}')
    except: td['destino_legal'] = {}
    try: td['destino_real'] = json.loads(tax['destino_real'] or '{}')
    except: td['destino_real'] = {}
    # Projetos financiados por este imposto
    links = query_db("""
        SELECT tpl.*, p.title, p.type, p.status, p.progress_pct, p.budget_bi, p.responsible
        FROM tax_project_links tpl
        JOIN projects p ON tpl.project_id = p.id
        WHERE tpl.tax_codigo = ?
        ORDER BY tpl.valor_bi DESC
    """, (codigo.upper(),))
    # Resultados dos projetos ligados
    outcomes = {}
    for l in links:
        pid = l['project_id']
        outcomes[pid] = query_db('SELECT * FROM project_outcomes WHERE project_id=? ORDER BY positivo DESC', (pid,))
    return render_template('rastreabilidade_imposto.html',
                           tax=td, links=links, outcomes=outcomes)


@app.route('/rastreabilidade/gasto-extraordinario/<int:gid>')
def rastreabilidade_gasto(gid):
    gasto = query_db('SELECT * FROM extraordinary_spending WHERE id=?', (gid,), one=True)
    if not gasto:
        return render_template('404.html'), 404
    return render_template('rastreabilidade_gasto.html', gasto=gasto)


@app.route('/api/rastreabilidade/impostos')
def api_impostos():
    taxes = query_db('SELECT codigo, nome, tipo, esfera, arrecadacao_anual_bi, progressivo, regressivo FROM tax_types ORDER BY arrecadacao_anual_bi DESC')
    return jsonify([dict(t) for t in taxes])


# ─── DREX — Gestor Financeiro Soberano ──────────────────────────────────────

def calcular_irpf(renda_mensal):
    """Calcula IRPF mensal com tabela progressiva 2024"""
    renda_anual = renda_mensal * 12
    if renda_anual <= 33888:
        return 0.0
    elif renda_anual <= 45012:
        return renda_mensal * 0.075 - 169.44
    elif renda_anual <= 55976:
        return renda_mensal * 0.15 - 381.44
    elif renda_anual <= 73227:
        return renda_mensal * 0.225 - 662.77
    else:
        return renda_mensal * 0.275 - 1028.87

def calcular_inss(renda_mensal):
    """Calcula INSS com tabela progressiva 2024"""
    aliquotas = [(1412, 0.075), (2666.68, 0.09), (4000.03, 0.12), (7786.02, 0.14)]
    total = 0.0
    prev = 0.0
    for teto, aliq in aliquotas:
        if renda_mensal <= prev:
            break
        faixa = min(renda_mensal, teto) - prev
        total += faixa * aliq
        prev = teto
        if renda_mensal <= teto:
            break
    return min(total, 908.86)  # teto INSS 2024


@app.route('/drex')
def drex():
    states_list = query_db('SELECT code, name, pib_bi, hdi, salario_medio, desemprego_pct, custo_vida_mult FROM state_economy ORDER BY name')
    # Médias coletivas da plataforma
    avg_data = query_db("""
        SELECT state_code, AVG(renda) as avg_renda, AVG(irpf) as avg_irpf,
               AVG(inss) as avg_inss, AVG(impostos_consumo) as avg_consumo,
               AVG(total_impostos) as avg_total, COUNT(*) as total_subs
        FROM drex_submissions GROUP BY state_code
    """)
    coletivo = {r['state_code']: dict(r) for r in avg_data}
    # Alocação coletiva média
    all_subs = query_db("SELECT alocacao FROM drex_submissions ORDER BY created_at DESC LIMIT 1000")
    alocacao_media = {}
    if all_subs:
        for sub in all_subs:
            try:
                aloc = json.loads(sub['alocacao'])
                for k, v in aloc.items():
                    alocacao_media[k] = alocacao_media.get(k, 0) + float(v)
            except: pass
        if alocacao_media:
            n = len(all_subs)
            alocacao_media = {k: round(v/n, 1) for k, v in alocacao_media.items()}
    return render_template('drex.html', states_list=states_list,
                           coletivo=coletivo, alocacao_media=alocacao_media,
                           orcamento_setores=ORCAMENTO_SETORES)


@app.route('/drex/estado/<code>')
def drex_estado(code):
    state = query_db('SELECT * FROM state_economy WHERE code=?', (code.upper(),), one=True)
    if not state:
        return jsonify({'error': 'Estado não encontrado'}), 404
    sd = dict(state)
    try: sd['setores_principais'] = json.loads(state['setores_principais'] or '[]')
    except: sd['setores_principais'] = []
    # Médias do estado
    avg = query_db("""
        SELECT AVG(renda) as avg_renda, AVG(total_impostos) as avg_impostos,
               COUNT(*) as participantes FROM drex_submissions WHERE state_code=?
    """, (code.upper(),), one=True)
    sd['media_renda'] = round(avg['avg_renda'] or 0, 2)
    sd['media_impostos'] = round(avg['avg_impostos'] or 0, 2)
    sd['participantes'] = avg['participantes'] or 0
    return jsonify(sd)


@app.route('/drex/calcular', methods=['POST'])
def drex_calcular():
    data = request.get_json() or {}
    renda = float(data.get('renda', 0))
    state_code = data.get('estado', 'SP').upper()
    alocacao = data.get('alocacao', {})

    if renda <= 0:
        return jsonify({'error': 'Renda inválida'}), 400

    irpf = calcular_irpf(renda)
    inss = calcular_inss(renda)
    # Impostos no consumo: assume 70% da renda líquida vai pra consumo; ~34% de impostos embutidos
    renda_liquida = renda - irpf - inss
    consumo_estimado = renda_liquida * 0.70
    impostos_consumo = consumo_estimado * 0.34  # ICMS+PIS+COFINS+IPI+ISS estimados
    total_impostos = irpf + inss + impostos_consumo

    # Carga tributária efetiva
    carga_pct = (total_impostos / renda * 100) if renda > 0 else 0

    # Custo de vida pelo estado
    state = query_db('SELECT custo_vida_mult, cooperativismo_fed_pct FROM state_economy WHERE code=?',
                     (state_code,), one=True)
    mult = float(state['custo_vida_mult']) if state else 1.0
    coop_pct = float(state['cooperativismo_fed_pct']) if state else 15.0

    # Distribuição dos impostos por setor (estimativa constitucional)
    distribuicao = {
        'Previdência (INSS)': round(inss, 2),
        'Saúde (SUS)': round(total_impostos * 0.08, 2),
        'Educação': round(total_impostos * 0.07, 2),
        'Juros da Dívida': round(total_impostos * 0.36, 2),
        'Segurança Pública': round(total_impostos * 0.04, 2),
        'Infraestrutura': round(total_impostos * 0.03, 2),
        'Outros': round(total_impostos * 0.08, 2),
    }

    # Salvar no DB
    get_db().execute("""
        INSERT INTO drex_submissions (state_code, renda, irpf, inss, impostos_consumo, total_impostos, alocacao)
        VALUES (?,?,?,?,?,?,?)""",
        (state_code, renda, irpf, inss, impostos_consumo, total_impostos, json.dumps(alocacao)))
    get_db().commit()

    # Médias coletivas por estado
    avg = query_db("""
        SELECT AVG(renda) as ar, AVG(total_impostos) as at, COUNT(*) as n
        FROM drex_submissions WHERE state_code=?
    """, (state_code,), one=True)

    return jsonify({
        'renda': round(renda, 2),
        'irpf': round(irpf, 2),
        'inss': round(inss, 2),
        'impostos_consumo': round(impostos_consumo, 2),
        'total_impostos': round(total_impostos, 2),
        'renda_liquida': round(renda_liquida, 2),
        'carga_pct': round(carga_pct, 1),
        'custo_vida_mult': mult,
        'cooperativismo_fed_pct': coop_pct,
        'cooperativismo_valor': round(renda * coop_pct / 100, 2),
        'distribuicao': distribuicao,
        'coletivo': {
            'avg_renda': round(avg['ar'] or 0, 2),
            'avg_impostos': round(avg['at'] or 0, 2),
            'participantes': avg['n'] or 0
        }
    })


# ─── ECONOMIA ────────────────────────────────────────────────────────────────

@app.route('/crimes')
def crimes():
    crime_id = request.args.get('id', '')
    selected = next((c for c in CRIMES_FINANCEIROS if c['id'] == crime_id), None)
    return render_template('crimes.html', crimes=CRIMES_FINANCEIROS, selected=selected)


@app.route('/mercado')
def mercado():
    return render_template('mercado.html', content=MERCADO_CONTENT)


# ─── CONSTITUIÇÃO (override com denúncias) ───────────────────────────────────

@app.route('/constituicao')
def constituicao():
    followed = request.args.get('followed', '')
    if followed == '1':
        articles = query_db('SELECT * FROM constitution_articles WHERE is_followed=1 ORDER BY id')
    elif followed == '0':
        articles = query_db('SELECT * FROM constitution_articles WHERE is_followed=0 ORDER BY id')
    else:
        articles = query_db('SELECT * FROM constitution_articles ORDER BY id')
    # Add violation counts per article
    articles_list = []
    for a in articles:
        count = query_db('SELECT COUNT(*) as c FROM violations WHERE article_number=?',
                         (a['article_number'],), one=True)['c']
        articles_list.append({'article': a, 'violation_count': count})
    return render_template('constituicao.html', articles=articles_list, followed=followed)


@app.route('/static/sw.js')
def service_worker():
    return send_from_directory(app.static_folder, 'sw.js',
                               mimetype='application/javascript')


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("Banco de dados não encontrado. Execute: python database.py")
    app.run(debug=True, host='0.0.0.0', port=5000)
