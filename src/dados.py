"""Módulo unificado de coleta, limpeza, padronização e integração das bases.

Centraliza todo o pipeline de ETL (extração, transformação e carga) do projeto
para manter o notebook principal focado na análise exploratória, nos testes
estatísticos e nas visualizações:

1. Coleta via API (com cache local em CSV) e reorganização dos indicadores do
   World Bank (população, PIB total e PIB per capita);
2. Padronização dos códigos de país (ISO-3 do World Bank -> código NOC do COI),
   tratando colisões e transições históricas;
3. Filtragem exclusiva dos Jogos Olímpicos de Verão, padronização de delegações
   e agregação de subedições ocorridas no mesmo ano (como Melbourne e Estocolmo
   em 1956);
4. Construção da base completa na granularidade ``país × edição olímpica``,
   incorporando delegações participantes sem medalhas (com contagem zerada);
5. Junção com os indicadores socioeconômicos e diagnóstico de NOCs sem
   correspondência no World Bank.

Attributes:
    INDICADORES_WB: Mapeamento entre os códigos oficiais das séries do World Bank
        e os nomes padronizados das colunas no DataFrame final.
    ANO_INICIAL_WB: Primeiro ano solicitado na consulta à API do World Bank.
    ANO_FINAL_WB: Último ano solicitado na consulta à API do World Bank.
    CAMINHO_CSV_WB: Caminho padrão do arquivo CSV local usado como cache dos
        dados do World Bank.
    ISO_PARA_NOC: Dicionário de conversão explícita de códigos ISO-3 para códigos
        NOC nos casos em que as duas nomenclaturas divergem.
    ISO_REMOVIDO_WB: Código ISO-3 descartado antes do mapeamento por representar
        território sem comitê olímpico próprio e colidir com um NOC existente.
    ULTIMO_ANO_LIB: Último ano olímpico em que o Líbano foi registrado sob o
        código ``LIB`` antes da adoção de ``LBN``.
    CORRECOES_OLIMPICAS: Mapeamento de delegações olímpicas especiais ou
        transitórias para seu país correspondente.
    COLUNAS_MEDALHAS: Lista das colunas numéricas de contagem de medalhas.
"""

from pathlib import Path
import pandas as pd


# =============================================================================
# Constantes e mapeamentos
# =============================================================================

# Códigos oficiais dos indicadores World Development Indicators (World Bank):
# - SP.POP.TOTL: população total (habitantes)
# - NY.GDP.MKTP.CD: PIB total (US$ correntes)
# - NY.GDP.PCAP.CD: PIB per capita (US$ correntes)
INDICADORES_WB: dict[str, str] = {
    'SP.POP.TOTL': 'population',
    'NY.GDP.MKTP.CD': 'gdp',
    'NY.GDP.PCAP.CD': 'gdp_per_capita',
}

# Intervalo temporal coletado no World Bank (1960 marca o início da cobertura
# sistemática da maioria das séries macroeconômicas nacionais).
ANO_INICIAL_WB: int = 1960
ANO_FINAL_WB: int = 2025
CAMINHO_CSV_WB: str = 'world_bank.csv'

# Mapeamento explícito de códigos ISO-3 (World Bank) para códigos NOC (COI).
# Códigos idênticos nas duas bases (ex.: USA, BRA, FRA) não precisam constar aqui.
# Nota: `Series.replace(dict)` realiza substituição simultânea, evitando conflitos
# em cadeia como 'CHL' -> 'CHI' ou 'BHR' -> 'BRN' e 'BRN' -> 'BRU'.
ISO_PARA_NOC: dict[str, str] = {
    'DZA': 'ALG', 'AGO': 'ANG', 'ATG': 'ANT', 'ABW': 'ARU', 'ASM': 'ASA',
    'BHS': 'BAH', 'BGD': 'BAN', 'BRB': 'BAR', 'BMU': 'BER', 'BTN': 'BHU',
    'BLZ': 'BIZ', 'BWA': 'BOT', 'BHR': 'BRN', 'BRN': 'BRU', 'BGR': 'BUL',
    'BFA': 'BUR', 'KHM': 'CAM', 'CYM': 'CAY', 'COG': 'CGO', 'TCD': 'CHA',
    'CHL': 'CHI', 'CRI': 'CRC', 'HRV': 'CRO', 'DNK': 'DEN', 'SLV': 'ESA',
    'FJI': 'FIJ', 'GMB': 'GAM', 'GNB': 'GBS', 'GNQ': 'GEQ', 'DEU': 'GER',
    'GRC': 'GRE', 'GRD': 'GRN', 'GTM': 'GUA', 'GIN': 'GUI', 'HTI': 'HAI',
    'HND': 'HON', 'IDN': 'INA', 'IRN': 'IRI', 'VIR': 'ISV', 'VGB': 'IVB',
    'XKX': 'KOS', 'SAU': 'KSA', 'KWT': 'KUW', 'LVA': 'LAT', 'LBY': 'LBA',
    'LSO': 'LES', 'MDG': 'MAD', 'MYS': 'MAS', 'MWI': 'MAW', 'MNG': 'MGL',
    'MCO': 'MON', 'MUS': 'MRI', 'MRT': 'MTN', 'MMR': 'MYA', 'NIC': 'NCA',
    'NLD': 'NED', 'NPL': 'NEP', 'NGA': 'NGR', 'NER': 'NIG', 'OMN': 'OMA',
    'PRY': 'PAR', 'PHL': 'PHI', 'PSE': 'PLE', 'PRT': 'POR', 'PRI': 'PUR',
    'ZAF': 'RSA', 'WSM': 'SAM', 'SYC': 'SEY', 'KNA': 'SKN', 'SVN': 'SLO',
    'SLB': 'SOL', 'LKA': 'SRI', 'SDN': 'SUD', 'CHE': 'SUI', 'TZA': 'TAN',
    'TON': 'TGA', 'TGO': 'TOG', 'ARE': 'UAE', 'URY': 'URU', 'VUT': 'VAN',
    'VNM': 'VIE', 'VCT': 'VIN', 'ZMB': 'ZAM', 'ZWE': 'ZIM',
}

# 'CHI' no World Bank identifica Channel Islands (Ilhas do Canal) e colidiria
# com o código olímpico 'CHI' atribuído ao Chile ('CHL' -> 'CHI').
ISO_REMOVIDO_WB: str = 'CHI'

# O código olímpico do Líbano mudou na base histórica: 'LIB' até 2016 e 'LBN' a partir de 2020.
ULTIMO_ANO_LIB: int = 2016

# Padronizações de delegações olímpicas com correspondência nacional direta
CORRECOES_OLIMPICAS: dict[str, str] = {
    'ROC': 'RUS',  # Comitê Olímpico Russo -> Rússia
    'OAR': 'RUS',  # Atletas Olímpicos da Rússia -> Rússia (Inverno)
}

COLUNAS_MEDALHAS: list[str] = ['gold', 'silver', 'bronze', 'total']


# =============================================================================
# World Bank: coleta, reorganização e padronização
# =============================================================================

def reorganizar_world_bank(
    df: pd.DataFrame,
    indicadores: dict[str, str] = INDICADORES_WB,
) -> pd.DataFrame:
    """Converte o DataFrame bruto da API do World Bank para o formato ``país × ano``.

    A biblioteca ``wbgapi`` retorna os dados em formato largo por ano (uma coluna
    para cada ano numérico e linhas indexadas por país e série). Esta função
    empilha os anos em formato longo (``melt``) e pivota os indicadores em
    colunas distintas (``pivot_table``), renomeando-os conforme ``indicadores``.

    Args:
        df: DataFrame bruto no formato retornado por ``wbgapi.data.DataFrame``,
            contendo as colunas identificadoras ``['economy', 'series', 'Country', 'Series']``
            e colunas numéricas correspondentes aos anos.
        indicadores: Dicionário que mapeia códigos de séries do World Bank
            (chaves) para os nomes de colunas desejados (valores).

    Returns:
        DataFrame estruturado na granularidade ``país × ano``, contendo as
        colunas ``'iso'``, ``'country'``, ``'year'`` (tipo ``int``) e uma coluna
        numérica para cada indicador mapeado.
    """
    # Empilha todas as colunas de anos em uma única coluna 'year'
    df_long = df.melt(
        id_vars=['economy', 'series', 'Country', 'Series'],
        var_name='year',
        value_name='valor',
    )

    # Pivota cada série socioeconômica para sua própria coluna por país e ano
    df_wide = df_long.pivot_table(
        index=['economy', 'Country', 'year'],
        columns='series',
        values='valor',
    ).reset_index()

    df_wide['year'] = df_wide['year'].astype(int)
    return df_wide.rename(columns={**indicadores, 'economy': 'iso', 'Country': 'country'})


def coletar_world_bank(
    caminho_csv: str | Path = CAMINHO_CSV_WB,
    indicadores: dict[str, str] = INDICADORES_WB,
    ano_inicial: int = ANO_INICIAL_WB,
    ano_final: int = ANO_FINAL_WB,
) -> pd.DataFrame:
    """Lê os dados do World Bank do disco ou consulta a API caso o cache não exista.

    Implementa uma estratégia *cache-first*: se o arquivo especificado em
    ``caminho_csv`` já existir localmente, ele é lido diretamente; caso
    contrário, realiza a requisição à API do World Bank via ``wbgapi``, salva o
    resultado bruto em CSV e o carrega em seguida.

    Args:
        caminho_csv: Caminho do arquivo CSV local usado para leitura ou
            persistência dos dados brutos do World Bank.
        indicadores: Dicionário cujas chaves correspondem aos códigos das
            séries do World Bank a serem baixadas.
        ano_inicial: Ano inicial (inclusivo) da série temporal solicitada.
        ano_final: Ano final (inclusivo) da série temporal solicitada.

    Returns:
        DataFrame contendo os dados lidos do CSV local (no formato bruto da API
        ou já reorganizado, dependendo da origem do arquivo).

    Raises:
        ImportError: Se o arquivo local não existir e o pacote ``wbgapi`` não
            estiver instalado no ambiente.
    """
    caminho = Path(caminho_csv)
    if not caminho.exists():
        # Importação tardia para evitar dependência de rede/pacote quando o CSV já existe
        import wbgapi as wb

        df_wb = wb.data.DataFrame(
            indicadores.keys(),
            time=range(ano_inicial, ano_final + 1),
            labels=True,
            numericTimeKeys=True,
        ).reset_index()
        df_wb.to_csv(caminho, index=False)

    return pd.read_csv(caminho)


def adicionar_noc_world_bank(df: pd.DataFrame) -> pd.DataFrame:
    """Cria a coluna ``noc`` a partir do código ISO-3 para junção com os dados olímpicos.

    Remove o código ``ISO_REMOVIDO_WB`` (``'CHI'``, Channel Islands) para evitar
    ambiguidade com o Chile, aplica o dicionário ``ISO_PARA_NOC`` e ajusta a
    transição histórica do código olímpico do Líbano (``LIB`` até 2016 e
    ``LBN`` a partir de 2020).

    Args:
        df: DataFrame do World Bank contendo ao menos as colunas ``'iso'`` e
            ``'year'``.

    Returns:
        Cópia do DataFrame sem o registro ``ISO_REMOVIDO_WB`` e acrescida da
        coluna ``'noc'`` padronizada segundo o padrão do COI.
    """
    df_out = df[df['iso'] != ISO_REMOVIDO_WB].copy()
    df_out['noc'] = df_out['iso'].replace(ISO_PARA_NOC)

    # Transição histórica do código olímpico do Líbano (LIB até 2016; LBN a partir de 2020)
    df_out.loc[(df_out['iso'] == 'LBN') & (df_out['year'] <= ULTIMO_ANO_LIB), 'noc'] = 'LIB'
    df_out.loc[(df_out['iso'] == 'LBN') & (df_out['year'] > ULTIMO_ANO_LIB), 'noc'] = 'LBN'

    return df_out


def preparar_world_bank(
    caminho_csv: str | Path = CAMINHO_CSV_WB,
    indicadores: dict[str, str] = INDICADORES_WB,
) -> pd.DataFrame:
    """Carrega, estrutura em ``país × ano`` e padroniza códigos ISO para NOC.

    Orquestra a coleta e a limpeza da base socioeconômica, detectando
    automaticamente se o CSV carregado está no formato bruto da API (presença
    da coluna ``'series'``) ou se já foi previamente pivotado.

    Args:
        caminho_csv: Caminho do arquivo CSV local do World Bank.
        indicadores: Dicionário de mapeamento entre códigos das séries do World
            Bank e nomes das colunas de saída.

    Returns:
        DataFrame pronto para integração, indexado logicamente por
        ``('year', 'noc')``, com colunas ``'iso'``, ``'country'``, ``'year'``,
        ``'noc'`` e os indicadores socioeconômicos renomeados.
    """
    df_wb = coletar_world_bank(caminho_csv, indicadores=indicadores)

    # Se o CSV veio direto do formato bruto da API, reorganiza para país × ano
    if 'series' in df_wb.columns:
        df_wb = reorganizar_world_bank(df_wb, indicadores=indicadores)
    else:
        df_wb = df_wb.copy()
        df_wb['year'] = df_wb['year'].astype(int)

    return adicionar_noc_world_bank(df_wb)


# =============================================================================
# Dados olímpicos: filtragem e agregação
# =============================================================================

def filtrar_verao_e_padronizar_noc(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra apenas os Jogos Olímpicos de Verão e padroniza códigos NOC equivalentes.

    Args:
        df: DataFrame bruto olímpico (quadro de medalhas ou atletas) contendo
            ao menos as colunas ``'season'`` e ``'noc'``.

    Returns:
        Cópia do DataFrame restrita às linhas em que ``season == 'Summer'``,
        com códigos transitórios substituídos segundo ``CORRECOES_OLIMPICAS``.
    """
    df_verao = df[df['season'] == 'Summer'].copy()
    df_verao['noc'] = df_verao['noc'].replace(CORRECOES_OLIMPICAS)
    return df_verao


def agregar_medalhas_por_pais_edicao(df_medalhas: pd.DataFrame) -> pd.DataFrame:
    """Consolida o total de medalhas por ``ano`` e ``NOC``.

    A agregação por ``['year', 'noc']`` é necessária para unificar subedições
    realizadas no mesmo ano olímpico (caso dos Jogos de 1956, cujas provas
    hípicas ocorreram em Estocolmo e as demais modalidades em Melbourne) e
    eventuais delegações unificadas após correção de NOC.

    Args:
        df_medalhas: DataFrame de medalhas já filtrado para os Jogos de Verão,
            contendo ``'year'``, ``'noc'``, ``'country'``, ``'gold'``,
            ``'silver'``, ``'bronze'`` e ``'total'``.

    Returns:
        DataFrame agregado com uma linha única por ``('year', 'noc')``,
        preservando o primeiro nome de país observado e a soma das medalhas.
    """
    return (
        df_medalhas
        .groupby(['year', 'noc'], as_index=False)
        .agg(
            country=('country', 'first'),
            gold=('gold', 'sum'),
            silver=('silver', 'sum'),
            bronze=('bronze', 'sum'),
            total=('total', 'sum'),
        )
    )


def construir_base_olimpica(
    df_medalhas: pd.DataFrame,
    df_atletas: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói a base ``país × edição`` incluindo delegações sem medalhas.

    Como o quadro oficial de medalhas registra apenas as delegações que
    subiram ao pódio, utiliza-se a tabela de participação individual
    (``df_atletas``) para identificar todos os ``('year', 'noc')`` presentes em
    cada edição, preenchendo com ``0`` as medalhas dos não medalhistas.

    Args:
        df_medalhas: DataFrame de medalhas dos Jogos de Verão.
        df_atletas: DataFrame de participações de atletas dos Jogos de Verão,
            contendo ao menos as colunas ``'year'`` e ``'noc'``.

    Returns:
        DataFrame na granularidade ``país × edição`` com todas as delegações
        participantes e colunas inteiras ``'gold'``, ``'silver'``, ``'bronze'``
        e ``'total'``.

    Raises:
        pandas.errors.MergeError: Se houver duplicidade na chave ``('year', 'noc')``
            após a agregação de medalhas (violação de ``validate='one_to_one'``).
    """
    df_medalhas_pais_edicao = agregar_medalhas_por_pais_edicao(df_medalhas)
    # Universo completo de delegações participantes em cada edição
    df_participantes = df_atletas[['year', 'noc']].drop_duplicates()

    df_olimpico = df_participantes.merge(
        df_medalhas_pais_edicao,
        on=['year', 'noc'],
        how='left',
        validate='one_to_one',
    )

    df_olimpico[COLUNAS_MEDALHAS] = df_olimpico[COLUNAS_MEDALHAS].fillna(0).astype(int)
    return df_olimpico


# =============================================================================
# Integração das bases, carregamento principal e diagnóstico
# =============================================================================

def combinar_com_world_bank(
    df_olimpico: pd.DataFrame,
    df_world_bank: pd.DataFrame,
) -> pd.DataFrame:
    """Une os dados olímpicos aos indicadores socioeconômicos por ``ano`` e ``NOC``.

    Realiza um *left join* preservando todas as participações olímpicas (inclusive
    edições anteriores a 1960 ou NOCs históricos sem série no World Bank) e
    consolida o nome do país priorizando o registro olímpico, seguido pelo nome
    do World Bank e, em último caso, pelo próprio código NOC.

    Args:
        df_olimpico: DataFrame olímpico na granularidade ``país × edição``.
        df_world_bank: DataFrame padronizado do World Bank na granularidade
            ``país × ano`` contendo a coluna ``'noc'``.

    Returns:
        DataFrame integrado sem as colunas auxiliares de junção
        (``'country_olimpico'``, ``'country_wb'`` e ``'iso'``).

    Raises:
        pandas.errors.MergeError: Se a chave ``('year', 'noc')`` não for única
            em ambas as tabelas (violação de ``validate='one_to_one'``).
    """
    df_merged = df_olimpico.merge(
        df_world_bank,
        on=['year', 'noc'],
        how='left',
        suffixes=('_olimpico', '_wb'),
        validate='one_to_one',
    )

    # Delegações sem medalhas chegam com country_olimpico nulo e herdam o nome do World Bank
    df_merged['country'] = (
        df_merged['country_olimpico']
        .fillna(df_merged['country_wb'])
        .fillna(df_merged['noc'])
    )

    colunas_auxiliares = [
        col for col in ('country_olimpico', 'country_wb', 'iso') if col in df_merged.columns
    ]
    return df_merged.drop(columns=colunas_auxiliares)


def listar_noc_sem_world_bank(
    df_olimpico: pd.DataFrame,
    df_world_bank: pd.DataFrame,
    ano_inicial: int = 1960,
    ano_final: int = 2024,
) -> pd.DataFrame:
    """Diagnostica os NOCs participantes sem correspondência no World Bank no período.

    Identifica delegações presentes nos Jogos de Verão entre ``ano_inicial`` e
    ``ano_final`` que não encontram par ``('year', 'noc')`` na base do World
    Bank (como estados históricos extintos, territórios ultramarinos ou equipes
    independentes), resumindo seu impacto em edições e medalhas.

    Args:
        df_olimpico: DataFrame olímpico integrado ou base na granularidade
            ``país × edição``.
        df_world_bank: DataFrame padronizado do World Bank contendo ``'year'``
            e ``'noc'``.
        ano_inicial: Ano inicial (inclusivo) da janela de diagnóstico.
        ano_final: Ano final (inclusivo) da janela de diagnóstico.

    Returns:
        DataFrame ordenado de forma decrescente por ``'medalhas'`` e
        ``'edicoes'``, contendo as colunas ``['noc', 'pais', 'edicoes', 'primeiro_ano', 'ultimo_ano', 'medalhas']``.
    """
    participantes = df_olimpico[df_olimpico['year'].between(ano_inicial, ano_final)]
    chaves_wb = df_world_bank[['year', 'noc']].drop_duplicates()

    comparacao = participantes.merge(
        chaves_wb,
        on=['year', 'noc'],
        how='left',
        indicator=True,
    )
    sem_registro = comparacao[comparacao['_merge'] == 'left_only']

    return (
        sem_registro
        .groupby('noc', as_index=False)
        .agg(
            pais=('country', 'first'),
            edicoes=('year', 'nunique'),
            primeiro_ano=('year', 'min'),
            ultimo_ano=('year', 'max'),
            medalhas=('total', 'sum'),
        )
        .assign(pais=lambda d: d['pais'].fillna(d['noc']))
        .sort_values(['medalhas', 'edicoes'], ascending=False)
        .reset_index(drop=True)
    )


def carregar_bases_brutas(
    caminho_medalhas: str | Path = 'medal_table.csv',
    caminho_atletas: str | Path = 'olympic_athletes.csv',
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega os arquivos CSV olímpicos filtrados para os Jogos de Verão.

    Args:
        caminho_medalhas: Caminho para o arquivo CSV do quadro de medalhas.
        caminho_atletas: Caminho para o arquivo CSV de registros de atletas.

    Returns:
        Tupla ``(df_medalhas, df_atletas)`` contendo ambos os DataFrames
        filtrados para ``season == 'Summer'`` e com códigos NOC padronizados.

    Raises:
        FileNotFoundError: Se algum dos arquivos CSV informados não existir.
    """
    df_medalhas = filtrar_verao_e_padronizar_noc(pd.read_csv(caminho_medalhas))
    df_atletas = filtrar_verao_e_padronizar_noc(pd.read_csv(caminho_atletas))
    return df_medalhas, df_atletas


def carregar_bases(
    caminho_medalhas: str | Path = 'medal_table.csv',
    caminho_atletas: str | Path = 'olympic_athletes.csv',
    caminho_wb: str | Path = CAMINHO_CSV_WB,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Executa o pipeline completo e retorna as bases integradas para análise.

    Ponto de entrada principal do módulo para o notebook de análise
    exploratória. Integra os registros olímpicos de Verão com os indicadores
    socioeconômicos do World Bank na unidade ``país × edição olímpica``.

    Args:
        caminho_medalhas: Caminho para o CSV do quadro de medalhas.
        caminho_atletas: Caminho para o CSV de participações de atletas.
        caminho_wb: Caminho para o CSV local do World Bank (criado via API
            caso ainda não exista).

    Returns:
        Tupla ``(df_olimpico_completo, df_socioeconomico)``, onde:
            - ``df_olimpico_completo``: Cobre todas as edições de Verão de
              1896 a 2024 (incluindo delegações sem medalhas com ``total = 0``).
            - ``df_socioeconomico``: Subconjunto de ``df_olimpico_completo``
              restrito ao recorte de 1960 a 2024 com cobertura do World Bank.

    Raises:
        FileNotFoundError: Se os arquivos CSV olímpicos não forem encontrados.
        pandas.errors.MergeError: Se houver violação de unicidade na chave
            ``('year', 'noc')`` durante a construção ou junção das bases.
    """
    df_medalhas, df_atletas = carregar_bases_brutas(caminho_medalhas, caminho_atletas)
    df_wb = preparar_world_bank(caminho_wb)

    df_olimpico = construir_base_olimpica(df_medalhas, df_atletas)
    df_olimpico_completo = combinar_com_world_bank(df_olimpico, df_wb)
    df_socioeconomico = df_olimpico_completo[
        df_olimpico_completo['year'].between(1960, 2024)
    ].copy()

    return df_olimpico_completo, df_socioeconomico