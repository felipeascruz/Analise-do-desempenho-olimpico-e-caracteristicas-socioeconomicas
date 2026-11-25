"""Módulo unificado de coleta, limpeza, padronização e integração das bases.

Centraliza o pipeline de preparação de dados do projeto para manter o notebook
principal focado na análise exploratória e nas visualizações:

1. Coleta e reorganização dos indicadores do World Bank (população, PIB e PIB per capita);
2. Padronização dos códigos de país (ISO-3 do World Bank -> NOC olímpico);
3. Filtragem dos Jogos de Verão, padronização de NOCs e agregação de subedições (1956);
4. Construção da base país × edição incluindo delegações participantes sem medalhas;
5. Junção com os indicadores socioeconômicos e diagnóstico de NOCs sem correspondência.
"""

from pathlib import Path
import pandas as pd


# =============================================================================
# Constantes e mapeamentos
# =============================================================================

# Códigos oficiais dos indicadores do World Bank e colunas correspondentes:
# SP.POP.TOTL: população total
# NY.GDP.MKTP.CD: PIB (US$ correntes)
# NY.GDP.PCAP.CD: PIB per capita (US$ correntes)
INDICADORES_WB: dict[str, str] = {
    'SP.POP.TOTL': 'population',
    'NY.GDP.MKTP.CD': 'gdp',
    'NY.GDP.PCAP.CD': 'gdp_per_capita',
}

ANO_INICIAL_WB: int = 1960
ANO_FINAL_WB: int = 2025
CAMINHO_CSV_WB: str = 'world_bank.csv'

# Mapeamento explícito de códigos ISO-3 (World Bank) para códigos NOC (COI).
# Códigos já idênticos nas duas bases (ex.: USA, BRA, FRA) não precisam constar aqui.
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

# CHI no World Bank corresponde a Channel Islands e conflita com o NOC CHI do Chile.
ISO_REMOVIDO_WB: str = 'CHI'

# O código olímpico do Líbano mudou na base: LIB até 2016 e LBN a partir de 2020.
ULTIMO_ANO_LIB: int = 2016

# Padronizações de delegações olímpicas com correspondência direta
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
    """Converte o formato bruto da API (um ano por coluna) para país × ano."""
    df_long = df.melt(
        id_vars=['economy', 'series', 'Country', 'Series'],
        var_name='year',
        value_name='valor',
    )

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
    """Lê o CSV local do World Bank ou realiza a coleta via API se ausente."""
    caminho = Path(caminho_csv)
    if not caminho.exists():
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
    """Cria a coluna 'noc' a partir do código ISO para junção com os dados olímpicos."""
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
    """Carrega, estrutura em país × ano e padroniza códigos ISO para NOC."""
    df_wb = coletar_world_bank(caminho_csv, indicadores=indicadores)

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
    """Mantém apenas os Jogos Olímpicos de Verão e padroniza códigos NOC equivalentes."""
    df_verao = df[df['season'] == 'Summer'].copy()
    df_verao['noc'] = df_verao['noc'].replace(CORRECOES_OLIMPICAS)
    return df_verao


def agregar_medalhas_por_pais_edicao(df_medalhas: pd.DataFrame) -> pd.DataFrame:
    """Soma as medalhas por ano e NOC (unificando Melbourne e Estocolmo em 1956)."""
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
    """Constrói a base país × edição com todos os participantes (zero medalhas incluídos)."""
    df_medalhas_pais_edicao = agregar_medalhas_por_pais_edicao(df_medalhas)
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
    """Une os dados olímpicos aos indicadores socioeconômicos por ano e NOC."""
    df_merged = df_olimpico.merge(
        df_world_bank,
        on=['year', 'noc'],
        how='left',
        suffixes=('_olimpico', '_wb'),
        validate='one_to_one',
    )

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
    """Lista os NOCs participantes sem registro correspondente no World Bank no período."""
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
    """Carrega quadro de medalhas e atletas filtrados para Jogos de Verão."""
    df_medalhas = filtrar_verao_e_padronizar_noc(pd.read_csv(caminho_medalhas))
    df_atletas = filtrar_verao_e_padronizar_noc(pd.read_csv(caminho_atletas))
    return df_medalhas, df_atletas


def carregar_bases(
    caminho_medalhas: str | Path = 'medal_table.csv',
    caminho_atletas: str | Path = 'olympic_athletes.csv',
    caminho_wb: str | Path = CAMINHO_CSV_WB,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Constrói as bases integradas na unidade país × edição olímpica.

    Retorna:
        df_olimpico_completo: Jogos de Verão de 1896 a 2024 (inclui não medalhistas com total = 0).
        df_socioeconomico: Recorte de 1960 a 2024 integrado aos indicadores do World Bank.
    """
    df_medalhas, df_atletas = carregar_bases_brutas(caminho_medalhas, caminho_atletas)
    df_wb = preparar_world_bank(caminho_wb)

    df_olimpico = construir_base_olimpica(df_medalhas, df_atletas)
    df_olimpico_completo = combinar_com_world_bank(df_olimpico, df_wb)
    df_socioeconomico = df_olimpico_completo[
        df_olimpico_completo['year'].between(1960, 2024)
    ].copy()

    return df_olimpico_completo, df_socioeconomico
