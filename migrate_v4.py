"""
Brasil Soberano — Migração v4
- tax_types: cada imposto com tipo, base, destino legal e explicação cidadã
- tax_project_links: imposto → projeto → % alocado
- project_outcomes: KPIs e resultados alcançados por projeto
- extraordinary_spending: gastos fora do orçamento com rastreabilidade total
"""
import sqlite3, os, json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brasil_soberano.db')
db = sqlite3.connect(DB_PATH)

# ─── 1. TIPOS DE IMPOSTOS ─────────────────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS tax_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    nome_completo TEXT NOT NULL,
    tipo TEXT NOT NULL,
    esfera TEXT NOT NULL,
    base_calculo TEXT NOT NULL,
    quem_paga_direto TEXT NOT NULL,
    quem_paga_real TEXT NOT NULL,
    aliquota_info TEXT NOT NULL,
    destino_legal TEXT NOT NULL,
    destino_real TEXT NOT NULL,
    arrecadacao_anual_bi REAL DEFAULT 0,
    progressivo INTEGER DEFAULT 0,
    regressivo INTEGER DEFAULT 0,
    explicacao_cidada TEXT NOT NULL,
    como_fiscalizar TEXT NOT NULL
)
""")

tax_types = [
    ("IRPF","Imposto de Renda PF","Imposto de Renda Pessoa Física",
     "direto","federal",
     "Rendimentos do trabalho, capital e atividade rural",
     "Pessoa física com renda acima de R$ 2.824/mês",
     "Trabalhador assalariado (retido na fonte antes de receber)",
     "Tabela progressiva: 0% (até R$2.824) → 7,5% → 15% → 22,5% → 27,5% (acima de R$6.101/mês)",
     json.dumps({"Custeio do governo federal":42,"Educação (FUNDEB)":18,"Saúde (SUS)":15,"Previdência complementar":10,"Outros programas sociais":15}),
     json.dumps({"Juros da dívida pública":36,"Previdência":28,"Custeio (salários, contratos)":20,"Saúde":8,"Educação":5,"Infraestrutura e outros":3}),
     210.5,1,0,
     "É o imposto mais justo: quem ganha mais paga mais. Mas tem um problema: isenção de lucros e dividendos para sócios e donos de empresa. Um CEO que recebe R$ 200k/mês como 'dividendo' paga ZERO de IRPF. Um assalariado de R$ 6k paga 27,5%.",
     "Consulte sua declaração no e-CAC (gov.br/ecac). Veja para onde foi no orçamento federal em portaldatransparencia.gov.br"),

    ("INSS","INSS","Instituto Nacional do Seguro Social",
     "contribuicao","federal",
     "Folha de salários (empregado + empregador)",
     "Empregado (7,5% a 14%) + Empregador (20% sobre toda a folha)",
     "Trabalhador CLT (descontado do salário) + empresa (custo invisível ao trabalhador)",
     "Progressivo por faixas: 7,5% (até R$1.412) → 9% → 12% → 14% (teto: R$908,86/mês). Empregador paga 20% fixo sobre toda a folha + RAT (1-3%)",
     json.dumps({"Aposentadorias e pensões":85,"Auxílio-doença e acidentes":8,"Salário-maternidade":4,"Outros benefícios":3}),
     json.dumps({"Aposentadorias e pensões":85,"Auxílio-doença":8,"Maternidade":4,"Administração do INSS":3}),
     680.0,1,0,
     "O INSS financia a aposentadoria de 37 milhões de brasileiros. É um dos sistemas de distribuição de renda mais eficientes: transfere renda de quem trabalha para quem já trabalhou. O problema é o déficit: arrecada ~R$ 680bi e paga ~R$ 850bi/ano — os R$ 170bi restantes vêm do Tesouro.",
     "Consulte seu CNIS (Cadastro Nacional de Informações Sociais) em meu.inss.gov.br para ver todos os seus registros de contribuição."),

    ("ICMS","ICMS","Imposto sobre Circulação de Mercadorias e Serviços",
     "indireto","estadual",
     "Circulação de mercadorias, energia, combustível, comunicação",
     "Empresa que vende o produto",
     "Consumidor final (embutido no preço — você paga sem ver)",
     "Alíquota varia por estado e produto: 12% (essenciais) a 35% (supérfluos). Energia elétrica: 25-35%. Alimentos básicos: 7-12%.",
     json.dumps({"Saúde (mínimo constitucional)":12,"Educação (mínimo constitucional)":25,"Livre alocação do estado":63}),
     json.dumps({"Livre alocação":55,"Saúde":12,"Educação":25,"Dívida do estado":8}),
     750.0,0,1,
     "O ICMS é o imposto mais injusto do Brasil: é regressivo — o pobre paga proporcionalmente mais que o rico. Uma família que ganha R$ 2k e gasta tudo em consumo paga ~R$ 340/mês em ICMS embutido. Um rico que investe a maioria da renda paga pouco. Energia elétrica taxada em 35% é um absurdo para quem usa pouco.",
     "Veja a SEFAZ do seu estado. Em SP: fazenda.sp.gov.br. Nota Fiscal Paulista devolve parte do ICMS."),

    ("PIS_COFINS","PIS/COFINS","Programa de Integração Social / Contribuição Social",
     "contribuicao","federal",
     "Faturamento bruto das empresas",
     "Empresa (repassado no preço ao consumidor)",
     "Consumidor final (eleva o preço de tudo em ~9%)",
     "PIS: 0,65% (cumulativo) ou 1,65% (não-cumulativo). COFINS: 3% (cumulativo) ou 7,6% (não-cumulativo). Total embutido nos preços: ~9%.",
     json.dumps({"Seguro-Desemprego e Abono Salarial (PIS)":40,"BNDES (PIS parcial)":10,"Saúde (COFINS)":30,"Assistência Social (COFINS)":20}),
     json.dumps({"Seguro-desemprego":35,"BNDES":12,"Saúde":28,"Assistência Social":18,"Administração":7}),
     580.0,0,1,
     "PIS/COFINS somam ~R$ 580bi/ano — mais que o orçamento da saúde. O PIS financia o seguro-desemprego (você recebe se for demitido sem justa causa). A COFINS vai para saúde e assistência social. Mas são embutidos no preço de TUDO que você compra — você paga sem saber.",
     "Toda nota fiscal tem o valor de PIS/COFINS desagregado. Exija a nota e veja quanto paga por produto."),

    ("IOF","IOF","Imposto sobre Operações Financeiras",
     "regulatorio","federal",
     "Operações de crédito, câmbio, seguros e títulos",
     "Pessoa que contrata crédito, seguro ou realiza câmbio",
     "Consumidor de crédito (empréstimo, cartão rotativo, financiamento)",
     "Varia: Crédito pessoal 3%/ano. Cartão rotativo: 3% + IOF diário. Câmbio: 1,1%. Seguro: 7,38%.",
     json.dumps({"Tesouro Nacional (livre alocação)":100}),
     json.dumps({"Juros da dívida":36,"Custeio do governo":40,"Programas sociais":24}),
     60.0,0,0,
     "O IOF é um imposto regulatório — serve para o governo controlar a economia (aumenta o IOF para reduzir crédito, reduz para estimular). Mas também arrecada R$ 60bi/ano. O pior: incide em quem mais precisa de crédito — a pessoa de baixa renda que pega empréstimo paga IOF + juros abusivos.",
     "Veja o IOF no contrato de qualquer empréstimo. É obrigatório constar."),

    ("IPI","IPI","Imposto sobre Produtos Industrializados",
     "indireto","federal",
     "Saída do produto industrializado da fábrica",
     "Indústria (repassado no preço)",
     "Consumidor final (eleva o preço de produtos industrializados)",
     "Varia por produto: 0% (essenciais) a 330% (cigarros). Carro: 7-25%. Bebida alcoólica: 25-47%.",
     json.dumps({"Fundo de Participação dos Municípios":25,"Fundo de Participação dos Estados":25,"Fundo de Exportação":10,"Fundo Amazônia":3,"Tesouro Nacional":37}),
     json.dumps({"Municípios (FPM)":25,"Estados (FPE)":25,"Tesouro/custeio":50}),
     70.0,0,0,
     "25% do IPI vai diretamente para os municípios (FPM) e 25% para os estados. É por isso que cidades pequenas conseguem sobreviver — recebem IPI mesmo sem ter indústria. Carros elétricos têm IPI zerado — política pública via imposto.",
     "Veja a TIPI (Tabela do IPI) na Receita Federal para saber a alíquota de qualquer produto."),

    ("ISS","ISS","Imposto sobre Serviços",
     "indireto","municipal",
     "Prestação de serviços de qualquer natureza",
     "Prestador do serviço (empresa ou profissional autônomo)",
     "Consumidor (embutido no preço do serviço)",
     "Entre 2% (mínimo constitucional) e 5% (máximo). Definido por cada município.",
     json.dumps({"Município — livre alocação":100}),
     json.dumps({"Saúde municipal":15,"Educação municipal":25,"Custeio (servidores)":45,"Infraestrutura":15}),
     110.0,0,0,
     "O ISS fica 100% no seu município. É o imposto sobre a economia de serviços: consulta médica, advogado, salão de beleza, software, consultoria. Municípios grandes (SP, RJ) arrecadam bilhões. Municípios pequenos arrecadam quase nada — por isso dependem do FPM.",
     "Veja o site da Prefeitura. Em SP: sf.prefeitura.sp.gov.br. A NFS-e (Nota Fiscal de Serviços Eletrônica) mostra o ISS de cada serviço."),

    ("IPTU","IPTU","Imposto Predial e Territorial Urbano",
     "direto","municipal",
     "Valor venal do imóvel urbano",
     "Proprietário do imóvel",
     "Proprietário (mas pode ser repassado no aluguel ao inquilino)",
     "Varia por município e valor do imóvel: 0,5% a 1,5%/ano. Municípios podem ter alíquota progressiva.",
     json.dumps({"Município — livre alocação":100}),
     json.dumps({"Saúde":15,"Educação":25,"Manutenção urbana":30,"Segurança":15,"Outros":15}),
     55.0,1,0,
     "O IPTU progressivo é a melhor ferramenta contra especulação imobiliária: terrenos ociosos pagam mais, incentivando uso produtivo. Mas muitas prefeituras não aplicam a progressividade por pressão dos proprietários. O STF já confirmou que IPTU progressivo é constitucional.",
     "Veja o carnê do IPTU ou portal da Prefeitura. Toda propriedade tem valor venal público — consulte se parece justo."),
]

for t in tax_types:
    existing = db.execute("SELECT id FROM tax_types WHERE codigo=?", (t[0],)).fetchone()
    if not existing:
        db.execute("""INSERT INTO tax_types (codigo,nome,nome_completo,tipo,esfera,base_calculo,
            quem_paga_direto,quem_paga_real,aliquota_info,destino_legal,destino_real,
            arrecadacao_anual_bi,progressivo,regressivo,explicacao_cidada,como_fiscalizar)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", t)
print("✅ tax_types: 8 impostos")

# ─── 2. IMPOSTO → PROJETO (ligação) ──────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS tax_project_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tax_codigo TEXT NOT NULL,
    project_id INTEGER NOT NULL,
    pct_alocado REAL DEFAULT 0,
    valor_bi REAL DEFAULT 0,
    exercicio INTEGER DEFAULT 2024,
    nota TEXT
)
""")

tax_project_links = [
    ("IRPF", 1, 8.0, 16.84, 2024, "15% do IRPF vai para saúde — Hospital Regional Nordeste financiado parcialmente"),
    ("IRPF", 3, 5.0, 10.53, 2024, "IRPF financia MEC que gere o Programa Escola Integral"),
    ("INSS", 6, 2.0, 13.60, 2024, "INSS complementa verbas do saneamento (COFINS financiamento BNDES)"),
    ("ICMS", 5, 15.0, 112.50, 2024, "ICMS estadual: mínimo de 12% constitucional para saúde — plataforma TI saúde"),
    ("PIS_COFINS", 6, 5.0, 29.00, 2024, "COFINS via BNDES para saneamento básico universal"),
    ("PIS_COFINS", 3, 3.0, 17.40, 2024, "PIS/COFINS parcela vai para MEC — Escola em Tempo Integral"),
    ("IPI", 7, 25.0, 17.50, 2024, "25% do IPI vai para municípios via FPM — Ferrovia Norte-Sul recebe parcela"),
    ("ISS", 5, 10.0, 11.00, 2024, "ISS de grandes municípios financia saúde pública local — plataforma IA/SUS"),
    ("IPTU", 8, 20.0, 11.00, 2024, "IPTU financia escolas técnicas via FPM e FPE complementação"),
]
for l in tax_project_links:
    db.execute("INSERT INTO tax_project_links (tax_codigo,project_id,pct_alocado,valor_bi,exercicio,nota) VALUES (?,?,?,?,?,?)", l)
print("✅ tax_project_links: 9 ligações")

# ─── 3. RESULTADOS POR PROJETO ────────────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS project_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    indicador TEXT NOT NULL,
    meta TEXT NOT NULL,
    realizado TEXT,
    data_apuracao TEXT,
    status TEXT DEFAULT 'em_acompanhamento',
    fonte TEXT,
    positivo INTEGER DEFAULT 1
)
""")

project_outcomes = [
    # Hospital Regional Nordeste (id=1)
    (1,"Leitos construídos","500 leitos","225 (45% concluído)","2024-12","em_execucao","Ministério da Saúde",1),
    (1,"UTI operacional","80 leitos de UTI","0 (aguardando conclusão)","2024-12","nao_iniciado","MS/ANVISA",0),
    (1,"Municípios atendidos","180 municípios","0 (obra em andamento)","2024-12","em_execucao","DATASUS",0),
    # BR-163 Pará (id=2)
    (2,"Km pavimentados","800 km","256 km (32%)","2024-11","em_execucao","DNIT",1),
    (2,"Redução de custo logístico","30% no trecho","12% (parcial)","2024-11","em_execucao","ILOS",1),
    (2,"Empregos gerados","8.500 diretos","4.200 diretos","2024-11","em_execucao","CAGED",1),
    # Escola Integral (id=3)
    (3,"Alunos em período integral","1.000.000","280.000 (28%)","2024-12","em_execucao","MEC/INEP",1),
    (3,"Escolas convertidas","4.500 escolas","1.260 escolas","2024-12","em_execucao","MEC",1),
    (3,"Refeições servidas/dia","3 refeições por aluno","3 refeições","2024-12","atingido","PNAE/MEC",1),
    # Saneamento Universal (id=6)
    (6,"Pessoas com acesso a água","35 milhões novos","7.7 milhões novos","2024-12","em_execucao","ANA/SNIS",1),
    (6,"Municípios com esgoto tratado","5.570 (todos)","3.890 (70%)","2024-12","em_execucao","SNIS 2024",1),
    (6,"Redução de doenças de veiculação hídrica","60%","22% (parcial)","2024-12","em_execucao","DATASUS",1),
    # Ferrovia Norte-Sul (id=7)
    (7,"Km concluídos","355 km","242 km (68%)","2024-11","em_execucao","VALEC",1),
    (7,"Redução de custo de frete","25% no trecho","18% (estimado)","2024-11","em_execucao","ANTT",1),
    # Escola Técnica (id=8)
    (8,"Novas unidades abertas","50 IFETs","3 (fase inicial)","2024-12","em_execucao","MEC/SETEC",1),
    (8,"Vagas ofertadas/ano","25.000","1.500 (novas unidades)","2024-12","em_execucao","MEC",1),
]
for o in project_outcomes:
    db.execute("INSERT INTO project_outcomes (project_id,indicador,meta,realizado,data_apuracao,status,fonte,positivo) VALUES (?,?,?,?,?,?,?,?)", o)
print("✅ project_outcomes: 16 indicadores")

# ─── 4. GASTOS EXTRAORDINÁRIOS ───────────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS extraordinary_spending (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    tipo TEXT NOT NULL,
    valor_bi REAL NOT NULL,
    exercicio INTEGER NOT NULL,
    origem_recurso TEXT NOT NULL,
    portaria_decreto TEXT,
    orgao_responsavel TEXT NOT NULL,
    descricao TEXT NOT NULL,
    resultado TEXT,
    rastreabilidade TEXT,
    status TEXT DEFAULT 'executado',
    positivo INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
)
""")

extraordinary = [
    ("COVID-19 — Auxílio Emergencial","pandemia",
     293.0,2020,
     "Crédito extraordinário / Emenda Constitucional 106/2020",
     "MP 936/2020, EC 106/2020",
     "Ministério da Cidadania / Caixa Econômica Federal",
     "R$ 293 bilhões pagos a 67 milhões de beneficiários durante a pandemia. Maior programa social da história do Brasil. R$ 600/mês por 5 meses, depois R$ 300. Sem esse gasto, a recessão teria sido catastrófica.",
     "67 milhões de famílias beneficiadas. Consumo das famílias caiu 4,8% (teria caído >15% sem o auxílio). Estimativa: salvou 1,1 milhão de empregos.",
     "Transparência completa em auxilio.caixa.gov.br. CPF consultável. Fraudes investigadas pela CGU.",
     "executado",1),

    ("COVID-19 — Compra de Vacinas","pandemia",
     20.5,2021,
     "Fundo Nacional de Saúde / Crédito Extraordinário",
     "MP 1.026/2021, Portaria MS 69/2021",
     "Ministério da Saúde / FIOCRUZ / Instituto Butantan",
     "R$ 20,5 bilhões para compra de 500 milhões de doses de vacinas COVID-19. Contratos com Pfizer, AstraZeneca, Janssen, Coronavac. Houve CPI do Senado investigando irregularidades na compra da Covaxin.",
     "482 milhões de doses aplicadas. 155 milhões de pessoas com esquema completo. Estima-se 765.000 mortes evitadas pela vacinação.",
     "Contratos no ComprasNet e no Portal COVID do MS. CPI resultou em 80 indiciamentos por Renan Calheiros.",
     "executado",1),

    ("Enchentes RS 2024 — Reconstrução","desastre_natural",
     86.0,2024,
     "Crédito extraordinário / Fundos federais de calamidade",
     "Decreto 11.992/2024, MP 1.262/2024",
     "Ministério da Integração Nacional / Casa Civil",
     "R$ 86 bilhões aprovados pelo Congresso para reconstrução do Rio Grande do Sul após enchentes de maio de 2024 — a maior catástrofe climática da história do Brasil. 169 mortos, 700 mil deslocados, 478 municípios afetados.",
     "Execução: R$ 28 bilhões executados até dez/2024 (32%). 45.000 casas reconstruídas (meta: 120.000). 850 pontes provisórias instaladas.",
     "Painel de monitoramento em reconstrucaors.gov.br. TCE-RS faz auditorias em tempo real. Transferências municipais rastreáveis.",
     "em_execucao",1),

    ("Queimadas e Seca — Emergência Climática 2023","desastre_natural",
     12.8,2023,
     "Reserva de Contingência / Fundo Nacional para Calamidades",
     "Portaria SDR 2.234/2023",
     "IBAMA / Ministério do Meio Ambiente / Defesa Civil",
     "Emergência climática: seca extrema no Norte e Nordeste, incêndios no Pantanal e Cerrado. R$ 12,8 bilhões em operações emergenciais de combate a incêndios, distribuição de água e socorro a populações.",
     "21 milhões de litros de água distribuídos no Amazonas. 4.200 focos de incêndio combatidos no Pantanal. Redução de 28% na área queimada vs 2022.",
     "Relatórios do IBAMA públicos. SIGA — Sistema de Informações Georreferenciadas da Amazônia. INPE divulga dados em tempo real.",
     "executado",1),

    ("Emendas Parlamentares — Suspeitas de Desvio","corrupcao_suspeita",
     8.5,2023,
     "Orçamento Geral da União — Emendas Impositivas",
     "LOA 2023 / Investigações CGU",
     "Ministério da Saúde / CGU / Polícia Federal",
     "CGU identificou indícios de irregularidade em R$ 8,5 bilhões em emendas parlamentares. ONGs sem histórico recebendo contratos milionários. Municípios com obras fantasmas. Emendas 'pix' sem rastreabilidade de destino.",
     "32 parlamentares investigados. 14 contratos suspensos. Devolução de R$ 1,2 bilhão determinada pelo TCU. 8 ONGs fechadas por irregularidades.",
     "Portal da Transparência: portaldatransparencia.gov.br/emendas. Qualquer cidadão pode ver o beneficiário e o valor de cada emenda parlamentar.",
     "em_investigacao",0),

    ("Pandemia — Superfaturamento PPE","corrupcao_suspeita",
     2.1,2020,
     "Crédito extraordinário COVID-19",
     "PGR 1.034/2020 (investigação)",
     "Ministério da Saúde (gestão Pazuello)",
     "CGU e PGR identificaram superfaturamento de R$ 2,1 bilhões na compra de EPIs, respiradores e medicamentos sem eficácia comprovada (cloroquina). Contratos sem licitação com empresas sem experiência.",
     "Ministro investigado. R$ 800 milhões em contratos cancelados. Inquérito aberto no STF. R$ 450 milhões devolvidos.",
     "Relatório CGU publicado em 2021. Inquérito 4.874 no STF. Nomes dos fornecedores no ComprasNet.",
     "em_investigacao",0),

    ("Fundo Constitucional do Norte, Nordeste e Centro-Oeste","desenvolvimento_regional",
     45.0,2024,
     "FNO, FNE, FCO — Fundo Constitucional (art. 159, I, c da CF)",
     "Lei 7.827/1989, LOA 2024",
     "Banco da Amazônia / BNB / Banco do Brasil",
     "3% da arrecadação do IPI e IR são obrigatoriamente destinados ao desenvolvimento das regiões Norte, Nordeste e Centro-Oeste. São créditos com juros baixíssimos para produtores rurais, empresas e municípios.",
     "2024: 185.000 operações de crédito. R$ 45 bilhões emprestados. Inadimplência: 4,2% (menor que mercado). Geração estimada de 320.000 empregos.",
     "Relatórios anuais em fazenda.gov.br/fcco. Operações rastreáveis por CNPJ e CPF do tomador.",
     "executado",1),
]
for e in extraordinary:
    db.execute("""INSERT INTO extraordinary_spending 
        (titulo,tipo,valor_bi,exercicio,origem_recurso,portaria_decreto,orgao_responsavel,
         descricao,resultado,rastreabilidade,status,positivo)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", e)
print("✅ extraordinary_spending: 7 registros")

db.commit()
db.close()
print("\n🇧🇷 Migração v4 concluída!")
