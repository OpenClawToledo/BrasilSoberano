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
    items = query_db(q, args)
    cats = query_db('SELECT DISTINCT category FROM feed_items ORDER BY category')
    states_list = query_db('SELECT DISTINCT state FROM feed_items WHERE state IS NOT NULL ORDER BY state')
    return render_template('feed.html', items=items, cats=cats, states_list=states_list,
                           level=level, state=state, category=category)


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


# ─── DENÚNCIA CONSTITUCIONAL ─────────────────────────────────────────────────

@app.route('/denuncia')
def denuncia():
    violations = query_db('SELECT * FROM violations ORDER BY created_at DESC')
    articles = query_db('SELECT article_number, simple_explanation FROM constitution_articles ORDER BY id')
    return render_template('denuncia.html', violations=violations, articles=articles, levels=LEVELS)


@app.route('/denuncia/nova', methods=['POST'])
def nova_denuncia():
    data = request.get_json()
    get_db().execute(
        'INSERT INTO violations (article_number, description, level, location, evidence) VALUES (?,?,?,?,?)',
        (data['article_number'], data['description'], data['level'],
         data.get('location', ''), data.get('evidence', ''))
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
