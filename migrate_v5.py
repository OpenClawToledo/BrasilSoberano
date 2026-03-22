"""
Brasil Soberano — Migração v5
- inss_simulations: histórico de simulações de aposentadoria
- government_purchases: compras do governo com rastreabilidade total por item
"""
import sqlite3, os, json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brasil_soberano.db')
db = sqlite3.connect(DB_PATH)

# ─── 1. SIMULAÇÕES DE APOSENTADORIA ──────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS inss_simulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT,
    idade INTEGER NOT NULL,
    sexo TEXT NOT NULL,
    salario REAL NOT NULL,
    anos_contribuicao REAL NOT NULL,
    regra_ativa TEXT,
    anos_faltam REAL,
    beneficio_estimado REAL,
    total_contribuido REAL,
    total_recebera REAL,
    saldo_liquido REAL,
    created_at TEXT DEFAULT (datetime('now'))
)
""")
print("✅ inss_simulations: criada")

# ─── 2. COMPRAS DO GOVERNO ───────────────────────────────────────────────────
db.execute("""
CREATE TABLE IF NOT EXISTS government_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_processo TEXT,
    modalidade TEXT NOT NULL,
    produto TEXT NOT NULL,
    descricao_completa TEXT NOT NULL,
    quantidade REAL NOT NULL,
    unidade TEXT NOT NULL,
    valor_unitario REAL NOT NULL,
    valor_total REAL NOT NULL,
    comprador_orgao TEXT NOT NULL,
    comprador_uasg TEXT,
    fornecedor TEXT NOT NULL,
    fornecedor_cnpj TEXT,
    projeto_id INTEGER,
    recurso_orcamentario TEXT NOT NULL,
    necessidade TEXT NOT NULL,
    data_hora TEXT NOT NULL,
    prazo_entrega TEXT,
    data_entrega_real TEXT,
    transporte TEXT,
    fiscal_responsavel TEXT,
    nota_fiscal TEXT,
    status TEXT DEFAULT 'contratado',
    como_validar TEXT NOT NULL,
    portal_url TEXT,
    suspeita_irregularidade INTEGER DEFAULT 0,
    nota_irregularidade TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)
""")

purchases = [
    # 1 - Hospital (projeto 1) — medicamentos
    ("PE-0234/2024","pregao_eletronico",
     "Medicamento — Amoxicilina 500mg (caixas de 21 cápsulas)",
     "Antibiótico de amplo espectro para tratamento de infecções respiratórias e urinárias. Lote hospitalar, embalagem c/ 21 cápsulas de 500mg, validade mín. 24 meses.",
     50000,"caixa",4.80,240000.0,
     "Ministério da Saúde / Hospital Regional Nordeste (NE)",
     "254014",
     "Farmacêutica Brasileira Ltda","12.345.678/0001-99",
     1,"Programa Nacional de Assistência Farmacêutica (IRPF/COFINS)",
     "Estoque mínimo para 500 leitos hospitalares — reposição trimestral conforme protocolo MS",
     "2024-03-15 09:42:00","30 dias","2024-04-10",
     "Caminhão refrigerado (2-8°C) — transportadora LogFrio LTDA",
     "Farm. Dr. Carlos Medeiros CRF-NE 45821",
     "NF-e 45.821.003","entregue",
     "ComprasNet: comprasnet.gov.br/ConsultaLicitacoes/PE-0234-2024 | NF-e: nfe.fazenda.gov.br (chave 35240312345678000199550010004582100)",
     "https://comprasnet.gov.br",0,None),

    # 2 - Hospital — equipamento
    ("DL-0089/2024","dispensa_licitacao",
     "Respirador Mecânico — UTI Adulto (marca Dixtal DX-5020)",
     "Respirador de alto desempenho para UTI adulto, com módulos de ventilação volumétrica, pressométrica e CPAP. Inclui 2 anos de garantia e treinamento de equipe.",
     5,"unidade",87500.0,437500.0,
     "Ministério da Saúde / Fundo Nacional de Saúde",
     "250005",
     "Equipamentos Médicos Nacionais S/A","98.765.432/0001-11",
     1,"Recursos extraordinários COVID + Fundo Nacional de Saúde (COFINS)",
     "Ampliação da capacidade de UTI — 5 novos leitos de terapia intensiva conforme planejamento ministerial",
     "2024-01-20 14:15:00","60 dias","2024-03-22",
     "Frete especial em veículo blindado + técnico de instalação no local — Empresa: MedTrans Brasil",
     "Eng. Biomédico Pedro Santos CREA-NE 112.456",
     "NF-e 12.001.445","entregue",
     "Portal Transparência: portaldatransparencia.gov.br/despesas/por-favorecido/98765432000111 | ComprasNet DL-0089/2024",
     "https://portaldatransparencia.gov.br",0,None),

    # 3 - BR-163 (projeto 2) — asfalto
    ("TP-0512/2024","tomada_precos",
     "CBUQ — Concreto Betuminoso Usinado a Quente (toneladas)",
     "Material asfáltico para pavimentação de 260km da BR-163 no Pará, trecho Santarém-Rurópolis. Especificação DNIT 031/2006. Densidade mín. 2,3 t/m³, resistência à tração >0,65 MPa.",
     85000,"tonelada",420.0,35700000.0,
     "DNIT — Departamento Nacional de Infraestrutura de Transportes",
     "393013",
     "Construtora Amazônica S/A","34.567.890/0001-44",
     2,"LOA 2024 — Programa Nacional de Infraestrutura (IPI+FPM complementação federal)",
     "Pavimentação do trecho crítico da BR-163 PA: único acesso terrestre de 3 municípios durante o inverno amazônico",
     "2024-02-28 10:00:00","180 dias",None,
     "Usina de asfalto local (Santarém-PA) + caminhões tanque basculante 10m³ — 42 viagens/dia",
     "Eng. Civil Ana Paula Lima CREA-PA 98.234",
     "NF-e 78.432.001","em_execucao",
     "DNIT: dnit.gov.br/licitacoes/TP-0512-2024 | SICONV: siconv.planejamento.gov.br | TCU: contas.tcu.gov.br",
     "https://dnit.gov.br",0,None),

    # 4 - Saneamento (projeto 6) — tubulação
    ("CC-1102/2024","concorrencia",
     "Tubo PVC Soldável DN200 (metros lineares) — Rede de Distribuição de Água",
     "Tubulação para rede de distribuição de água potável, DN200mm, pressão nominal PN8, conforme NBR 5647. Para expansão da rede em 47 municípios do Norte do Brasil sem abastecimento.",
     320000,"metro_linear",28.50,9120000.0,
     "Ministério das Cidades / FUNASA",
     "257004",
     "Tigre S/A — Tubos e Conexões","56.789.012/0001-33",
     6,"Marco do Saneamento (PIS/COFINS via BNDES + recursos de emendas aprovadas)",
     "Expansão da rede de água tratada para 47 municípios do Norte sem abastecimento — meta do Marco Legal do Saneamento (Lei 14.026/2020)",
     "2024-04-05 11:30:00","90 dias","2024-07-01",
     "Caminhão carretão (carga longa) — entrega parcelada por lote municipal. Seguro de transporte obrigatório R$ 500k",
     "Eng. Sanitarista Maria Oliveira CREA-AM 67.891",
     "NF-e 34.221.876","entregue",
     "BNDES: bndes.gov.br/operacoes/saneamento2024 | Tribunal de Contas: tcu.gov.br/obras-saneamento | SNIS: app.cidades.gov.br/serieHistorica",
     "https://cidades.gov.br",0,None),

    # 5 - Escola (projeto 3) — merenda
    ("ARP-0318/2024","ata_registro_precos",
     "Feijão Carioca Tipo 1 (sacas de 60kg) — Merenda Escolar",
     "Feijão carioca grão tipo 1, isento de impurezas, saco 60kg, safra 2024. Para Programa Nacional de Alimentação Escolar (PNAE) — 1,2 milhão de alunos em 12 estados.",
     42000,"saca_60kg",185.0,7770000.0,
     "FNDE — Fundo Nacional de Desenvolvimento da Educação",
     "153173",
     "Cooperativa Agrícola do Centro-Oeste Ltda","78.901.234/0001-22",
     3,"PNAE — Programa Nacional de Alimentação Escolar (LOA/IRPF/IPI)",
     "Garantir 3 refeições diárias para 1,2M de alunos em período integral — 180 dias letivos de 2024",
     "2024-01-10 08:00:00","Entrega semanal","Em andamento (200 entregas realizadas)",
     "Caminhão graneleiro + armazém regulador regional — CONAB coordena logística",
     "Nutricionista Beatriz Carvalho CFN 34.567",
     "NF-e série (001-200) 2024","em_execucao",
     "FNDE: fnde.gov.br/programas/pnae | PNAE Transparência: pnae.fnde.gov.br/licitacoes | CONAB: conab.gov.br",
     "https://fnde.gov.br",0,None),

    # 6 - SUSPEITO: Emenda parlamentar — consultoria
    ("TP-0998/2023","inexigibilidade",
     "Consultoria em Gestão Pública — Capacitação de Servidores",
     "Serviços de consultoria para capacitação em gestão pública, planejamento estratégico e governança para 50 servidores municipais. Duração: 40h. Sem produto físico entregável.",
     1,"serviço",1800000.0,1800000.0,
     "Prefeitura Municipal de Cidade Pequena-MG (Emenda Parlamentar Deputado X)",
     "987654",
     "Instituto de Gestão e Excelência Pública LTDA ME","11.222.333/0001-55",
     None,"Emenda Parlamentar Impositiva 2023 (LOA — dotação parlamentar R$ 1,8M)",
     "Capacitação de servidores municipais conforme indicação parlamentar",
     "2023-11-15 09:00:00","30 dias","2023-12-10",
     "Serviço presencial — não aplicável transporte de produto",
     "Assessor municipal João da Silva (sem formação declarada)",
     "NF-e 00.000.999","pago",
     "Portal Transparência Municipal: transparencia.cidadepequena.mg.gov.br | CGU: cgu.gov.br/emendas | SICONV: plataformamaisbrasil.gov.br",
     "https://portaldatransparencia.gov.br",1,
     "⚠️ Instituto criado há 8 meses. Sócio é cunhado do vereador que articulou a emenda. Nenhum servidor comprova ter recebido o treinamento. CGU abriu processo de prestação de contas."),

    # 7 - Defesa — superfaturamento suspeito
    ("CC-0445/2022","concorrencia",
     "Colete Balístico Nível III-A (unidades) — Polícia Federal",
     "Colete balístico para proteção de agentes da PF em campo. Proteção NIJ Nível III-A. Inclui placa dianteira e traseira, ajuste ergonômico, certificação INMETRO.",
     3000,"unidade",4200.0,12600000.0,
     "Ministério da Justiça / Polícia Federal",
     "200344",
     "Equipamentos de Segurança Brasil S/A","22.333.444/0001-66",
     None,"LOA 2022 — Segurança Pública (IPI federal + dotação orçamentária)",
     "Reposição e expansão do estoque de EPIs da PF — 3.000 agentes de campo",
     "2022-08-20 14:00:00","45 dias","2022-10-05",
     "Frete seguro — empresa Transportadora Segura Ltda, veículo rastreado, escolta policial",
     "Major PM Rafael Moura (fiscal designado pela PF)",
     "NF-e 88.432.100","pago",
     "CGU: cgu.gov.br/assuntos/auditoria-e-fiscalizacao/processos | ComprasNet CC-0445/2022 | TCU: tcu.gov.br",
     "https://comprasnet.gov.br",1,
     "⚠️ SINAPI indica preço de mercado: R$ 1.800-2.500/colete. Valor pago: R$ 4.200 (68-133% acima). TCU abriu processo de auditoria em 2023. Empresa ganhou 7 contratos com o mesmo órgão nos últimos 3 anos."),

    # 8 - Vacinas (COVID)
    ("CC-0002/2021","concorrencia_internacional",
     "Vacina COVID-19 BioNTech/Pfizer — BNT162b2 (doses)",
     "Vacina COVID-19 mRNA, dose de 0,3mL, frasco multidose de 6 doses. Armazenamento -90°C a -60°C. 100 milhões de doses para o PNI — Programa Nacional de Imunização.",
     100000000,"dose",7.80,780000000.0,
     "Ministério da Saúde / Fundo Nacional de Saúde",
     "250005",
     "Pfizer Brasil Ltda","43.215.558/0001-00",
     None,"Crédito Extraordinário COVID-19 (EC 106/2020) — recursos do Tesouro Nacional",
     "Imunização em massa contra COVID-19 — meta: 160M de pessoas com 2 doses até dez/2021",
     "2021-03-01 00:00:00","Entrega mensal","Concluído (100M doses em 18 meses)",
     "Avião cargueiro (-80°C) → Aeroporto de Guarulhos → câmaras frigoríficas ANVISA → distribuição aos estados em caixas de isopor ultra-frio (-80°C)",
     "Dr. Eder Gatti CRM-SP 145.230 (Diretor PNI/MS)",
     "NF-e internacional (contrato bilateral)","entregue",
     "Portal COVID/MS: covid.saude.gov.br | SI-PNI: rnds.saude.gov.br | Compras abertas: opencovidbrazil.com | TCU: tcu.gov.br/covid",
     "https://covid.saude.gov.br",0,None),

    # 9 - Ferrovia (projeto 7) — trilhos
    ("CC-0701/2023","concorrencia",
     "Trilho Ferroviário — Perfil TR-57 (toneladas)",
     "Trilho de aço laminado perfil TR-57kg/m, aço grau 900A, comprimento 25m por peça, conforme ABNT NBR 7590. Para trecho central da Ferrovia Norte-Sul (GO), 242km concluídos.",
     18500,"tonelada",5800.0,107300000.0,
     "VALEC Engenharia, Construções e Ferrovias S/A",
     "393014",
     "Gerdau S/A — Aços Longos","33.611.500/0001-19",
     7,"Programa de Investimento em Logística (PIL) — LOA 2023 (IPI+IRPF)",
     "Construção de 355km da Ferrovia Norte-Sul, trecho Anápolis-Ouro Verde de Goiás — redução de custo logístico do agronegócio",
     "2023-06-15 10:00:00","30 dias/lote","Em andamento (14 lotes entregues)",
     "Trem de carga Gerdau Ouro Branco→Anápolis + ponte rolante para descarga de trilhos na obra",
     "Eng. Ferroviário Lucas Torres CREA-GO 89.123",
     "NF-e série mensal","em_execucao",
     "VALEC: valec.gov.br/noticias/ferrovia-norte-sul | ANTT: antt.gov.br | TCU: contas.tcu.gov.br/ferrovias",
     "https://valec.gov.br",0,None),

    # 10 - Escolas técnicas (projeto 8) — obras
    ("TP-0211/2025","tomada_precos",
     "Construção Civil — Bloco Didático IFET 2.500m² (obras e instalações)",
     "Construção de bloco didático com 12 salas de aula, 4 laboratórios, biblioteca e administração, conforme projeto-padrão MEC/SETEC. Área construída: 2.500m². Execução em 18 meses.",
     1,"obra",8200000.0,8200000.0,
     "MEC / Secretaria de Educação Profissional e Tecnológica (SETEC)",
     "153180",
     "Construtora Educação & Progresso Ltda","55.666.777/0001-88",
     8,"LOA 2025 — Expansão da Rede Federal de Educação (IPI municipal + emenda coletiva aprovada)",
     "Construção da 1ª unidade do IFET São Mateus do Sul (PR) — 500 vagas em cursos técnicos de mecânica, elétrica e agroindustrial",
     "2025-01-20 09:00:00","540 dias",None,
     "Insumos via fornecedores locais (cimento, aço, tijolos) — obra in loco em terreno doado pelo município",
     "Eng. Civil Rodrigo Pinto CREA-PR 78.901",
     "NF-e por medição mensal","em_execucao",
     "SIMEC: painel.mec.gov.br/obras | ComprasNet TP-0211/2025 | TCU: tcu.gov.br/obras-educacao",
     "https://simec.mec.gov.br",0,None),
]

for p in purchases:
    db.execute("""INSERT INTO government_purchases (
        numero_processo,modalidade,produto,descricao_completa,quantidade,unidade,
        valor_unitario,valor_total,comprador_orgao,comprador_uasg,fornecedor,fornecedor_cnpj,
        projeto_id,recurso_orcamentario,necessidade,data_hora,prazo_entrega,
        data_entrega_real,transporte,fiscal_responsavel,nota_fiscal,status,
        como_validar,portal_url,suspeita_irregularidade,nota_irregularidade
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", p)

print(f"✅ government_purchases: {len(purchases)} compras")

db.commit()
db.close()
print("\n🇧🇷 Migração v5 concluída!")
