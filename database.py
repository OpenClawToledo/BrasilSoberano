"""
Brasil Soberano — Database initialization and seed
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brasil_soberano.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    year INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    geopolitical_context TEXT,
    pattern_id INTEGER,
    state TEXT,
    key_figures TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    modern_equivalent TEXT,
    lesson TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS states (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    colonial_origin TEXT,
    main_revolts TEXT,
    economic_history TEXT,
    connection_to_others TEXT
);

CREATE TABLE IF NOT EXISTS families (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    origin TEXT NOT NULL,
    period TEXT NOT NULL,
    activity TEXT NOT NULL,
    modern_status TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER,
    context TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    what_happened TEXT NOT NULL,
    consequence TEXT NOT NULL,
    lesson TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS constitution_articles (
    id INTEGER PRIMARY KEY,
    article_number TEXT NOT NULL,
    official_text TEXT NOT NULL,
    simple_explanation TEXT NOT NULL,
    is_followed INTEGER DEFAULT 0,
    reality_check TEXT
);
"""

def seed_patterns(db):
    patterns = [
        (1, "O pobre paga, o rico negocia",
         "Em toda a história do Brasil, quando uma revolta falha ou uma crise estoura, os pobres são punidos e os ricos são anistiados. De Tiradentes (enforcado enquanto os ricos foram exilados) até hoje (pobre preso por roubar comida, rico com habeas corpus).",
         "Sistema carcerário: 67% negros. Foro privilegiado para políticos. Prisão em 2ª instância só para pobre.",
         "Desconfie de qualquer sistema onde a punição depende da classe social do acusado."),
        (2, "Negro luta, branco colhe",
         "Negros e indígenas lutaram em TODAS as guerras e revoltas do Brasil. Sempre foram prometidos liberdade ou reconhecimento. Sempre foram traídos depois. Lanceiros Negros massacrados em Porongos, João Cândido torturado após Revolta da Chibata, soldados negros reescravizados após Guerra do Paraguai.",
         "Trabalho precarizado: 92% das empregadas domésticas são negras. Negros são maioria no trabalho informal. Apps de entrega: maioria negra.",
         "Quando prometem igualdade em troca de trabalho ou luta, exija a igualdade ANTES, não depois."),
        (3, "Promessa e traição",
         "Toda grande mudança no Brasil veio acompanhada de promessas que foram quebradas. Abolição sem terra. República sem democracia. Constituição de 1988 sem reforma agrária. Cada governo promete mudança e entrega mais do mesmo.",
         "Reformas prometidas que nunca vêm: tributária, agrária, política, urbana. Cada eleição repete as mesmas promessas.",
         "Não aceite promessa — exija garantia. Lei escrita é melhor que discurso bonito."),
        (4, "O salvador da pátria",
         "Sempre que o Brasil entra em crise, aparece um 'homem forte' que promete resolver tudo. Pedro I, Deodoro, Vargas, Médici, e outros. O povo aplaude, entrega o poder, e depois descobre que o salvador virou ditador.",
         "Discurso de 'outsider' político que vai 'limpar tudo'. Messianismo político em todas as eleições.",
         "Nenhuma pessoa resolve os problemas de 215 milhões. Desconfie de quem promete solução simples para problemas complexos."),
        (5, "Riqueza exportada, miséria importada",
         "Desde 1500, o Brasil exporta riqueza bruta e importa miséria. Pau-brasil, açúcar, ouro, café, borracha, soja, minério — tudo sai cru e volta como produto caro. O lucro fica fora. Os danos ficam aqui.",
         "Brasil exporta soja e importa fertilizante. Exporta minério de ferro e importa aço. Exporta petróleo cru e importa gasolina refinada.",
         "Agregar valor dentro do país é a diferença entre colônia e nação soberana."),
        (6, "Dividir para conquistar",
         "A elite sempre dividiu o povo para manter o poder. Norte vs Sul, negro vs branco, rural vs urbano, estado vs estado. Enquanto o povo briga entre si, ninguém olha para cima.",
         "Preconceito regional (nordestino vs sulista). Rivalidade entre estados. Polarização política extrema que impede união popular.",
         "Quando alguém te diz que o problema é 'o outro brasileiro', pergunte: quem ganha com essa divisão?"),
        (7, "A lei que não pega",
         "O Brasil tem leis excelentes — no papel. A Lei Feijó (1831) proibiu o tráfico mas nunca foi cumprida. A Constituição de 1988 garante saúde e educação para todos. A Lei da Ficha Limpa é burlada. A expressão 'lei pra inglês ver' NASCEU no Brasil.",
         "Leis ambientais ignoradas (desmatamento). Constituição descumprida (saúde, educação, moradia). Impunidade para crimes de colarinho branco.",
         "Uma lei só existe se for aplicada igualmente para todos. Lei sem fiscalização é sugestão.")
    ]
    db.executemany("INSERT OR REPLACE INTO patterns VALUES (?,?,?,?,?)", patterns)

def seed_events(db):
    events = [
        (1,"1500-04-22",1500,"Chegada dos Portugueses","Pedro Álvares Cabral chega ao Brasil. Início da colonização e extração de pau-brasil.","colonial","Espanha e Portugal dividem o mundo pelo Tratado de Tordesilhas (1494). Era dos Descobrimentos.",5,"BA","Pedro Álvares Cabral","Carta de Pero Vaz de Caminha"),
        (2,"1532-01-22",1532,"Primeira Sesmaria","Martim Afonso de Sousa concede a primeira sesmaria a Pedro de Góis. Início do latifúndio brasileiro.","colonial","Portugal expande seu império. Reforma Protestante na Europa.",5,None,"Martim Afonso de Sousa, Pedro de Góis","Registro colonial"),
        (3,"1534-01-01",1534,"Capitanias Hereditárias","Brasil dividido em 15 faixas de terra doadas a 12 donatários. Modelo que criou o latifúndio.","colonial","Inquisição portuguesa (1536). Conquista espanhola do Peru (Pizarro).",5,None,"D. João III, Duarte Coelho","Cartas de doação"),
        (4,"1548-01-01",1548,"Confederação dos Tamoios","Aliança indígena contra portugueses. Apoiados pelos franceses.","revolt","França Antártica: franceses tentam colonizar o Rio de Janeiro.",2,"RJ","Cunhambebe, Aimberê","Crônicas coloniais"),
        (5,"1630-01-01",1630,"Invasão Holandesa","Holanda conquista Pernambuco. Período de relativa tolerância religiosa.","colonial","Guerra dos 30 Anos na Europa. Companhia das Índias Ocidentais holandesa.",None,"PE","Maurício de Nassau","Registros da WIC"),
        (6,"1654-01-01",1654,"Expulsão dos Holandeses","Insurreição Pernambucana expulsa os holandeses. Heróis: um branco, um negro, um indígena.","revolt","Cromwell governa a Inglaterra. Holanda em declínio.",2,"PE","João Fernandes Vieira, Henrique Dias, Filipe Camarão","Crônicas coloniais"),
        (7,"1694-02-06",1694,"Destruição de Palmares","Quilombo dos Palmares destruído após quase 100 anos. Zumbi decapitado.","revolt","Luis XIV governa a França (absolutismo). Revolução Gloriosa na Inglaterra (1688).",2,"AL","Zumbi dos Palmares, Ganga Zumba","Registros coloniais"),
        (8,"1720-07-01",1720,"Revolta de Vila Rica","Filipe dos Santos enforcado por protestar contra Casas de Fundição.","revolt","Bolha dos Mares do Sul na Inglaterra. Iluminismo se espalha.",1,"MG","Filipe dos Santos","Registros de Minas"),
        (9,"1789-01-01",1789,"Inconfidência Mineira","Conspiração pela independência de MG. Tiradentes executado — único pobre do grupo.","revolt","Revolução Francesa começa no MESMO ANO. Independência dos EUA (1776) como inspiração.",1,"MG","Tiradentes, Tomás Gonzaga, Cláudio Manuel da Costa","Autos da Devassa"),
        (10,"1798-01-01",1798,"Conjuração Baiana","Primeira revolta POPULAR: alfaiates, soldados mulatos pediam fim da escravidão e república.","revolt","Revolução Francesa em andamento. Haiti: escravos se preparando para revoltar (1804).",1,"BA","Lucas Dantas, João de Deus, Cipriano Barata","Documentos da Conjuração"),
        (11,"1808-01-22",1808,"Corte Portuguesa no Brasil","Família real foge de Napoleão. 15.000 pessoas. Brasil vira sede do Império Português.","colonial","Guerras Napoleônicas devastam a Europa. Bloqueio Continental.",4,None,"D. João VI, Carlota Joaquina","Registros da Corte"),
        (12,"1822-09-07",1822,"Independência do Brasil","Pedro I declara independência. Único caso nas Américas onde o PRÍNCIPE colonizador faz a independência.","empire","Congresso de Viena redesenhou a Europa. Monroe (1823). Bolívar liberta a América espanhola.",4,None,"Pedro I, José Bonifácio","Documentos imperiais"),
        (13,"1824-01-01",1824,"Confederação do Equador","Nordeste se revolta contra centralização de Pedro I. Frei Caneca fuzilado.","revolt","Monroe Doctrine. Grã-Bretanha é potência hegemônica.",1,"PE","Frei Caneca, Manuel de Carvalho","Registros imperiais"),
        (14,"1831-04-07",1831,"Abdicação de Pedro I","Pedro I abdica após crise. Deixa filho de 5 anos como imperador.","empire","Revolução de Julho na França (1830) derruba Carlos X. Onda liberal na Europa.",4,None,"Pedro I, Pedro II (5 anos)","Diários imperiais"),
        (15,"1835-01-01",1835,"Cabanagem","Revolta popular no Pará. 40.000 mortos (30% da população). Maior massacre proporcional.","revolt","Abolição nas colônias britânicas (1833). Industrialização na Inglaterra.",1,"PA","Eduardo Angelim, Malcher, Vinagre","Relatórios provinciais"),
        (16,"1835-09-20",1835,"Revolução Farroupilha","RS declara república. 10 anos de guerra. Lanceiros Negros massacrados em Porongos.","revolt","Era Vitoriana na Inglaterra. Expansão americana (Destino Manifesto).",2,"RS","Bento Gonçalves, Anita Garibaldi, Giuseppe Garibaldi","Registros militares"),
        (17,"1838-01-01",1838,"Balaiada","Revolta de pobres, vaqueiros e escravos no MA. Negro Cosme enforcado, brancos anistiados.","revolt","Rainha Vitória coroada (1837). Primeira Guerra do Ópio na China (1839).",1,"MA","Balaio, Raimundo Gomes, Negro Cosme","Documentos provinciais"),
        (18,"1840-07-23",1840,"Golpe da Maioridade","Pedro II assume com 14 anos. 'Quero já!' Estabilidade volta ao país.","empire","Guerras do Ópio. Europa em industrialização acelerada.",4,None,"Pedro II","Atas do Senado"),
        (19,"1850-09-04",1850,"Lei Eusébio de Queirós","Fim REAL do tráfico negreiro (pressão britânica, não moral).","empire","Revolução Industrial plena. Grã-Bretanha policia os mares. Corrida do Ouro na Califórnia.",7,None,"Eusébio de Queirós","Legislação imperial"),
        (20,"1850-09-18",1850,"Lei de Terras","Terra só por COMPRA. Impediu ex-escravos e pobres de ter terra. Efeito até HOJE.","empire","Revolução de 1848 na Europa. Manifesto Comunista de Marx e Engels.",5,None,"Pedro II","Legislação imperial"),
        (21,"1864-12-01",1864,"Guerra do Paraguai","Maior guerra sul-americana. 300.000+ paraguaios mortos. Brasil usou escravos como soldados.","empire","Guerra Civil Americana (1861-65). Bismarck unifica a Alemanha.",2,None,"Duque de Caxias, Solano López, Osório","Registros militares"),
        (22,"1871-09-28",1871,"Lei do Ventre Livre","Filhos de escravas nascem 'livres' — mas ficam com senhor até 21 anos.","empire","Comuna de Paris (1871). Unificação da Alemanha e Itália.",3,None,"Visconde do Rio Branco","Legislação imperial"),
        (23,"1888-05-13",1888,"Lei Áurea — Abolição","Abolição SEM terra, sem educação, sem indenização para os libertos. Fazendeiros foram compensados.","empire","Conferência de Berlim (1884-85): Europa coloniza a África. Meiji no Japão.",3,None,"Princesa Isabel, Joaquim Nabuco, José do Patrocínio, Luís Gama","Lei Áurea"),
        (24,"1889-11-15",1889,"Proclamação da República","Golpe militar derruba Pedro II. 'Ordem e Progresso' (positivismo). Povo assistiu sem entender.","republic","Exposição Universal de Paris. Torre Eiffel inaugurada. Scramble for Africa.",4,None,"Deodoro da Fonseca, Benjamin Constant","Documentos republicanos"),
        (25,"1896-01-01",1896,"Guerra de Canudos","25.000+ mortos. Comunidade de sertanejos pobres exterminada pelo Exército.","revolt","Era do Imperialismo. EUA preparam guerra contra Espanha (1898).",1,"BA","Antônio Conselheiro, Euclides da Cunha","Os Sertões - Euclides da Cunha"),
        (26,"1904-11-01",1904,"Revolta da Vacina","Povo do Rio contra vacinação forçada e demolição de cortiços.","revolt","Guerra Russo-Japonesa (1904-05). Japão emergente.",6,"RJ","Oswaldo Cruz, Lauro Sodré","Jornais da época"),
        (27,"1910-11-22",1910,"Revolta da Chibata","Marinheiros NEGROS contra chibatadas. João Cândido: 'Almirante Negro'. Traído após vitória.","revolt","Revolução Mexicana (1910). Crise do Império Otomano.",2,"RJ","João Cândido","Registros da Marinha"),
        (28,"1912-01-01",1912,"Guerra do Contestado","20.000+ mortos. Caboclos vs. fazendeiros e ferrovia estrangeira. Bombardeio aéreo.","revolt","Titanic afunda (1912). Primeira Guerra Mundial se aproxima.",1,"SC","José Maria, Adeodato","Registros militares"),
        (29,"1922-07-05",1922,"Revolta dos 18 do Forte","Tenentes contra oligarquias. 18 marcharam contra o Exército. Início do tenentismo.","revolt","URSS fundada (1922). Fascismo na Itália (Mussolini).",4,"RJ","Eduardo Gomes, Siqueira Campos","Registros militares"),
        (30,"1930-10-03",1930,"Revolução de 1930","Vargas toma o poder. Fim da República Velha (café com leite).","republic","Grande Depressão (1929). Nazismo crescendo na Alemanha.",4,None,"Getúlio Vargas, Góis Monteiro","Documentos da Era Vargas"),
        (31,"1932-07-09",1932,"Revolução Constitucionalista","SP contra Vargas. Maior guerra civil do séc. XX no Brasil.","revolt","Hitler ascende ao poder (1933). New Deal nos EUA.",6,"SP","São Paulo inteiro","Registros militares"),
        (32,"1935-11-27",1935,"Intentona Comunista","Tentativa de golpe comunista. Prestes preso. Olga Benário entregue aos nazistas.","revolt","Nazismo consolidado. Mussolini invade a Etiópia. Stalin na URSS.",4,None,"Luís Carlos Prestes, Olga Benário","Documentos policiais"),
        (33,"1937-11-10",1937,"Estado Novo","Vargas dá golpe e instala ditadura. Censura, nacionalismo, trabalhismo.","dictatorship","Véspera da WWII. Fascismo na Europa. Guerra Civil Espanhola.",4,None,"Getúlio Vargas","Constituição de 1937"),
        (34,"1943-05-01",1943,"CLT — Consolidação das Leis do Trabalho","Direitos trabalhistas criados — MAS excluindo domésticas e rurais (= os negros).","republic","WWII em andamento. Brasil entra na guerra ao lado dos Aliados.",3,None,"Getúlio Vargas","CLT"),
        (35,"1954-08-24",1954,"Suicídio de Vargas","Vargas se mata: 'Saio da vida para entrar na História'. Carta-testamento acusa elite.","republic","Guerra Fria. McCarthismo nos EUA. Descolonização da Ásia.",4,None,"Getúlio Vargas","Carta-testamento"),
        (36,"1960-04-21",1960,"Inauguração de Brasília","JK constrói nova capital no cerrado. '50 anos em 5'. Endividamento massivo.","republic","Revolução Cubana (1959). Guerra Fria em escalada. Kennedy eleito.",5,"DF","Juscelino Kubitschek, Oscar Niemeyer, Lucio Costa","Documentos oficiais"),
        (37,"1964-03-31",1964,"Golpe Militar","Militares derrubam Jango com apoio dos EUA (Operação Brother Sam) e da elite.","dictatorship","Guerra do Vietnã. Guerra Fria. EUA derrubam governos em toda a América Latina.",4,None,"Castelo Branco, Costa e Silva, João Goulart","Documentos desclassificados CIA"),
        (38,"1968-12-13",1968,"AI-5","Ato mais repressivo da ditadura. Fechou Congresso. Tortura institucionalizada.","dictatorship","Maio de 68 (Paris). Primavera de Praga. Assassinato de MLK e Bobby Kennedy.",7,None,"Costa e Silva","Texto do AI-5"),
        (39,"1985-01-15",1985,"Fim da Ditadura","Tancredo Neves eleito (indiretamente). Morre antes de assumir. Sarney assume.","democracy","Gorbachev na URSS. Queda do Muro de Berlim (1989) se aproxima.",3,None,"Tancredo Neves, José Sarney","Documentos da transição"),
        (40,"1988-10-05",1988,"Constituição de 1988","'Constituição Cidadã'. Direitos amplos no papel. Implementação? Outra história.","democracy","Fim da Guerra Fria se aproxima. Perestroika na URSS.",7,None,"Ulysses Guimarães","Constituição Federal"),
        (41,"1992-09-29",1992,"Impeachment de Collor","Primeiro impeachment. Caras-pintadas nas ruas. Democracia testa suas ferramentas.","democracy","Fim da URSS (1991). Guerra do Golfo. Tratado de Maastricht (UE).",None,None,"Fernando Collor, Itamar Franco","Registros do Congresso"),
        (42,"2003-01-01",2003,"Governo Lula — Cotas Raciais","115 anos após abolição: primeiras cotas raciais nas universidades.","democracy","Guerra do Iraque. 11 de setembro mudou geopolítica. BRICS emergem.",3,None,"Lula","Legislação federal"),
        (43,"2013-06-01",2013,"Jornadas de Junho","Milhões nas ruas. Começou por 20 centavos (ônibus). Virou revolta difusa contra tudo.","democracy","Primavera Árabe (2011). Snowden (NSA). Crise europeia.",6,None,"Movimento popular","Jornais e redes sociais"),
        (44,"2013-04-02",2013,"PEC das Domésticas","125 anos para dar direitos PLENOS a empregadas domésticas.","democracy","Mesma época das Jornadas de Junho. Mundo debatia desigualdade (Piketty).",3,None,"Congresso Nacional","EC 72/2013"),
        (45,"2016-08-31",2016,"Impeachment de Dilma","Segundo impeachment da democracia brasileira.","democracy","Brexit. Trump eleito. Ascensão do populismo global.",None,None,"Dilma Rousseff, Michel Temer","Registros do Senado"),
        (46,"1871-06-28",1871,"Lei do Ventre Livre","Filhos de escravas nascem 'livres' mas ficam com senhor até 21 anos. Abolição de mentira.","empire","Comuna de Paris. Unificação alemã. Imperialismo europeu acelerando.",7,None,"Visconde do Rio Branco","Legislação imperial"),
        (47,"1885-09-28",1885,"Lei dos Sexagenários","'Liberta' escravos com 60+. Expectativa de vida era 35. Cinismo legislativo.","empire","Conferência de Berlim partilhando a África. Alemanha como potência.",7,None,"Saraiva, Cotegipe","Legislação imperial"),
        (48,"1897-10-05",1897,"Massacre Final de Canudos","Exército destrói Canudos completamente. Degola de prisioneiros. Crianças mortas.","revolt","Caso Dreyfus na França. Zola publica 'J'accuse'. Era do imperialismo.",1,"BA","Antônio Conselheiro","Os Sertões"),
        (49,"1984-04-16",1984,"Diretas Já","Maior mobilização popular da história do Brasil. Milhões pedindo eleições diretas.","democracy","Reagan nos EUA. Guerra Fria ainda ativa. URSS enfraquecendo.",None,None,"Ulysses Guimarães, Tancredo Neves, Lula","Registros jornalísticos"),
        (50,"2018-09-02",2018,"Incêndio do Museu Nacional","200 anos de história destruídos. Acervo de 20 milhões de itens. Descaso com memória.","democracy","Ascensão do populismo global. Crise das democracias.",5,"RJ","Negligência governamental","Laudos técnicos")
    ]
    db.executemany("INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?)", events)

def seed_states(db):
    states = [
        (1,"AC","Acre","Conquistado da Bolívia (Revolução Acreana, 1903). Seringueiros.","Revolução Acreana","Borracha (séc XIX-XX), extrativismo, agropecuária","Amazônia legal. Conexão com AM, RO. Rota da borracha."),
        (2,"AL","Alagoas","Colonização portuguesa (séc XVI). Terra de Palmares.","Quilombo dos Palmares (1680-1694)","Açúcar, algodão, pecuária","Berço de Palmares. Conexão com PE, SE, BA. Migração para SP."),
        (3,"AM","Amazonas","Missões religiosas e exploração. Ciclo da borracha.","Cabanagem (atingiu)","Borracha, Zona Franca de Manaus","Maior estado. Conexão com PA, AC, RR. Amazônia como patrimônio."),
        (4,"AP","Amapá","Disputa com a França (Contestado Franco-Brasileiro). Território até 1988.","Resistência a invasões francesas","Extrativismo, mineração","Fronteira com Guiana Francesa. Conexão com PA."),
        (5,"BA","Bahia","Primeira capital (Salvador, 1549). Centro do tráfico escravista.","Conjuração Baiana (1798), Sabinada (1837), Canudos (1896-97)","Açúcar, cacau, petróleo, turismo","Berço da cultura afro-brasileira. Conexão com TODOS os estados via diáspora baiana."),
        (6,"CE","Ceará","Colonização tardia. Primeiro estado a abolir escravidão (1884).","Quebra-Quilos, Oligarquia Accioly","Algodão, seca, indústria","Aboliu 4 anos antes da Lei Áurea! Conexão com PI, RN, PB. Grande emigração."),
        (7,"DF","Distrito Federal","Criado em 1960 por JK. Brasília: capital planejada.","Jornadas de Junho (2013)","Governo federal, serviços","Centro do poder. Construído por candangos (migrantes nordestinos)."),
        (8,"ES","Espírito Santo","Capitania de Vasco Fernandes Coutinho (1535). Resistência indígena.","Resistência Botocuda","Café, mineração (Vale)","Conexão com MG, RJ, BA. Porto de exportação."),
        (9,"GO","Goiás","Bandeirantes paulistas (séc XVIII). Mineração de ouro.","Sem grandes revoltas registradas","Ouro, agropecuária, soja","Centro do agronegócio. Conexão com MT, MS, MG, TO."),
        (10,"MA","Maranhão","Colonização francesa (1612) e portuguesa. Estado do Grão-Pará.","Revolta de Beckman (1684), Balaiada (1838-41)","Algodão, arroz, soja","Ligação histórica com o Pará (mesmo estado colonial). Grande desigualdade."),
        (11,"MT","Mato Grosso","Bandeirantes e mineração (séc XVIII). Fronteira com Paraguai/Bolívia.","Guerra do Paraguai (fronteira)","Ouro, borracha, soja, gado","Fronteira estratégica. Conexão com MS, GO, PA, AM."),
        (12,"MS","Mato Grosso do Sul","Separado de MT em 1977. Região de fronteira.","Guerra do Paraguai (palco)","Pecuária, soja, celulose","Fronteira com Paraguai e Bolívia. Conexão com SP, PR, GO, MT."),
        (13,"MG","Minas Gerais","Ciclo do Ouro (séc XVIII). Maior população colonial.","Inconfidência Mineira (1789), Revolta de Vila Rica (1720)","Ouro, ferro, café, leite, indústria","'Minas é muitas.' Conexão com TODOS os estados do Sudeste e Centro-Oeste."),
        (14,"PA","Pará","Uma das mais antigas ocupações. Belém (1616).","Cabanagem (1835-40) — 40.000 mortos","Borracha, mineração, extrativismo","Amazônia. Maior genocídio proporcional (Cabanagem). Conexão com AM, MA, TO, AP."),
        (15,"PB","Paraíba","Colonização com conflito indígena (Potiguara). Açúcar.","Confederação do Equador (1824)","Açúcar, algodão, turismo","João Pessoa: capital nomeada por assassinato político. Conexão com PE, RN, CE."),
        (16,"PR","Paraná","Colonização tardia. Imigração europeia massiva.","Revolução Federalista (1893), Contestado (limítrofe)","Café, soja, indústria","Maior diversidade étnica europeia. Conexão com SP, SC, MS."),
        (17,"PE","Pernambuco","Centro colonial. Mais revoltas que qualquer estado.","Insurreição Pernambucana, Confederação do Equador, Revolução de 1817, Praieira, Guerra dos Mascates","Açúcar (500 anos), tecnologia (Porto Digital)","Berço da resistência. Conexão com AL, PB, BA, CE."),
        (18,"PI","Piauí","Colonização pelo interior (pecuária), não pelo litoral.","Batalha do Jenipapo (1823) — independência de fato","Pecuária, soja","Única capital no interior do Nordeste (Teresina). Conexão com MA, CE, BA."),
        (19,"RJ","Rio de Janeiro","Capital por 197 anos (1763-1960). Centro do poder.","Revolta da Vacina (1904), Chibata (1910), Intentona (1935)","Café (Vale do Paraíba), petróleo, turismo, serviços","Ex-capital. Onde tudo acontecia. Conexão histórica com MG, SP, ES."),
        (20,"RN","Rio Grande do Norte","Colonização holandesa e portuguesa. Base aérea na WWII.","Confederação do Equador","Sal, petróleo, energia eólica","Parnamirim: trampolim da vitória na WWII. Conexão com PB, CE."),
        (21,"RS","Rio Grande do Sul","Colonização açoriana, depois alemã e italiana. Gaúchos.","Revolução Farroupilha (1835-45), Federalista (1893)","Pecuária, vinho, soja, indústria","Identidade forte. Separatismo histórico. Conexão com SC, PR."),
        (22,"RO","Rondônia","Território até 1981. Ciclo da borracha. Ferrovia Madeira-Mamoré.","Sem grandes revoltas","Borracha, agropecuária, mineração","Ferrovia Madeira-Mamoré: 'ferrovia do diabo'. Conexão com AM, MT, AC."),
        (23,"RR","Roraima","Último território a virar estado (1988). Fronteira norte.","Conflitos indígenas recentes (Raposa Serra do Sol)","Mineração, agropecuária","Menor população. Fronteira com Venezuela e Guiana."),
        (24,"SC","Santa Catarina","Colonização açoriana, alemã, italiana.","Guerra do Contestado (1912-16), República Juliana (Farroupilha)","Indústria, turismo, agropecuária","Diversidade europeia. Conexão com PR, RS."),
        (25,"SP","São Paulo","Bandeirantes. Depois café. Depois indústria. Hoje: motor econômico.","Revolução de 1932, Tenentismo","Café, indústria, serviços, tecnologia","De bandeirantes a locomotiva do país. Conexão com TODOS os estados (migração)."),
        (26,"SE","Sergipe","Menor estado. Separado da Bahia em 1820.","Sem grandes revoltas próprias","Açúcar, petróleo","Menor estado do Brasil. Conexão com BA, AL."),
        (27,"TO","Tocantins","Criado em 1988, separado de Goiás. Mais novo estado.","Sem revoltas (estado novo)","Agropecuária, soja","Estado mais jovem. Conexão com GO, MA, PA, BA.")
    ]
    db.executemany("INSERT OR REPLACE INTO states VALUES (?,?,?,?,?,?,?)", states)

def seed_families(db):
    families = [
        (1,"Albuquerque Coelho","Portugal","Colonial (1534+)","Donatários de Pernambuco, senhores de engenho","Descendentes na política nordestina","colonial"),
        (2,"Cavalcanti","Florença/Portugal","Colonial (séc XVI+)","Senhores de engenho, latifundiários","Políticos em PE até hoje","colonial"),
        (3,"Prado","Portugal","Colonial/Império","Cafeicultores, banqueiros, políticos de SP","Elite cultural e empresarial paulista","colonial"),
        (4,"Breves","Portugal","Império","Maior escravocrata do Brasil (6.000+ escravos)","Fortuna diluída após abolição","colonial"),
        (5,"Andrada","Portugal","Independência+","José Bonifácio: Patriarca da Independência","Políticos até hoje","colonial"),
        (6,"Junqueira","Portugal","Império","Barões do café em MG/SP","Latifundiários","colonial"),
        (7,"Teixeira Leite","Portugal","Império","Barões de Vassouras, maiores escravistas do Vale","Fortuna perdida com fim do café","colonial"),
        (8,"Wanderley","Holanda/Portugal","Colonial","Coronéis do sertão nordestino","Políticos no Nordeste","colonial"),
        (9,"Pessoa","Portugal","Colonial/República","Proprietários rurais na Paraíba","Epitácio Pessoa (presidente), João Pessoa (governador)","colonial"),
        (10,"Moreira Salles","Portugal/MG","Séc XIX+","Banqueiros, diplomatas","Itaú Unibanco (~$7B). Controlam maior banco privado do BR","moderna"),
        (11,"Safra","Síria/Líbano (judaica sefardita)","Séc XX","Banqueiros","~$20B combinada. Maior fortuna do Brasil","moderna"),
        (12,"Lemann","Suíça (ascendência judaica)","Séc XX","3G Capital, AB InBev","~$15B. Controla Burger King, Heinz","moderna"),
        (13,"Saverin","Turquia (judaica sefardita)","Séc XX","Cofundador do Facebook","~$14B. Mora em Singapura","moderna"),
        (14,"Esteves","RJ (judaica)","Séc XX","BTG Pactual","~$8B. Maior banco de investimentos da AL","moderna"),
        (15,"Ermírio de Moraes","Portugal/SP","Séc XX","Votorantim (indústria)","~$7B. Cimento, alumínio, celulose","moderna"),
        (16,"Setúbal/Villela","SP (elite cafeeira)","Séc XIX+","Itaú (banco)","~$6B. Raízes na elite paulista","moderna"),
        (17,"Ometto","Itália/SP","Séc XIX+","Açúcar e etanol (Cosan/Raízen)","~$5B. Continuidade DIRETA dos barões do açúcar","moderna"),
        (18,"Diniz","Portugal","Séc XX","Pão de Açúcar (varejo)","~$5B. Imigrante português","moderna"),
        (19,"Marinho","Portugal/RJ","Séc XX","Globo (mídia)","~$4B. Maior conglomerado de mídia da AL","moderna"),
        (20,"Steinbruch","Europa Oriental (judaica)","Séc XX","CSN (siderurgia)","~$2B. Aço, mineração","moderna"),
        (21,"Klabin/Lafer","Lituânia (judaica)","Séc XIX+","Klabin (papel e celulose)","~$2B. Maior produtora de papel do BR","moderna"),
        (22,"Sarney","Maranhão","Séc XX","Política, mídia","Oligarquia maranhense. Ex-presidente. Família controla MA há 60+ anos","política"),
        (23,"Calheiros","Alagoas","Séc XX","Política","Renan Calheiros: décadas no Senado. Família domina AL","política"),
        (24,"Magalhães","Bahia","Séc XX","Política, mídia","ACM e família: dominaram BA por 50+ anos","política"),
        (25,"Barbalho","Pará","Séc XX","Política","Jader Barbalho e família: dominam PA há décadas","política"),
        (26,"Neves","Minas Gerais","Séc XX","Política","Tancredo, Aécio: dinastia política mineira","política"),
        (27,"Covas/Doria","São Paulo","Séc XX","Política","Mário Covas, Bruno Covas: política paulista","política"),
        (28,"Gomes","Ceará","Séc XX","Política","Ciro, Cid Gomes: política cearense","política"),
        (29,"Bolsonaro","Rio de Janeiro","Séc XXI","Política","Família com 4+ membros na política simultaneamente","política"),
        (30,"Lula/PT","São Paulo/Nordeste","Séc XX+","Política, sindicalismo","De operário a presidente 2x. Maior líder popular desde Vargas","política")
    ]
    db.executemany("INSERT OR REPLACE INTO families VALUES (?,?,?,?,?,?,?)", families)

def seed_scenarios(db):
    scenarios = [
        (1,"Abolição COM ou SEM reforma agrária?",1888,
         "É 1888. A escravidão vai acabar. 700.000 pessoas serão libertadas. A pergunta é: COMO?",
         "Abolir E dar terras aos libertos (como André Rebouças propôs)",
         "Abolir SEM dar nada (como realmente aconteceu)",
         "A Lei Áurea foi assinada SEM nenhuma reparação. Libertos ficaram sem terra, sem casa, sem trabalho. Fazendeiros foram indenizados.",
         "Origem das favelas. Negros na base da pirâmide 138 anos depois. Desigualdade racial permanente.",
         "Liberdade sem condições materiais é abandono. Reforma agrária em 1888 teria mudado o Brasil inteiro."),
        (2,"Apoiar ou resistir ao Golpe de 1964?",1964,
         "Jango propõe reformas de base: agrária, urbana, bancária, educacional. Militares e EUA preparam golpe.",
         "Resistir ao golpe: defender as reformas e a democracia",
         "Apoiar o golpe: acreditar que militares 'salvarão' o país da 'ameaça comunista'",
         "O golpe aconteceu. 21 anos de ditadura. Tortura, censura, desaparecimentos. As reformas NUNCA foram feitas.",
         "Dívida externa explodiu. Desigualdade aumentou. Infraestrutura para elite (rodovias), nada para povo (saneamento). Trauma nacional.",
         "Quem promete 'ordem' em troca de liberdade geralmente entrega nem ordem nem liberdade."),
        (3,"Privatizar ou criar fundo soberano com o pré-sal?",2010,
         "Brasil descobre enormes reservas de petróleo no pré-sal. O que fazer com essa riqueza?",
         "Criar fundo soberano (modelo Noruega): lucros investidos em educação, saúde e futuro",
         "Privatizar: vender para empresas estrangeiras em troca de royalties",
         "Brasil adotou modelo misto, mas sem fundo soberano robusto. Petrobras parcialmente privatizada. Lucros distribuídos sem planejamento.",
         "Noruega com fundo soberano: $1.4 TRILHÃO guardados para o futuro. Brasil: petróleo extraído, lucro exportado.",
         "Recurso natural é finito. Sem fundo soberano, é riqueza de uma geração e miséria das próximas."),
        (4,"Constituinte aberta ou fechada?",1987,
         "Ditadura acabou. Brasil precisa de nova Constituição. Quem escreve?",
         "Constituinte EXCLUSIVA: cidadãos eleitos SÓ para escrever a Constituição",
         "Congresso Constituinte: os mesmos deputados/senadores escrevem a Constituição E legislam",
         "Optaram pelo Congresso Constituinte. Mesmos políticos da ditadura participaram. Muitos artigos progressistas, mas com brechas para a elite.",
         "Constituição avançada MAS cheia de exceções. Direitos garantidos no papel, descumpridos na prática.",
         "Quem escreve as regras do jogo determina quem ganha. Constituinte exclusiva teria sido mais democrática."),
        (5,"Industrializar ou continuar agrário?",1850,
         "Barão de Mauá quer industrializar o Brasil. Elite agrária prefere continuar exportando café.",
         "Apoiar Mauá: industrialização, ferrovias, bancos nacionais",
         "Manter o modelo agrário-exportador",
         "A elite sabotou Mauá. Bancos ingleses dominaram. Brasil continuou exportando café cru e importando tudo manufaturado.",
         "Japão (Meiji, 1868) industrializou e virou potência. Brasil ficou agrário e permanece dependente até hoje.",
         "País que exporta matéria-prima e importa produto acabado será sempre colônia econômica."),
        (6,"Integrar ou segregar após abolição?",1890,
         "Escravidão acabou. O que fazer com 700.000 libertos?",
         "Integrar: educação, terras, cidadania plena para todos",
         "Política de embranquecimento: trazer imigrantes europeus para 'substituir' negros",
         "Brasil escolheu o embranquecimento. Incentivou imigração europeia. Negros ficaram marginalizados. Lei da Vadiagem prendia quem não tinha emprego.",
         "Racismo estrutural consolidado. Negros na base econômica. Mito da 'democracia racial'.",
         "Integração custa dinheiro hoje mas constrói nação. Segregação é barata hoje mas destrói o futuro."),
        (7,"Votar nas Diretas ou aceitar eleição indireta?",1984,
         "Milhões pedem eleições diretas. Congresso vai votar a emenda Dante de Oliveira.",
         "Insistir nas diretas: pressão popular até conseguir",
         "Aceitar a indireta: 'pelo menos saímos da ditadura'",
         "A emenda foi REJEITADA (faltaram 22 votos). Eleição indireta elegeu Tancredo (que morreu). Sarney governou.",
         "Transição 'lenta, gradual e segura' preservou poder dos militares e da elite. Democratização incompleta.",
         "Aceitar 'o possível' quando se podia exigir 'o necessário' é a história do Brasil."),
        (8,"Resistir ou aceitar a dívida externa?",1980,
         "Brasil deve $100 bilhões para bancos estrangeiros. FMI exige austeridade.",
         "Declarar moratória: não pagar e investir no povo (como fez parcialmente em 1987)",
         "Aceitar as condições do FMI: cortar gastos sociais para pagar bancos",
         "Brasil alternou entre as duas. Moratória de 1987 foi parcial. Depois aceitou condições do FMI nos anos 90.",
         "Década perdida (1980s). Hiperinflação. Privatizações nos anos 90. Dependência financeira permanente.",
         "Dívida é instrumento de controle. País endividado não é soberano."),
        (9,"Quilombo ou fuga individual?",1680,
         "Você é escravizado. Consegue fugir. O que faz?",
         "Ir para Palmares: construir sociedade livre coletiva",
         "Fugir sozinho: buscar liberdade individual no mato",
         "Palmares existiu por quase 100 anos. 20.000+ pessoas. Agricultura, defesa, organização social. Provou que era possível.",
         "Palmares foi destruído, mas sua memória sobreviveu. Zumbi virou símbolo. 20 de novembro = Dia da Consciência Negra.",
         "Resistência coletiva cria legado. Resistência individual desaparece. Organize-se."),
        (10,"Educação ou segurança?",2026,
         "Orçamento limitado. Onde investir: mais escolas ou mais polícia?",
         "Educação: investir em escolas, universidades, formação profissional",
         "Segurança: mais polícia, mais prisões, mais câmeras",
         "Dados mostram que países que investiram em educação (Coreia do Sul, Finlândia) reduziram criminalidade. Países que investiram só em polícia (EUA, Brasil) têm as maiores populações carcerárias do mundo.",
         "Brasil tem 900.000 presos e criminalidade crescente. Coreia do Sul investiu em educação e tem taxa de homicídio 50x menor.",
         "Prender é caro e não funciona. Educar é investimento que paga em uma geração.")
    ]
    db.executemany("INSERT OR REPLACE INTO scenarios VALUES (?,?,?,?,?,?,?,?,?)", scenarios)

def seed_constitution(db):
    articles = [
        (1,"Art. 1°","Todo poder emana do povo, que o exerce por meio de representantes eleitos ou diretamente.","O poder é SEU. Deputados são seus empregados, não seus chefes. E você pode exercer poder diretamente (plebiscito, referendo, iniciativa popular).",0,"Na prática, plebiscitos e referendos quase nunca acontecem. Iniciativa popular exige 1.5 milhão de assinaturas. O povo delega e esquece."),
        (2,"Art. 3°, III","Erradicar a pobreza e reduzir as desigualdades sociais e regionais.","O Brasil TEM OBRIGAÇÃO constitucional de acabar com a pobreza. Não é favor — é dever.","0","Brasil é top 10 em desigualdade no mundo. 33 milhões passam fome (2023). Claramente descumprido."),
        (3,"Art. 5°","Todos são iguais perante a lei, sem distinção de qualquer natureza.","Ninguém é mais que ninguém. Não importa se é rico, pobre, preto, branco, homem, mulher.",0,"Foro privilegiado para políticos. Negros representam 67% dos presos. Justiça de classe evidente."),
        (4,"Art. 5°, XXXV","A lei não excluirá da apreciação do Poder Judiciário lesão ou ameaça a direito.","Se alguém feriu seu direito, você pode ir à Justiça. SEMPRE. Ninguém pode te impedir.",1,"Funciona razoavelmente, embora a Justiça seja lenta (processo pode levar 10+ anos)."),
        (5,"Art. 5°, LXIII","O preso será informado de seus direitos, entre os quais o de permanecer calado.","Se for preso, você NÃO precisa falar nada. Pode ficar calado. E tem direito a advogado.",0,"Policiais frequentemente ignoram isso. Presos pobres raramente têm acesso a advogado nas primeiras horas."),
        (6,"Art. 6°","São direitos sociais a educação, a saúde, a alimentação, o trabalho, a moradia, o transporte, o lazer, a segurança...","Você TEM DIREITO a: escola, hospital, comida, emprego, casa, ônibus, lazer, segurança. Tudo isso é OBRIGAÇÃO do Estado.",0,"Filas no SUS. Escolas sem estrutura. Déficit habitacional de 6 milhões. Transporte caro. Massivamente descumprido."),
        (7,"Art. 7°, IV","Salário mínimo capaz de atender às necessidades vitais básicas do trabalhador e de sua família.","O salário mínimo deveria pagar: moradia, alimentação, educação, saúde, lazer, vestuário, higiene, transporte e previdência.",0,"DIEESE calcula que o mínimo deveria ser ~R$6.500. O real é ~R$1.500. Descumprido por definição."),
        (8,"Art. 14","A soberania popular será exercida pelo sufrágio universal e pelo voto direto e secreto.","Você vota. Seu voto é secreto. Ninguém pode te obrigar a votar em ninguém.",1,"Funciona mecanicamente, mas o sistema é influenciado por dinheiro, fake news e compra de votos."),
        (9,"Art. 37","A administração pública obedecerá aos princípios de legalidade, impessoalidade, moralidade, publicidade e eficiência.","Governo tem que ser: legal, impessoal, moral, público e eficiente. Tudo ao mesmo tempo.",0,"Nepotismo, corrupção, sigilo de 100 anos, ineficiência crônica. Princípios existem no papel."),
        (10,"Art. 170","A ordem econômica tem por fim assegurar a todos existência digna, conforme os ditames da justiça social.","A economia do Brasil deve servir ao POVO, não ao mercado. Existência digna é o objetivo constitucional da economia.",0,"Economia orientada para lucro e exportação. 33 milhões com fome num país que alimenta 1.5 bilhão."),
        (11,"Art. 196","A saúde é direito de todos e dever do Estado.","SUS é um DIREITO SEU. Hospital público, remédio, tratamento — tudo gratuito. É direito, não favor.",1,"SUS existe e funciona (maior sistema público do mundo), mas subfinanciado. Filas enormes."),
        (12,"Art. 205","A educação é direito de todos e dever do Estado e da família.","Escola pública e gratuita é seu DIREITO. Da creche à universidade.",1,"Existe, mas qualidade precária. Professor mal pago. Infraestrutura ruim. Investimento abaixo da meta."),
        (13,"Art. 215","O Estado garantirá a todos o pleno exercício dos direitos culturais.","Cultura é direito. Museu, teatro, música, arte — o Estado deve garantir acesso.",0,"Museu Nacional pegou fogo (2018). Cultura é o primeiro orçamento cortado."),
        (14,"Art. 225","Todos têm direito ao meio ambiente ecologicamente equilibrado.","Amazônia, cerrado, água limpa — são SEUS direitos. Destruir o meio ambiente é violar a Constituição.",0,"Desmatamento recorde. Queimadas. Garimpo ilegal. Agrotóxicos. Massivamente descumprido."),
        (15,"Art. 231","São reconhecidos aos índios os direitos originários sobre as terras que tradicionalmente ocupam.","Terras indígenas são dos indígenas. Ponto. A Constituição é clara.",0,"Marco temporal. Invasões. Garimpo. Assassinatos de lideranças. Sob ataque constante.")
    ]
    db.executemany("INSERT OR REPLACE INTO constitution_articles VALUES (?,?,?,?,?,?)", articles)

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    seed_patterns(db)
    seed_events(db)
    seed_states(db)
    seed_families(db)
    seed_scenarios(db)
    seed_constitution(db)
    db.commit()
    
    # Print stats
    for table in ['events','patterns','states','families','scenarios','constitution_articles']:
        count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  ✅ {table}: {count} registros")
    
    db.close()
    print(f"\n🇧🇷 Banco criado em: {DB_PATH}")

def seed_civic_tables(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        author_anon TEXT DEFAULT 'Cidadão Anônimo',
        created_at TEXT DEFAULT (datetime('now')),
        votes_yes INTEGER DEFAULT 0,
        votes_no INTEGER DEFAULT 0,
        votes_abstain INTEGER DEFAULT 0,
        status TEXT DEFAULT 'aberta'
    );

    CREATE TABLE IF NOT EXISTS judgments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_name TEXT NOT NULL,
        target_period TEXT,
        target_role TEXT,
        description TEXT NOT NULL,
        charge TEXT NOT NULL,
        votes_culpado INTEGER DEFAULT 0,
        votes_inocente INTEGER DEFAULT 0,
        votes_parcial INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS budget_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        setor TEXT NOT NULL,
        valor_bilhoes REAL NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS study_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        trilha_id INTEGER NOT NULL,
        lesson_id INTEGER NOT NULL,
        completed INTEGER DEFAULT 0,
        quiz_score INTEGER DEFAULT -1
    );
    """)

    # Seed initial proposals
    proposals = [
        ("Renda Básica Universal de R$ 800 para todos os brasileiros adultos",
         "Todo cidadão brasileiro maior de 18 anos receberia R$ 800 mensais, sem condicionalidades. Financiado por imposto sobre grandes fortunas e transações financeiras acima de R$ 100k.",
         "economia"),
        ("Voto obrigatório para quem paga imposto, opcional para quem não paga",
         "Quem paga imposto de renda tem obrigação de votar. Quem não paga (baixa renda) tem o voto facultativo. Mantém engajamento da classe produtiva sem punir os mais pobres.",
         "política"),
        ("Reforma agrária com indenização justa e prazo de 10 anos",
         "Desapropriar terras improdutivas acima de 500 hectares, indenizar a preço de mercado, distribuir em lotes de 20-50 ha para famílias cadastradas, com assistência técnica por 5 anos.",
         "social"),
        ("Teto de gasto para publicidade governamental: 0.1% do PIB",
         "Governo federal, estados e municípios somados não podem gastar mais de 0,1% do PIB em publicidade. Atual gasto: R$ 3 bilhões/ano. Meta: R$ 1,5 bilhão máximo.",
         "transparência"),
        ("Mandato único de 6 anos para todos os cargos eletivos",
         "Presidente, governadores, prefeitos, senadores, deputados: todos com mandato único de 6 anos, sem reeleição. Elimina política de carreira. Força renovação a cada ciclo.",
         "política"),
    ]
    for p in proposals:
        existing = db.execute("SELECT id FROM proposals WHERE title = ?", (p[0],)).fetchone()
        if not existing:
            db.execute("INSERT INTO proposals (title, description, category) VALUES (?,?,?)", p)

    # Seed judgments
    judgments = [
        ("Getúlio Vargas", "1930-1954", "Presidente/Ditador",
         "Criou a CLT e os direitos trabalhistas, mas também instaurou o Estado Novo, censurou a imprensa e torturou opositores. Entregou Olga Benário (grávida) aos nazistas.",
         "Crime contra a democracia vs. legado trabalhista"),
        ("Princesa Isabel", "1888", "Regente do Império",
         "Assinou a Lei Áurea e aboliu a escravidão. Mas a abolição veio sem terra, sem educação, sem indenização para os libertos. Os fazendeiros foram indenizados. Negros foram abandonados.",
         "Abolição incompleta: herói ou cumplice da exclusão pós-escravidão?"),
        ("Marechal Deodoro da Fonseca", "1889-1891", "Primeiro Presidente",
         "Proclamou a República. Mas também deu golpe no próprio Congresso (1891), instaurou estado de sítio e renunciou antes de ser deposto. A República nasceu sem o povo.",
         "Republicano ou golpista? O povo foi consultado?"),
        ("Dom Pedro II", "1840-1889", "Imperador",
         "49 anos de reinado. Modernizou o Brasil, aboliu a escravidão gradualmente, perdeu a guerra do Paraguai com 400k mortos, foi derrubado sem processo democrático.",
         "O melhor governante que o Brasil já teve — ou um imperador que atrasou a democracia?"),
        ("Emílio Garrastazu Médici", "1969-1974", "Ditador",
         "O período mais brutal da ditadura. Tortura sistemática, desaparecimentos, censura total. Mas também o 'Milagre Econômico': 10% de crescimento ao ano. A conta chegou depois.",
         "Crescimento econômico justifica tortura e censura?"),
    ]
    for j in judgments:
        existing = db.execute("SELECT id FROM judgments WHERE target_name = ?", (j[0],)).fetchone()
        if not existing:
            db.execute("INSERT INTO judgments (target_name, target_period, target_role, description, charge) VALUES (?,?,?,?,?)", j)

    db.commit()
    print("  ✅ proposals: seeded")
    print("  ✅ judgments: seeded")
    print("  ✅ budget_allocations: created")
    print("  ✅ study_progress: created")


def seed_painel_tables(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        type TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT DEFAULT 'proposta',
        budget_bi REAL DEFAULT 0,
        start_date TEXT,
        end_date TEXT,
        responsible TEXT,
        progress_pct INTEGER DEFAULT 0,
        priority TEXT DEFAULT 'media',
        state TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        votes_yes INTEGER DEFAULT 0,
        votes_no INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS laws (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        phase TEXT DEFAULT 'proposta',
        author TEXT,
        type TEXT DEFAULT 'ordinaria',
        impact TEXT,
        votes_yes INTEGER DEFAULT 0,
        votes_no INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        last_update TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS processes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_number TEXT,
        title TEXT NOT NULL,
        type TEXT NOT NULL,
        description TEXT NOT NULL,
        defendant TEXT,
        charge TEXT,
        status TEXT DEFAULT 'abertura',
        verdict TEXT,
        court TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        last_update TEXT DEFAULT (datetime('now'))
    );
    """)

    # Seed projects
    projects = [
        ("Construção do Hospital Regional do Nordeste", "saude", "Hospital com 500 leitos para atender 2 milhões de habitantes do interior nordestino. Inclui UTI, maternidade e pronto-socorro.", "em_execucao", 1.2, "2024-03-01", "2026-12-01", "Ministério da Saúde", 45, "alta", "NE"),
        ("Ampliação da BR-163 no Pará", "infraestrutura", "Pavimentação de 800km da BR-163 na Amazônia, conectando o Pará ao Mato Grosso para escoamento da produção agrícola.", "em_execucao", 3.8, "2023-06-01", "2027-06-01", "DNIT", 32, "alta", "PA"),
        ("Programa Escola em Tempo Integral", "escola", "Expansão do ensino em tempo integral para 1 milhão de alunos da rede pública. Inclui refeições, reforço e atividades extracurriculares.", "aprovado", 2.5, "2025-01-01", "2028-12-31", "MEC", 10, "alta", None),
        ("Sistema de Defesa Cibernética Nacional", "militar", "Criação do Centro de Defesa Cibernética do Brasil para proteção de infraestrutura crítica contra ataques digitais.", "proposta", 0.8, None, None, "Ministério da Defesa", 0, "media", None),
        ("Plataforma de IA para Saúde Pública", "tecnologia", "Sistema de inteligência artificial para diagnóstico precoce de doenças no SUS, analisando exames e histórico de pacientes.", "proposta", 0.3, None, None, "DATASUS", 0, "media", None),
        ("Saneamento Básico Universal até 2033", "civil", "Marco do Saneamento: levar água tratada e esgoto para os 35 milhões de brasileiros que ainda não têm acesso. Meta constitucional.", "em_execucao", 15.0, "2021-07-15", "2033-12-31", "Ministério das Cidades", 22, "critica", None),
        ("Ferrovia Norte-Sul (trecho central)", "infraestrutura", "355km de ferrovia ligando Anápolis (GO) a Ouro Verde (GO), integrando o centro do país ao sistema ferroviário nacional.", "em_execucao", 5.6, "2022-01-01", "2026-12-01", "VALEC", 68, "alta", "GO"),
        ("Construção de 50 Escolas Técnicas Federais", "escola", "Expansão da Rede Federal de Educação Profissional com 50 novas unidades em cidades médias, priorizando regiões sem IFETs.", "aprovado", 1.8, "2025-06-01", "2028-12-31", "MEC/SETEC", 5, "alta", None),
    ]
    for p in projects:
        db.execute("INSERT INTO projects (title,type,description,status,budget_bi,start_date,end_date,responsible,progress_pct,priority,state) VALUES (?,?,?,?,?,?,?,?,?,?,?)", p)

    # Seed laws
    laws = [
        ("PEC 45/2019", "Reforma Tributária", "Unifica PIS, Cofins, IPI, ICMS e ISS em dois impostos: CBS (federal) e IBS (estadual/municipal). Simplifica o sistema mais complexo do mundo.", "promulgada", "Congresso Nacional", "constitucional", "Reduz custo do compliance tributário. Impacto de R$ 2,5 trilhões na economia em 10 anos."),
        ("PL 2.630/2020", "PL das Fake News", "Regulamenta plataformas digitais no Brasil. Obriga transparência de algoritmos e rastreabilidade de conteúdo em massa.", "comissao", "Senado Federal", "ordinaria", "Afeta liberdade de expressão vs. combate à desinformação. Polêmico."),
        ("PL 1.087/2023", "Marco da IA", "Regulamentação da Inteligência Artificial no Brasil. Define responsabilidades, direitos dos usuários e proibições.", "votacao", "Câmara dos Deputados", "ordinaria", "Pode posicionar o Brasil como líder em regulação de IA na América Latina."),
        ("PEC 66/2023", "Reforma do Judiciário", "Cria o Conselho Nacional de Supervisão da Magistratura com representação da sociedade civil. Aumenta transparência do Judiciário.", "proposta", "Congresso Nacional", "constitucional", "Reduz autonomia excessiva do STF. Polêmico entre juristas."),
        ("PL 4.173/2023", "Imposto sobre Super-Ricos", "Tributação mínima de 15% sobre rendimentos de pessoas físicas com patrimônio acima de R$ 50 milhões.", "sancionada", "Executivo Federal", "ordinaria", "Arrecadação estimada de R$ 14 bilhões/ano. Alinhado a acordo OCDE."),
        ("PL 2.903/2023", "Estatuto dos Povos Indígenas", "Reforma da legislação indigenista brasileira. Define direitos territoriais, consulta prévia e proteção cultural.", "comissao", "Câmara dos Deputados", "ordinaria", "Tensão entre direitos indígenas e agronegócio. Marco temporal em disputa."),
    ]
    for l in laws:
        db.execute("INSERT INTO laws (number,title,description,phase,author,type,impact) VALUES (?,?,?,?,?,?,?)", l)

    # Seed processes
    procs = [
        ("AP 1002/STF", "Ação Penal — Golpistas de 8 de Janeiro", "penal", "Julgamento dos responsáveis pelos ataques às sedes dos três poderes em 8 de janeiro de 2023.", "Mais de 200 réus", "Abolição violenta do Estado Democrático de Direito, golpe de Estado, dano ao patrimônio público", "julgamento", None, "STF"),
        ("ADPF 709/STF", "Proteção das Terras Yanomami", "constitucional", "Ação para garantir proteção federal das terras Yanomami contra garimpo ilegal, omissão do Estado e genocídio.", "União Federal", "Omissão na proteção de povos indígenas — violação do Art. 231 da CF", "sentenca", "Procedente — Estado obrigado a agir", "STF"),
        ("ACP 2023.001", "Desmatamento Ilegal no Cerrado", "civil_publica", "Ação Civil Pública contra fazendeiros e empresas por desmatamento em área de proteção do Cerrado (600 mil ha).", "Fazendas Agro Norte S/A e outros", "Violação do Código Florestal e Art. 225 da CF", "instrucao", None, "TRF-1"),
        ("INQ 4.781/STF", "Investigação de Fake News e Milícias Digitais", "penal", "Inquérito que investiga ataques ao STF, financiamento de fake news e organização de milícias digitais.", "Investigados: múltiplos", "Incitação ao crime, ameaça a ministros, financiamento de atos antidemocráticos", "recurso", "Condenação em 1ª instância", "STF"),
        ("MS 38.760/STJ", "Anulação de Licitação Superfaturada", "administrativo", "Mandado de segurança contestando licitação de R$ 2,3 bilhões para obra de saneamento com indícios de sobrepreço de 40%.", "Construtora Mega Engenharia", "Superfaturamento, fraude em licitação, desvio de recursos públicos", "abertura", None, "STJ"),
    ]
    for p in procs:
        db.execute("INSERT INTO processes (case_number,title,type,description,defendant,charge,status,verdict,court) VALUES (?,?,?,?,?,?,?,?,?)", p)

    db.commit()
    print("  ✅ projects: seeded (8)")
    print("  ✅ laws: seeded (6)")
    print("  ✅ processes: seeded (5)")

def seed_v2_tables(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_number TEXT NOT NULL,
        description TEXT NOT NULL,
        level TEXT NOT NULL,
        location TEXT,
        evidence TEXT,
        status TEXT DEFAULT 'recebida',
        support_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS assemblies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        type TEXT NOT NULL,
        level TEXT NOT NULL,
        location TEXT,
        description TEXT NOT NULL,
        signatures INTEGER DEFAULT 1,
        min_signatures INTEGER DEFAULT 10,
        status TEXT DEFAULT 'coletando',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS feed_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        source TEXT,
        level TEXT DEFAULT 'federal',
        state TEXT,
        city TEXT,
        category TEXT DEFAULT 'geral',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS citizen_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_area TEXT NOT NULL,
        skill_name TEXT NOT NULL,
        role_title TEXT NOT NULL,
        role_description TEXT NOT NULL,
        sector TEXT NOT NULL,
        rotation_months INTEGER DEFAULT 24,
        level TEXT DEFAULT 'cidade'
    );
    """)

    # Seed feed items
    feeds = [
        ("Saneamento básico: 35 milhões ainda sem acesso à água tratada", "Relatório do IBGE aponta que o Brasil ainda tem 35 milhões de pessoas sem acesso a água potável, concentradas no Norte e Nordeste.", "IBGE 2024", "federal", None, None, "infraestrutura"),
        ("STF julga constitucionalidade do marco temporal indígena", "Supremo analisa se terras indígenas só podem ser demarcadas onde havia ocupação em 1988.", "STF", "federal", None, None, "constituicao"),
        ("Reforma Tributária: primeiros efeitos em 2025", "CBS começa a substituir PIS/Cofins. Empresas relatam simplificação mas alertam para período de transição.", "Receita Federal", "federal", None, None, "economia"),
        ("Desmatamento na Amazônia cai 50% em 2023", "INPE registra menor taxa desde 2018. Operações de fiscalização e pressão internacional são apontadas como causas.", "INPE", "federal", "AM", None, "meio_ambiente"),
        ("Greve dos professores em Minas Gerais entra no 3º mês", "Professores estaduais paralisam aulas em protesto contra defasagem salarial de 40% em relação ao piso nacional.", "Sind-UTE", "estado", "MG", "Belo Horizonte", "educacao"),
        ("Obra do VLT de Fortaleza parada há 2 anos por falta de verba", "Veículo Leve sobre Trilhos com R$ 800 milhões investidos está paralisado. Governo federal corta repasse.", "Tribunal de Contas", "cidade", "CE", "Fortaleza", "infraestrutura"),
        ("Dengue: 3 milhões de casos em 2024, recorde histórico", "Brasil bate recorde de casos de dengue. Especialistas apontam falta de saneamento e mudanças climáticas.", "Ministério da Saúde", "federal", None, None, "saude"),
        ("Fundo Constitucional do DF defasado em R$ 2 bilhões", "Governo federal repassa menos do que é constitucionalmente obrigado ao Distrito Federal há 5 anos consecutivos.", "CLDF", "estado", "DF", "Brasília", "constituicao"),
        ("Escola sem telhado: 40% das escolas públicas precisam de reforma urgente", "Levantamento do MEC mostra estrutura precária em quase metade das escolas públicas do país.", "MEC 2024", "federal", None, None, "educacao"),
        ("Garimpo ilegal em Terra Yanomami reduzido em 70% após operação", "IBAMA e Polícia Federal removem 95% dos garimpeiros. Saúde dos Yanomami ainda em estado crítico.", "IBAMA", "federal", "RR", None, "constituicao"),
    ]
    for f in feeds:
        db.execute("INSERT INTO feed_items (title,summary,source,level,state,city,category) VALUES (?,?,?,?,?,?,?)", f)

    # Seed citizen roles
    roles = [
        ("saude","Enfermagem","Agente de Saúde Comunitária","Visita domiciliar, prevenção, acompanhamento de famílias vulneráveis no bairro","Saúde Pública",18,"bairro"),
        ("saude","Medicina","Médico do PSF","Atendimento primário no Posto de Saúde da Família, referenciamento e prevenção","Saúde Pública",24,"cidade"),
        ("educacao","Pedagogia","Tutor Cívico","Facilitador de educação política e histórica em escolas públicas do bairro","Educação",12,"bairro"),
        ("educacao","Ensino","Professor da Rede Pública","Docência na rede estadual ou municipal com plano de carreira meritocrático","Educação",36,"cidade"),
        ("engenharia","Engenharia Civil","Fiscal de Obras Públicas","Supervisão de obras de infraestrutura, saneamento e habitação no município","Infraestrutura",24,"cidade"),
        ("engenharia","Engenharia de Software","Desenvolvedor de Sistemas Públicos","Desenvolvimento e manutenção de sistemas de governo (DATAPREV, DATASUS, etc.)","Tecnologia",24,"federal"),
        ("direito","Advocacia","Defensor Público Rotativo","Atendimento jurídico gratuito à população de baixa renda","Justiça",18,"cidade"),
        ("direito","Mediação","Mediador Comunitário","Resolução de conflitos de bairro sem necessidade de judicialização","Justiça",12,"bairro"),
        ("administracao","Gestão","Gestor de Projeto Social","Coordenação de projetos sociais financiados por fundo municipal","Assistência Social",18,"cidade"),
        ("administracao","Finanças","Auditor Cidadão","Revisão de contas públicas municipais com publicação de relatório","Transparência",12,"cidade"),
        ("ti","Programação","Desenvolvedor Cívico","Criação de ferramentas de transparência e participação popular","Tecnologia",24,"federal"),
        ("ti","Dados","Analista de Dados Públicos","Análise e publicação de dados do governo em formato acessível","Transparência",18,"federal"),
        ("comunicacao","Jornalismo","Repórter Cidadão","Cobertura hiperlocal de bairro com publicação em plataforma pública","Comunicação",12,"bairro"),
        ("campo","Agricultura","Técnico Agrícola Comunitário","Assistência técnica a agricultores familiares e cooperativas rurais","Agricultura",18,"cidade"),
        ("seguranca","Bombeiro","Defesa Civil Comunitária","Treinamento da comunidade em primeiros socorros e evacuação","Segurança",12,"bairro"),
        ("cultura","Arte","Agente Cultural","Organização de eventos culturais e preservação do patrimônio local","Cultura",12,"bairro"),
    ]
    db.executemany("INSERT INTO citizen_roles (skill_area,skill_name,role_title,role_description,sector,rotation_months,level) VALUES (?,?,?,?,?,?,?)", roles)

    db.commit()
    print("  ✅ violations: created")
    print("  ✅ assemblies: created")
    print("  ✅ feed_items: seeded (10)")
    print("  ✅ citizen_roles: seeded (16)")

if __name__ == '__main__':
    print("🇧🇷 Brasil Soberano — Inicializando banco de dados...")
    init_db()
    db = sqlite3.connect(DB_PATH)
    seed_civic_tables(db)
    seed_painel_tables(db)
    seed_v2_tables(db)
    db.close()
    print("✅ Pronto!")
