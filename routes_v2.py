"""
Brasil Soberano v2 — Rotas adicionais
Importado por app.py
"""
from flask import render_template, request, jsonify, g
import hashlib, json

CRIMES_FINANCEIROS = [
    {
        "id": "superfaturamento",
        "icon": "🏗️",
        "nome": "Superfaturamento em Obras",
        "como_funciona": "Uma obra pública tem custo real de R$ 10 milhões. A empresa contratada emite nota de R$ 18 milhões. A diferença (R$ 8 milhões) é dividida entre o empresário e o agente público que aprovou. Isso é possível porque: (1) o orçamento é feito pela própria empresa; (2) a fiscalização é fraca ou corrompida; (3) não existe engenheiro independente verificando.",
        "quem_paga": "Você — via impostos. Cada R$ 1 desviado é R$ 1 a menos em saúde, escola ou asfalto.",
        "custo_pais": "Tribunal de Contas da União estima R$ 200 bilhões/ano em obras superfaturadas no Brasil.",
        "como_identificar": [
            "Preço acima de 30% do SINAPI (tabela de preços do governo)",
            "Mesma empresa ganha sempre as licitações do mesmo gestor",
            "Obra entregue com qualidade muito abaixo do contratado",
            "Aditivos contratuais frequentes (aumentam o valor após licitação)"
        ],
        "o_que_fazer": "Denuncie no TCU (tcu.gov.br), CGU (gov.br/cgu), MP ou portal da transparência do município.",
        "solucao": "BIM (Building Information Modeling) obrigatório para todas as obras — software que calcula o custo real automaticamente. Auditoria independente por engenheiros civis sorteados. Publicação em tempo real de todos os gastos com fotos geolocalizadas.",
        "nivel": "federal"
    },
    {
        "id": "lavagem",
        "icon": "🧺",
        "nome": "Lavagem de Dinheiro",
        "como_funciona": "Dinheiro ilegal (corrupção, tráfico, fraude) precisa 'parecer limpo' para ser gasto. As 3 fases clássicas: (1) COLOCAÇÃO — dinheiro entra no sistema financeiro via empresas de fachada, apostas, imóveis; (2) OCULTAÇÃO — transferências entre contas, paraísos fiscais, empresas offshore; (3) INTEGRAÇÃO — dinheiro 'limpo' reaparece como lucro de empresa legítima.",
        "quem_paga": "Toda a sociedade — mercado imobiliário inflacionado, concorrência desleal, economia distorcida.",
        "custo_pais": "ENCCLA estima que o Brasil lava R$ 150-200 bilhões por ano (2-3% do PIB).",
        "como_identificar": [
            "Empresa sem funcionários ou atividade real com faturamento alto",
            "Pessoa física compra imóvel caro em espécie sem renda declarada compatível",
            "Transferências para paraísos fiscais (Cayman, BVI, Luxemburgo)",
            "Restaurante ou loja sempre 'cheio' mas nunca lucrativo — fachada para lavar"
        ],
        "o_que_fazer": "Denuncie ao COAF (Conselho de Controle de Atividades Financeiras) em gov.br/coaf. O COAF é obrigado a investigar qualquer denúncia de movimentação atípica.",
        "solucao": "Cadastro de beneficiários finais obrigatório para toda empresa (quem são os donos reais). Taxação de transações acima de R$ 50k. Fim do dinheiro vivo para imóveis e carros.",
        "nivel": "federal"
    },
    {
        "id": "emendas",
        "icon": "💼",
        "nome": "Desvio de Emendas Parlamentares",
        "como_funciona": "Cada deputado tem R$ 25 milhões/ano para 'emendar' no orçamento. Na prática: o parlamentar indica onde o dinheiro vai (para uma ONG, município, entidade). Essa entidade é muitas vezes controlada pelo próprio parlamentar ou aliados. A ONG faz uma obra ou serviço fictício. O dinheiro volta ao parlamentar como 'doação' ou através de empresas de fachada.",
        "quem_paga": "O contribuinte. São R$ 50 bilhões/ano em emendas parlamentares com fiscalização mínima.",
        "custo_pais": "CGU identificou que 30-40% das emendas têm indícios de irregularidade.",
        "como_identificar": [
            "ONG criada há menos de 1 ano recebe emenda milionária",
            "ONG no endereço residencial do vereador ou parente do deputado",
            "Serviço contratado (capacitação, consultoria) sem produto tangível",
            "Mesmo CNPJ recebe emendas de múltiplos parlamentares"
        ],
        "o_que_fazer": "Pesquise em portaldatransparencia.gov.br quem são os beneficiários das emendas do seu deputado. Denuncie ao MP Federal ou CGU.",
        "solucao": "Emendas impositivas com execução obrigatória em obras físicas rastreáveis. Proibição de emendas para ONGs sem 5 anos de existência. Publicação em tempo real com fotos.",
        "nivel": "federal"
    },
    {
        "id": "sonegacao",
        "icon": "📋",
        "nome": "Sonegação Fiscal",
        "como_funciona": "Empresa declara faturamento menor ao Fisco, esconde receitas, usa notas falsas de despesa para reduzir lucro tributável, mantém funcionários 'por fora' (sem registro). Pessoa física omite rendimentos, usa empresa no exterior para esconder patrimônio. Custo: governo arrecada menos, os honestos pagam mais para compensar.",
        "quem_paga": "Todos os contribuintes que pagam em dia — e quem usa os serviços públicos subfinanciados.",
        "custo_pais": "Receita Federal estima R$ 500 bilhões/ano em sonegação no Brasil.",
        "como_identificar": [
            "Empresa grande que paga pouco imposto e sempre está no Simples",
            "Funcionário sem carteira assinada em empresa formal",
            "Nota fiscal 'por fora' com desconto",
            "Patrimônio do dono claramente incompatível com o faturamento declarado"
        ],
        "o_que_fazer": "Denuncie à Receita Federal (receita.fazenda.gov.br/Contribuintes/Denuncias). Exija nota fiscal sempre — cada NF emitida é um imposto que o governo recebe.",
        "solucao": "Nota Fiscal Eletrônica obrigatória em todos os setores. NF-e integrada com CPF do consumidor (como em SP). Imposto automático retido na fonte para todas as transações.",
        "nivel": "federal"
    },
    {
        "id": "licitacao",
        "icon": "🤝",
        "nome": "Licitação Fraudulenta",
        "como_funciona": "A licitação deveria escolher a proposta mais barata e melhor. Na fraude: o edital é escrito com especificações técnicas que só uma empresa específica atende. Ou: empresas 'concorrentes' combinam os preços antes (cartel). Ou: a empresa vencedora é escolhida antes da licitação, e as outras empresas apresentam propostas maiores propositalmente.",
        "quem_paga": "O governo — que paga mais caro. Logo, o contribuinte.",
        "custo_pais": "CADE (órgão antitruste) já puniu cartéis que custaram R$ 50 bilhões ao erário.",
        "como_identificar": [
            "Edital com especificação técnica muito específica (número de série de produto)",
            "Pouquíssimas empresas participam da licitação",
            "Empresa vencedora sempre a mesma nos últimos anos",
            "Preço muito próximo do teto máximo (não houve competição real)"
        ],
        "o_que_fazer": "Consulte as licitações do seu município em comprasnet.gov.br. Denuncie ao CADE ou MP.",
        "solucao": "Plataforma nacional única de licitações com IA identificando padrões suspeitos. Separação total entre quem especifica e quem compra. Licitações abertas internacionalmente acima de R$ 10 milhões.",
        "nivel": "federal"
    },
    {
        "id": "previdencia",
        "icon": "👴",
        "nome": "Fraude Previdenciária",
        "como_funciona": "Pensões por morte para pessoas vivas. Benefícios por incapacidade para pessoas saudáveis. 'Laranjeiras': pessoa sem contribuição recebe benefício via fraude de documentos. Servidores aposentados com salário de ativo. Benefícios acumulados ilegalmente.",
        "quem_paga": "O INSS — que já tem déficit. Trabalhadores que contribuem e não receberão.",
        "custo_pais": "CGU estima R$ 10-15 bilhões/ano em fraudes previdenciárias.",
        "como_identificar": [
            "Parente morto ainda 'recebendo' pensão",
            "Pessoa saudável com benefício por incapacidade",
            "Servidor público acumulando dois salários integrais"
        ],
        "o_que_fazer": "Denuncie pelo 135 (Central de Atendimento do INSS) ou no portal Meu INSS.",
        "solucao": "Biometria facial obrigatória para recebimento. Cruzamento automático de dados do INSS com cartório (mortes), CNIS (contribuições) e SESPREV.",
        "nivel": "federal"
    },
]

MERCADO_CONTENT = {
    "titulo": "Mercado Livre como Ferramenta — O Modelo Soberano",
    "intro": "O Brasil tem uma das maiores reservas de recursos naturais do mundo. A questão não é SE o mercado deve existir — mas A SERVIÇO DE QUEM ele opera.",
    "setores_estrategicos": [
        {"setor": "Energia (petróleo, gás, solar, eólica)", "justificativa": "Recurso finito e essencial. Privatizar é entregar soberania.", "modelo": "Empresa pública com participação cidadã (ações para todos os brasileiros)"},
        {"setor": "Água e Saneamento", "justificativa": "Direito humano básico. Mercado não distribui água para quem não pode pagar.", "modelo": "Monopólio público universal + concessão privada com metas rígidas"},
        {"setor": "Telecomunicações", "justificativa": "Infraestrutura estratégica. Quem controla a fibra controla a informação.", "modelo": "Rede pública neutra + provedores privados competindo no acesso"},
        {"setor": "Saúde Pública", "justificativa": "Mercado em saúde gera iniquidade: rico se trata, pobre morre.", "modelo": "SUS universal + planos privados complementares"},
        {"setor": "Educação Básica", "justificativa": "Educação diferenciada por renda perpetua desigualdade por gerações.", "modelo": "Escola pública de qualidade universal + privada regulada"},
        {"setor": "Defesa e Segurança", "justificativa": "Violência não pode ser negócio. Segurança privada é falha do Estado.", "modelo": "Monopólio estatal com controle civil"},
    ],
    "mercado_livre": [
        {"setor": "Indústria e Manufatura", "regra": "Livre, mas com cota de conteúdo nacional mínimo e proteção tarifária estratégica"},
        {"setor": "Comércio Interno", "regra": "Livre, com regulação antimonopólio forte (sem megacorporações dominantes)"},
        {"setor": "Tecnologia e Inovação", "regra": "Incentivado, com transferência de tecnologia obrigatória para investimento estrangeiro"},
        {"setor": "Agronegócio", "regra": "Livre, mas com limite de propriedade (teto de 500 ha por CPF) e cotas de produção nacional"},
        {"setor": "Turismo e Cultura", "regra": "Livre, com proteção do patrimônio natural e cultural"},
        {"setor": "Serviços Financeiros", "regra": "Regulado, com banco público forte como âncora e limite de spreads bancários"},
    ],
    "modelo_china": "A China usa o mercado como INSTRUMENTO: abre para capital estrangeiro em setores não-estratégicos, exige transferência de tecnologia, usa os lucros para financiar o setor público. O mercado trabalha para o Estado, não o contrário. O Brasil pode fazer o mesmo: atrair investimento externo COM condições (empregar locais, usar insumos nacionais, pagar impostos aqui).",
    "lucro_publico": "Empresas do setor estratégico deveriam distribuir dividendos diretamente aos cidadãos — como o Alaska Permanent Fund (EUA) distribui dividendos do petróleo para todos os residentes do Alaska."
}
