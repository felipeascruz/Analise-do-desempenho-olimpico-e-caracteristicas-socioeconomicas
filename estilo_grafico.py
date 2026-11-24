"""Estilo gráfico dos gráficos do notebook, inspirado nos princípios de Edward Tufte.

Princípios aplicados:

- máxima razão dados/tinta: sem grade, sem bordas superior e direita e sem caixas de legenda;
- moldura de intervalo (range frame): os eixos cobrem apenas a extensão dos dados;
- rótulos diretos nas linhas e valores escritos nas barras, no lugar de legendas e eixos;
- título e subtítulo informativos à esquerda, no lugar de rótulos redundantes nos eixos;
- cores discretas da paleta Okabe-Ito, a mesma usada nas perguntas 5 a 8 do notebook.

Fundo, texto e eixos herdam o tema do notebook (rcParams do matplotlib): o módulo só altera a
fonte e usa a cor do texto do tema, com transparência, nos elementos de apoio. As cores da paleta
têm contraste de pelo menos 3:1 tanto sobre fundo claro quanto sobre fundo escuro.
O arquivo deve ficar na mesma pasta do notebook.
"""

import math

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D


# =============================================================================
# Constantes
# =============================================================================

# Paleta Okabe-Ito, com o mesmo significado usado nas perguntas 5 a 8
COR_POPULACAO = '#009E73'
COR_PIB = '#0072B2'
COR_PIB_PER_CAPITA = '#D55E00'

# Cores para séries sem indicador associado e para valores positivos e negativos
COR_PRIMARIA = COR_PIB
COR_SECUNDARIA = COR_PIB_PER_CAPITA
COR_POSITIVA = COR_PIB
COR_NEGATIVA = COR_PIB_PER_CAPITA

# Distância (em pontos) entre os eixos e a área de dados
DESLOCAMENTO_EIXOS = 8

# Nomes das ordens de grandeza, no singular e no plural
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
    """Contexto do matplotlib com o estilo do trabalho, sem alterar as cores do tema do notebook.

    Uso: with estilo_tufte(): ... (o gráfico deve ser exibido, com plt.show(), dentro do bloco).
    """
    return plt.rc_context({
        'font.family': 'serif',
        'axes.grid': False,
        'axes.spines.top': False,
        'axes.spines.right': False
    })


def cor_neutra(opacidade=0.6):
    """Cor do texto do tema com transparência, que resulta em um cinza sobre qualquer fundo."""
    return to_rgba(plt.rcParams['text.color'], opacidade)


# =============================================================================
# Formatação de números
# =============================================================================

def formatar_numero(valor, casas=None, sinal=False):
    """Formata o número com vírgula decimal.

    Sem 'casas', números inteiros aparecem sem decimais e os demais com uma casa decimal.
    """
    if casas is None:
        casas = 0 if float(valor).is_integer() else 1

    texto = f'{valor:+.{casas}f}' if sinal else f'{valor:.{casas}f}'
    return texto.replace('.', ',')


def formatar_potencia_de_dez(valor, prefixo=''):
    """Escreve uma potência de dez por extenso (ex.: 1000000 -> '1 milhão', 10**10 -> '10 bilhões')."""
    expoente = round(math.log10(valor))
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
    """Valores 'redondos' (1, 2, 2,5 ou 5 vezes uma potência de dez) dentro do intervalo, em torno de 'alvo' marcas."""
    amplitude = maximo - minimo
    base = 10 ** math.floor(math.log10(amplitude / alvo))
    candidatos = [fator * base * 10 ** k for k in (0, 1) for fator in (1, 2, 2.5, 5)]
    passo = min(candidatos, key=lambda p: abs(amplitude / p - alvo))

    marca = math.ceil(minimo / passo) * passo
    marcas = []
    while marca <= maximo + 1e-9:
        marcas.append(int(marca) if float(marca).is_integer() else marca)
        marca += passo

    return marcas


def marcas_de_anos(anos, passo=20):
    """Anos múltiplos de 'passo' dentro do período dos dados."""
    return list(range((anos.min() // passo + 1) * passo, anos.max() + 1, passo))


def definir_marcas_y(ax, marcas, sufixo=''):
    """Marcas do eixo vertical, com vírgula decimal e sufixo opcional (ex.: '%')."""
    ax.set_yticks(marcas)
    ax.set_yticklabels([f'{formatar_numero(marca)}{sufixo}' for marca in marcas])


def eixo_log_em_potencias_de_dez(ax, valores, prefixo=''):
    """Eixo horizontal logarítmico com marcas em potências de dez, escritas por extenso."""
    ax.set_xscale('log')

    primeiro = math.ceil(math.log10(valores.min()))
    ultimo = math.floor(math.log10(valores.max()))
    marcas = [10 ** expoente for expoente in range(primeiro, ultimo + 1)]

    ax.set_xticks(marcas)
    ax.set_xticklabels([formatar_potencia_de_dez(marca, prefixo) for marca in marcas])
    ax.minorticks_off()


# =============================================================================
# Elementos do gráfico
# =============================================================================

def moldura_de_intervalo(ax, x_min, x_max, y_min, y_max, deslocamento=DESLOCAMENTO_EIXOS):
    """Eixos que cobrem apenas a extensão dos dados (range frame), sem bordas superior e direita."""
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)

    ax.spines['left'].set_bounds(y_min, y_max)
    ax.spines['bottom'].set_bounds(x_min, x_max)

    for lado in ('left', 'bottom'):
        ax.spines[lado].set_position(('outward', deslocamento))
        ax.spines[lado].set_color(cor_neutra())

    ax.tick_params(length=3, color=cor_neutra(), labelcolor=cor_neutra(0.8), labelsize=10)


def titulo_e_subtitulo(ax, titulo, subtitulo, recuo=DESLOCAMENTO_EIXOS):
    """Título e subtítulo alinhados à esquerda. O subtítulo informa a unidade e dispensa o rótulo do eixo vertical.

    O 'recuo' alinha o texto ao eixo vertical, que fica deslocado para fora da área de dados.
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
    """Escreve o rótulo ao lado de um ponto, na mesma cor da linha (rótulo direto, no lugar da legenda)."""
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


def rotular_painel(ax, texto, cor):
    """Rótulo colorido no canto superior esquerdo de um painel, no lugar do título do painel."""
    ax.text(0.02, 0.97, texto, transform=ax.transAxes, ha='left', va='top', color=cor, fontsize=12)


def rotulo_do_eixo(ax, texto):
    """Rótulo discreto para o eixo horizontal, usado quando a unidade não está clara pelas marcações."""
    ax.set_xlabel(texto, fontsize=11, color=cor_neutra(0.75), labelpad=10)


def legenda_sem_moldura(ax, itens, loc='lower left'):
    """Legenda sem caixa para estilos de linha. 'itens' é uma lista de (rótulo, estilo da linha)."""
    manipuladores = [Line2D([], [], color=cor_neutra(0.8), linestyle=estilo) for _, estilo in itens]
    ax.legend(manipuladores, [rotulo for rotulo, _ in itens], frameon=False, loc=loc, fontsize=10)


# =============================================================================
# Barras
# =============================================================================

def barras_com_valores(ax, rotulos, valores, cor, casas=2):
    """Barras finas com o valor escrito acima de cada uma, sem eixo vertical."""
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
    """Barras agrupadas com valores escritos acima. 'series' é um dicionário {nome: (valores, cor)}.

    Os nomes das séries aparecem na cor da respectiva barra, sem caixa de legenda.
    """
    largura_total = 0.7
    largura = largura_total / len(series)
    maximo = 0

    for k, (nome, (valores, cor)) in enumerate(series.items()):
        valores = list(valores)
        maximo = max(maximo, max(valores))
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
    """Barras horizontais a partir do zero, com o valor (e o sinal) escrito na ponta de cada uma."""
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
    ax.margins(x=0.2)

    for lado in ('top', 'right', 'bottom', 'left'):
        ax.spines[lado].set_visible(False)

    ax.tick_params(axis='y', length=0, labelcolor=cor_neutra(0.9), labelsize=11)


def _acabamento_das_barras(ax, rotulos, maximo):
    """Remove o eixo vertical e deixa apenas a linha de base e os rótulos das categorias."""
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
    'rotular_painel',
    'rotulo_do_eixo',
    'legenda_sem_moldura',
    'barras_com_valores',
    'barras_agrupadas_com_valores',
    'barras_horizontais_divergentes',
]
