"""Estilo gráfico dos gráficos do notebook, inspirado nos princípios de Edward Tufte.

Princípios aplicados:

- Máxima razão dados/tinta: sem grade, sem bordas superior e direita e sem
  caixas de legenda;
- Moldura de intervalo (*range frame*): os eixos cobrem apenas a extensão dos
  dados;
- Rótulos diretos nas linhas e valores escritos nas barras, no lugar de
  legendas e eixos redundantes;
- Título e subtítulo informativos à esquerda, dispensando rótulos no eixo
  vertical;
- Cores discretas da paleta Okabe-Ito, padronizadas entre as perguntas 5 a 8
  do notebook.

Fundo, texto e eixos herdam o tema ativo do notebook (``rcParams`` do
matplotlib): o módulo altera apenas a família tipográfica e aplica a cor do
texto do tema, com transparência, nos elementos estruturais de apoio. As cores
da paleta mantêm contraste mínimo de 3:1 tanto sobre fundo claro quanto sobre
fundo escuro.

Attributes:
    COR_POPULACAO: Cor hexadecimal (verde Okabe-Ito) associada à variável
        população.
    COR_PIB: Cor hexadecimal (azul Okabe-Ito) associada ao PIB total.
    COR_PIB_PER_CAPITA: Cor hexadecimal (laranja-avermelhado Okabe-Ito)
        associada ao PIB per capita.
    COR_PRIMARIA: Cor padrão para séries únicas ou principais sem indicador
        socioeconômico específico.
    COR_SECUNDARIA: Cor padrão para séries secundárias de comparação.
    COR_POSITIVA: Cor utilizada para valores ou desvios positivos.
    COR_NEGATIVA: Cor utilizada para valores ou desvios negativos.
    DESLOCAMENTO_EIXOS: Distância padrão, em pontos tipográficos, entre os
        eixos (``spines``) e a área de plotagem dos dados.
    NOMES_ORDENS: Dicionário que associa expoentes múltiplos de 3 às formas
        no singular e no plural das ordens de grandeza em português.
"""

import math

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D


# =============================================================================
# Constantes
# =============================================================================

# Paleta Okabe-Ito (segura para daltonismo), com significado fixo nas perguntas 5 a 8
COR_POPULACAO = '#009E73'
COR_PIB = '#0072B2'
COR_PIB_PER_CAPITA = '#D55E00'

# Cores semânticas para séries genéricas e gráficos divergentes
COR_PRIMARIA = COR_PIB
COR_SECUNDARIA = COR_PIB_PER_CAPITA
COR_POSITIVA = COR_PIB
COR_NEGATIVA = COR_PIB_PER_CAPITA

# Distância (em pontos) entre os eixos externos e a área de dados
DESLOCAMENTO_EIXOS = 8

# Nomes das ordens de grandeza em português: expoente -> (singular, plural)
NOMES_ORDENS = {
    3: ('mil', 'mil'),
    6: ('milhão', 'milhões'),
    9: ('bilhão', 'bilhões'),
    12: ('trilhão', 'trilhões')
}


# =============================================================================
# Estilo e cores
# =============================================================================

def estilo_tufte():
    """Cria um gerenciador de contexto com o estilo visual minimalista do projeto.

    Altera temporariamente a família de fonte para serifada e desativa grades e
    bordas superior e direita, preservando as cores de fundo e texto do tema
    configurado no notebook. Todo o código de construção e exibição do gráfico
    (incluindo ``plt.show()``) deve permanecer dentro do bloco ``with``.

    Returns:
        Objeto ``matplotlib.rc_context`` com as configurações de estilo
        aplicadas durante a execução do bloco.
    """
    return plt.rc_context({
        'font.family': 'serif',
        'axes.grid': False,
        'axes.spines.top': False,
        'axes.spines.right': False
    })


def cor_neutra(opacidade=0.6):
    """Retorna a cor de texto do tema atual com canal alfa ajustado.

    Permite criar tons neutros (cinzas) para eixos, marcas e anotações de apoio
    que se adaptam automaticamente a temas claros ou escuros do notebook.

    Args:
        opacidade: Valor alfa entre ``0.0`` (totalmente transparente) e ``1.0``
            (totalmente opaco).

    Returns:
        Tupla RGBA ``(r, g, b, a)`` compatível com o matplotlib.
    """
    return to_rgba(plt.rcParams['text.color'], opacidade)


# =============================================================================
# Formatação de números
# =============================================================================

def formatar_numero(valor, casas=None, sinal=False):
    """Formata um número utilizando vírgula como separador decimal.

    Quando ``casas`` não é especificado, valores inteiros (como ``2.0``) são
    exibidos sem casas decimais e valores fracionários recebem uma casa
    decimal. Aplica arredondamento de 10 casas decimais antes de verificar se o
    valor é inteiro para evitar ruído binário de ponto flutuante (IEEE 754).

    Args:
        valor: Número inteiro ou de ponto flutuante a ser formatado.
        casas: Quantidade fixa de casas decimais. Se ``None``, determina
            automaticamente entre ``0`` (inteiros) e ``1`` (decimais).
        sinal: Se ``True``, inclui explicitamente o sinal ``+`` para valores
            positivos e ``-`` para negativos.

    Returns:
        Representação textual do número formatado no padrão decimal brasileiro.
    """
    valor_limpo = round(float(valor), 10)
    if casas is None:
        casas = 0 if valor_limpo.is_integer() else 1

    texto = f'{valor_limpo:+.{casas}f}' if sinal else f'{valor_limpo:.{casas}f}'
    return texto.replace('.', ',')


def formatar_potencia_de_dez(valor, prefixo=''):
    """Escreve uma potência de dez por extenso em escala curta (mil, milhão, bilhão).

    Converte valores numéricos (como ``10**6`` ou ``10**10``) em rótulos
    legíveis (``'1 milhão'``, ``'10 bilhões'``), concordando o substantivo em
    número conforme o multiplicador.

    Args:
        valor: Valor numérico positivo correspondente a uma potência de dez.
        prefixo: Texto opcional inserido antes do número (por exemplo, ``'US$ '``).

    Returns:
        String formatada com o prefixo, o fator numérico e a ordem de grandeza
        por extenso.

    Raises:
        ValueError: Se ``valor`` não for estritamente positivo.
    """
    if valor <= 0:
        raise ValueError("O parâmetro 'valor' deve ser estritamente positivo.")

    expoente = round(math.log10(valor))
    # Agrupa o expoente na ordem de milhar imediatamente inferior (0, 3, 6, 9 ou 12)
    ordem = min(max(expoente // 3 * 3, 0), 12)
    quantidade = 10 ** (expoente - ordem)

    if ordem == 0:
        return f'{prefixo}{quantidade}'

    singular, plural = NOMES_ORDENS[ordem]
    return f'{prefixo}{quantidade} {singular if quantidade == 1 else plural}'


# =============================================================================
# Marcações dos eixos
# =============================================================================

def marcas_do_eixo(minimo, maximo, alvo=5):
    """Calcula marcas numéricas "redondas" dentro do intervalo especificado.

    Seleciona um passo baseado em múltiplos de ``1``, ``2``, ``2,5`` ou ``5``
    de uma potência de dez de modo que a quantidade resultante de marcas fique
    o mais próximo possível de ``alvo``. Inclui guardas para intervalos
    degenerados (``minimo == maximo``) e arredondamento de precisão para evitar
    imprecisões binárias IEEE 754 em passos decimais.

    Args:
        minimo: Limite inferior do intervalo de dados.
        maximo: Limite superior do intervalo de dados.
        alvo: Quantidade aproximada de marcações desejadas no eixo (deve ser > 0).

    Returns:
        Lista ordenada de valores (``int`` quando exatos, ``float`` caso
        contrário) contidos em ``[minimo, maximo]``.

    Raises:
        ValueError: Se ``alvo <= 0`` ou se ``maximo < minimo``.
    """
    if alvo <= 0:
        raise ValueError("O parâmetro 'alvo' deve ser estritamente positivo.")
    if maximo < minimo:
        raise ValueError("O parâmetro 'maximo' deve ser maior ou igual a 'minimo'.")

    amplitude = maximo - minimo
    if math.isclose(amplitude, 0.0, abs_tol=1e-12):
        valor_unico = round(float(minimo), 10)
        return [int(valor_unico) if valor_unico.is_integer() else valor_unico]

    base = 10 ** math.floor(math.log10(amplitude / alvo))
    candidatos = [fator * base * 10 ** k for k in (0, 1) for fator in (1, 2, 2.5, 5)]
    passo = min(candidatos, key=lambda p: abs(amplitude / p - alvo))

    marca = math.ceil(minimo / passo) * passo
    marcas = []
    # Tolerância de 1e-9 evita perda da última marca; round(..., 10) evita ruído IEEE 754
    while marca <= maximo + 1e-9:
        marca_limpa = round(marca, 10)
        marcas.append(int(marca_limpa) if float(marca_limpa).is_integer() else marca_limpa)
        marca += passo

    return marcas


def marcas_de_anos(anos, passo=20):
    """Gera uma lista de anos múltiplos de ``passo`` dentro do período dos dados.

    Args:
        anos: Série ou array numérico contendo os anos presentes no gráfico.
        passo: Intervalo em anos entre marcações consecutivas.

    Returns:
        Lista de anos inteiros múltiplos de ``passo`` contidos entre o mínimo e
        o máximo de ``anos``.
    """
    return list(range((anos.min() // passo + 1) * passo, anos.max() + 1, passo))


def definir_marcas_y(ax, marcas, sufixo=''):
    """Define posições e rótulos formatados com vírgula decimal no eixo vertical.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` alvo da formatação.
        marcas: Sequência de valores numéricos onde os ticks serão posicionados.
        sufixo: Texto opcional anexado após cada número (por exemplo, ``'%'``).
    """
    ax.set_yticks(marcas)
    ax.set_yticklabels([f'{formatar_numero(marca)}{sufixo}' for marca in marcas])


def eixo_log_em_potencias_de_dez(ax, valores, prefixo=''):
    """Configura o eixo horizontal em escala logarítmica com rótulos por extenso.

    Posiciona marcações apenas nas potências inteiras de 10 compreendidas no
    intervalo de ``valores`` e desativa os sub-ticks logarítmicos intermediários
    para reduzir ruído visual. Valida previamente se os dados são estritamente
    positivos.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` a ser configurado.
        valores: Série ou array positivo usado para determinar a menor e a
            maior potência de 10 do eixo.
        prefixo: Prefixo opcional passado a ``formatar_potencia_de_dez``
            (por exemplo, ``'US$ '``).

    Raises:
        ValueError: Se ``valores`` não contiver números válidos ou possuir
            valores menores ou iguais a zero.
    """
    valores_validos = [float(v) for v in valores if v is not None and not math.isnan(float(v))]
    if not valores_validos:
        raise ValueError("A sequência 'valores' não contém valores numéricos válidos.")

    valor_min = min(valores_validos)
    valor_max = max(valores_validos)
    if valor_min <= 0:
        raise ValueError('A escala logarítmica exige valores estritamente positivos (> 0).')

    ax.set_xscale('log')

    primeiro = math.ceil(math.log10(valor_min))
    ultimo = math.floor(math.log10(valor_max))
    if primeiro > ultimo:
        primeiro = math.floor(math.log10(valor_min))
        ultimo = math.ceil(math.log10(valor_max))

    marcas = [10 ** expoente for expoente in range(primeiro, ultimo + 1)]

    ax.set_xticks(marcas)
    ax.set_xticklabels([formatar_potencia_de_dez(marca, prefixo) for marca in marcas])
    ax.minorticks_off()


# =============================================================================
# Elementos do gráfico
# =============================================================================

def moldura_de_intervalo(ax, x_min, x_max, y_min, y_max, deslocamento=DESLOCAMENTO_EIXOS):
    """Aplica uma moldura de intervalo (*range frame*) aos eixos esquerdo e inferior.

    Limita o traçado das linhas dos eixos exatamente aos intervalos
    ``[x_min, x_max]`` e ``[y_min, y_max]`` e desloca-os para fora da área de
    dados para evitar colisão entre pontos extremos e as bordas.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` a ser estilizado.
        x_min: Limite inferior do traçado do eixo horizontal.
        x_max: Limite superior do traçado do eixo horizontal.
        y_min: Limite inferior do traçado do eixo vertical.
        y_max: Limite superior do traçado do eixo vertical.
        deslocamento: Afastamento dos eixos para fora da área de dados, em
            pontos tipográficos.
    """
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)

    ax.spines['left'].set_bounds(y_min, y_max)
    ax.spines['bottom'].set_bounds(x_min, x_max)

    for lado in ('left', 'bottom'):
        ax.spines[lado].set_position(('outward', deslocamento))
        ax.spines[lado].set_color(cor_neutra())

    ax.tick_params(length=3, color=cor_neutra(), labelcolor=cor_neutra(0.8), labelsize=10)


def titulo_e_subtitulo(ax, titulo, subtitulo, recuo=DESLOCAMENTO_EIXOS):
    """Adiciona título e subtítulo alinhados à esquerda acima da área de plotagem.

    O subtítulo descreve a variável e a unidade do eixo vertical, dispensando
    um ``ylabel`` tradicional.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` onde os textos serão ancorados.
        titulo: Texto principal do gráfico.
        subtitulo: Texto explicativo secundário posicionado logo abaixo do
            título.
        recuo: Deslocamento horizontal para a esquerda (em pontos) utilizado
            para alinhar os textos ao eixo vertical deslocado.
    """
    ax.annotate(
        titulo,
        xy=(0, 1), xycoords='axes fraction',
        xytext=(-recuo, 36), textcoords='offset points',
        ha='left', va='bottom', fontsize=15
    )
    ax.annotate(
        subtitulo,
        xy=(0, 1), xycoords='axes fraction',
        xytext=(-recuo, 14), textcoords='offset points',
        ha='left', va='bottom', fontsize=11, color=cor_neutra(0.75)
    )


def rotular_ponto(ax, x, y, texto, cor, deslocamento=(8, 0), alinhamento='left'):
    """Insere um rótulo direto próximo a um ponto específico do gráfico.

    Utilizado para identificar séries diretamente na extremidade das linhas ou
    destacar observações relevantes sem recorrer a caixas de legenda. Quando
    múltiplas séries terminam com valores verticais próximos, ajuste
    ``deslocamento=(dx, dy)`` por série (ou utilize ``rotular_series_finais``)
    para evitar sobreposição textual.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` alvo da anotação.
        x: Coordenada horizontal do ponto de referência nos dados.
        y: Coordenada vertical do ponto de referência nos dados.
        texto: Rótulo textual a ser exibido.
        cor: Cor do texto (geralmente idêntica à da série correspondente).
        deslocamento: Tupla ``(dx, dy)`` com o afastamento do texto em pontos.
        alinhamento: Alinhamento horizontal do texto (``'left'``, ``'center'``
            ou ``'right'``).
    """
    ax.annotate(
        texto,
        xy=(x, y),
        xytext=deslocamento,
        textcoords='offset points',
        ha=alinhamento,
        va='center',
        color=cor,
        fontsize=11,
        annotation_clip=False
    )


def rotular_series_finais(ax, pontos, deslocamento_x=8, distancia_minima_pt=14):
    """Posiciona rótulos diretos no fim de múltiplas séries evitando sobreposição vertical.

    Ordena os pontos finais pela coordenada vertical e ajusta o deslocamento ``dy``
    (em pontos tipográficos) sempre que dois rótulos adjacentes ficarem a menos
    de ``distancia_minima_pt`` um do outro.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` alvo das anotações.
        pontos: Sequência de tuplas ``(x, y, texto, cor)`` representando o ponto
            final de cada série.
        deslocamento_x: Afastamento horizontal padrão em pontos à direita de ``x``.
        distancia_minima_pt: Separação vertical mínima desejada entre rótulos
            consecutivos, em pontos tipográficos.
    """
    if not pontos:
        return

    ordenados = sorted(pontos, key=lambda item: item[1])
    pts_por_pixel = 72.0 / ax.figure.dpi
    posicoes_y_pt = [
        ax.transData.transform((x, y))[1] * pts_por_pixel
        for x, y, _, _ in ordenados
    ]

    posicoes_ajustadas = list(posicoes_y_pt)
    for i in range(1, len(posicoes_ajustadas)):
        diferenca = posicoes_ajustadas[i] - posicoes_ajustadas[i - 1]
        if diferenca < distancia_minima_pt:
            posicoes_ajustadas[i] = posicoes_ajustadas[i - 1] + distancia_minima_pt

    # Centraliza o conjunto deslocado em torno do centro original
    desvio_medio = sum(a - o for a, o in zip(posicoes_ajustadas, posicoes_y_pt)) / len(posicoes_y_pt)
    posicoes_ajustadas = [pos - desvio_medio for pos in posicoes_ajustadas]

    for (x, y, texto, cor), y_orig, y_novo in zip(ordenados, posicoes_y_pt, posicoes_ajustadas):
        dy = round(y_novo - y_orig, 1)
        rotular_ponto(ax, x, y, texto, cor, deslocamento=(deslocamento_x, dy))


def rotular_painel(ax, texto, cor):
    """Adiciona um título interno colorido no canto superior esquerdo de um painel.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` correspondente ao subpainel.
        texto: Rótulo identificador do painel.
        cor: Cor aplicada ao texto.
    """
    ax.text(0.02, 0.97, texto, transform=ax.transAxes, ha='left', va='top', color=cor, fontsize=12)


def rotulo_do_eixo(ax, texto):
    """Adiciona um rótulo discreto ao eixo horizontal quando a unidade não é autoevidente.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` alvo.
        texto: Descrição da variável representada no eixo horizontal.
    """
    ax.set_xlabel(texto, fontsize=11, color=cor_neutra(0.75), labelpad=10)


def legenda_sem_moldura(ax, itens, loc='lower left'):
    """Cria uma legenda minimalista sem borda para diferenciar estilos de linha.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` onde a legenda será inserida.
        itens: Sequência de tuplas ``(rotulo, estilo_linha)`` (por exemplo,
            ``[('Série A', '-'), ('Série B', '--')]``).
        loc: Posição da legenda conforme convenção do ``ax.legend``.
    """
    manipuladores = [Line2D([], [], color=cor_neutra(0.8), linestyle=estilo) for _, estilo in itens]
    ax.legend(manipuladores, [rotulo for rotulo, _ in itens], frameon=False, loc=loc, fontsize=10)


# =============================================================================
# Barras
# =============================================================================

def barras_com_valores(ax, rotulos, valores, cor, casas=2):
    """Desenha um gráfico de barras verticais finas com valores anotados no topo.

    Remove o eixo vertical e exibe os valores diretamente sobre cada barra,
    eliminando a necessidade de marcas ou grades horizontais.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` alvo.
        rotulos: Sequência com os nomes das categorias do eixo horizontal.
        valores: Sequência numérica com as alturas das barras.
        cor: Cor de preenchimento das barras.
        casas: Número de casas decimais exibidas nos rótulos sobre as barras.
    """
    valores = list(valores)
    posicoes = range(len(valores))

    ax.bar(posicoes, valores, width=0.45, color=cor)

    for posicao, valor in zip(posicoes, valores):
        ax.annotate(
            formatar_numero(valor, casas),
            xy=(posicao, valor), xytext=(0, 5), textcoords='offset points',
            ha='center', va='bottom', fontsize=12
        )

    _acabamento_das_barras(ax, rotulos, max(valores))


def barras_agrupadas_com_valores(ax, rotulos, series, casas=2):
    """Desenha barras verticais agrupadas com rótulos numéricos e legenda colorida.

    Cada série é posicionada lado a lado dentro de cada categoria e identificada
    por uma legenda sem moldura cujos textos assumem a cor da respectiva barra.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` alvo.
        rotulos: Sequência com os nomes das categorias do eixo horizontal.
        series: Dicionário no formato ``{nome_serie: (valores, cor)}`` contendo
            os valores e a cor de cada grupo.
        casas: Número de casas decimais exibidas acima de cada barra.
    """
    largura_total = 0.7
    largura = largura_total / len(series)
    maximo = 0

    for k, (nome, (valores, cor)) in enumerate(series.items()):
        valores = list(valores)
        maximo = max(maximo, max(valores))
        # Centraliza o conjunto de k barras em torno de cada posição inteira i
        posicoes = [i - largura_total / 2 + largura * (k + 0.5) for i in range(len(valores))]

        ax.bar(posicoes, valores, width=largura * 0.9, color=cor, label=nome)

        for posicao, valor in zip(posicoes, valores):
            ax.annotate(
                formatar_numero(valor, casas),
                xy=(posicao, valor), xytext=(0, 5), textcoords='offset points',
                ha='center', va='bottom', fontsize=10
            )

    _acabamento_das_barras(ax, rotulos, maximo)

    legenda = ax.legend(frameon=False, loc='upper left', fontsize=11)
    for texto, (_, (_, cor)) in zip(legenda.get_texts(), series.items()):
        texto.set_color(cor)


def barras_horizontais_divergentes(ax, rotulos, valores, cor_positiva, cor_negativa, casas=1):
    """Desenha barras horizontais divergentes a partir de zero com valores nas pontas.

    Colore cada barra conforme o sinal do valor, adiciona uma linha vertical de
    referência em ``x = 0``, remove todas as bordas e anota os valores com sinal
    explícito nas extremidades.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` alvo.
        rotulos: Sequência com os rótulos das categorias no eixo vertical.
        valores: Sequência numérica (positiva ou negativa) que define o
            comprimento e o sentido das barras.
        cor_positiva: Cor aplicada às barras com ``valor > 0``.
        cor_negativa: Cor aplicada às barras com ``valor <= 0``.
        casas: Número de casas decimais exibidas nas anotações das pontas.
    """
    valores = list(valores)
    posicoes = range(len(valores))

    ax.barh(posicoes, valores, height=0.6, color=[cor_positiva if v > 0 else cor_negativa for v in valores])

    for posicao, valor in zip(posicoes, valores):
        ax.annotate(
            formatar_numero(valor, casas, sinal=True),
            xy=(valor, posicao),
            xytext=(5 if valor >= 0 else -5, 0), textcoords='offset points',
            ha='left' if valor >= 0 else 'right', va='center', fontsize=11
        )

    ax.axvline(0, color=cor_neutra(0.6), linewidth=1)
    ax.set_yticks(list(posicoes))
    ax.set_yticklabels(list(rotulos))
    ax.set_xticks([])
    # Margem horizontal extra evita que os rótulos numéricos ultrapassem a área do eixo
    ax.margins(x=0.2)

    for lado in ('top', 'right', 'bottom', 'left'):
        ax.spines[lado].set_visible(False)

    ax.tick_params(axis='y', length=0, labelcolor=cor_neutra(0.9), labelsize=11)


def _acabamento_das_barras(ax, rotulos, maximo):
    """Aplica o acabamento minimalista padrão aos gráficos de barras verticais.

    Configura os rótulos das categorias, oculta o eixo vertical e define uma
    folga superior de 12% acima do valor máximo para acomodar as anotações.

    Args:
        ax: Objeto ``matplotlib.axes.Axes`` alvo.
        rotulos: Sequência com os nomes das categorias do eixo horizontal.
        maximo: Maior valor numérico representado entre todas as barras.
    """
    ax.set_xticks(range(len(rotulos)))
    ax.set_xticklabels(list(rotulos))
    ax.set_yticks([])
    ax.set_ylim(0, maximo * 1.12)

    for lado in ('top', 'right', 'left'):
        ax.spines[lado].set_visible(False)

    ax.spines['bottom'].set_color(cor_neutra())
    ax.tick_params(axis='x', length=0, labelcolor=cor_neutra(0.8), labelsize=11, pad=8)


__all__ = [
    'COR_POPULACAO',
    'COR_PIB',
    'COR_PIB_PER_CAPITA',
    'COR_PRIMARIA',
    'COR_SECUNDARIA',
    'COR_POSITIVA',
    'COR_NEGATIVA',
    'DESLOCAMENTO_EIXOS',
    'estilo_tufte',
    'cor_neutra',
    'formatar_numero',
    'formatar_potencia_de_dez',
    'marcas_do_eixo',
    'marcas_de_anos',
    'definir_marcas_y',
    'eixo_log_em_potencias_de_dez',
    'moldura_de_intervalo',
    'titulo_e_subtitulo',
    'rotular_ponto',
    'rotular_series_finais',
    'rotular_painel',
    'rotulo_do_eixo',
    'legenda_sem_moldura',
    'barras_com_valores',
    'barras_agrupadas_com_valores',
    'barras_horizontais_divergentes',
]
