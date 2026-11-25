# Desempenho olímpico e características socioeconômicas
É investigado se o desempenho dos países nos **Jogos Olímpicos de Verão** está associado a características socioeconômicas (população, PIB e PIB per capita). Comparar países só pelo total de medalhas ignora diferenças enormes de tamanho e de riqueza, por isso o desempenho é analisado de formas complementares: número de medalhas, participação em cada edição e participação por categoria de prova (individual ou por equipe). Todas as conclusões são **associações**, não relações de causa e efeito.

A unidade de análise é o par **país × edição**. Países que participaram de uma edição e não ganharam medalhas entram com `total = 0`, e a ausência de indicador socioeconômico fica como dado ausente, nunca como zero.

```
Quadro de medalhas ─┐
                    ├─► painel país × edição ─┐
Atletas olímpicos ──┘                         ├─► 8 perguntas (gráficos + medidas descritivas)
                                              │
World Bank (população, PIB, PIB per capita) ──┘
```

## Estrutura

```
AEDV/
├── data/
│   ├── medal_table.csv          # quadro de medalhas por país e edição
│   ├── olympic_athletes.csv     # participações individuais (atleta × evento)
│   └── world_bank.csv           # indicadores do World Bank extraidos da API (1960–2025)
├── src/
│   ├── __init__.py              # lida com importação de modulos em src
│   ├── dados.py                 # módulo unificado de coleta, limpeza, padronização e integração das bases
│   └── estilo_grafico.py        # estilo gráfico dos gráficos do notebook, inspirado nos princípios de Edward Tufte
├── Análise do desempenho olímpico e características socioeconômicas.ipynb   # artigo principal
```

## Como rodar

### 1. Pré-requisitos

- Python 3 recente (o notebook foi executado com o Python 3.14)
- Dependências:

```bash
pip install pandas numpy matplotlib jupyter
```

### 2. Executar

```bash
cd src
jupyter lab
```

Abra o notebook `Análise do desempenho olímpico e características socioeconômicas.ipynb` e execute as células de cima para baixo. As células de preparação (logo após a descrição dos dados) criam os DataFrames usados em todas as perguntas, e incluem verificações (`assert`) de que a junção preserva os totais de medalhas por edição e por metal.

## Dados

| Fonte | Conteúdo | Cobertura |
|---|---|---|
| `medal_table.csv` | Medalhas (ouro, prata, bronze e total) por país e edição; só aparecem países com ao menos uma medalha. As medalhas de equipe são contadas uma única vez. | Verão e Inverno, 1896–2026 (1.929 linhas, 11 colunas) |
| `olympic_athletes.csv` | Uma linha por atleta × evento, com país (NOC), edição, esporte, prova e medalha. Usada para identificar todos os participantes, inclusive os sem medalha. | 315.094 linhas, 16 colunas |
| `world_bank.csv` | População total (`SP.POP.TOTL`), PIB em US$ correntes (`NY.GDP.MKTP.CD`) e PIB per capita em US$ correntes (`NY.GDP.PCAP.CD`), obtidos pela API do World Bank com `wbgapi`. | 1960–2025 |

## Tratamento dos dados

- **Recortes:** apenas Jogos de Verão. As perguntas 1 e 2 usam 1896–2024; as que envolvem o World Bank usam 1960–2024, período em que as fontes se sobrepõem. A pergunta 6 usa 2024 e a 8 usa 2016, por causa de lacunas na base de atletas nas edições recentes.
- **Códigos de país:** o World Bank usa códigos ISO3 e a base olímpica usa os do COI (NOC). Os códigos são convertidos por um dicionário (por exemplo `DEU → GER`, `NLD → NED`). Os cruzamentos são feitos sempre por código, nunca por nome.
- **Ajustes de identificadores:** o código `CHI` do World Bank (Channel Islands) é removido para não colidir com o NOC do Chile; `LIB` e `LBN` (Líbano) são unificados em `LBN`; `ROC` e `OAR` são mapeados para `RUS`.
- **Exclusões:** registros sem NOC e um registro isolado e inconsistente de ROC em 2024 saem da base.
- **Equipes mistas:** a categoria `MIX` é mantida separadamente, sem atribuir as medalhas a países.
- **1956:** a subedição equestre de Estocolmo aparece em linha separada, então as medalhas são somadas por **ano + NOC**.
- **Indicadores ausentes:** não são removidos globalmente; cada pergunta filtra só os indicadores de que precisa.

## Perguntas

| # | Pergunta | Recorte | Abordagem |
|---|---|---|---|
| 1 | Como o desempenho varia entre as edições? | 1896–2024 | Participantes, medalhistas, média e mediana de medalhas por edição |
| 2 | Como as medalhas se distribuem entre os países? Há concentração? | 1896–2024 | Participação acumulada dos NOCs e fatia dos 10 primeiros por edição |
| 3 | Países mais populosos ganham mais medalhas? | 1960–2024 | Dispersão com população em escala log, Spearman e quartis de população por edição |
| 4 | Há associação entre PIB e medalhas? | 1960–2024 | Dispersão, posição percentual do PIB na edição, Spearman e quartis |
| 5 | A relação muda com o PIB per capita? | 1960–2024 | Mesma amostra para os dois indicadores, Spearman e quartis |
| 6 | Quais países estão muito acima ou abaixo do padrão de países semelhantes? | 2024 | Diferença para a mediana dos 10 países mais próximos em população e PIB per capita, com sensibilidade a 5 e 15 vizinhos |
| 7 | As relações se mantêm ao longo das edições? | 1960–2024 | Spearman por edição para os três indicadores, com comparação por um painel fixo de NOCs |
| 8 | Quem se destaca nas provas individuais também se destaca nas de equipe? | 2016 | Classificação das provas, participação de cada NOC por categoria e Spearman |

## Principais resultados

Os valores abaixo vêm das análises do notebook.

- **Concentração:** em 2024, 92 das 206 delegações identificáveis ganharam ao menos uma medalha, e as 10 primeiras ficaram com cerca de 55,8% das medalhas. A mediana de medalhas por delegação é zero nas edições recentes.
- **Associações positivas, mas com muita dispersão:** a correlação de Spearman com o total de medalhas é de cerca de 0,48 para a população e 0,67 para a posição relativa do PIB; para o PIB per capita é de 0,37, menos intensa que a do PIB total na mesma amostra.
- **Estabilidade:** por edição, as três associações permanecem positivas de 1960 a 2024, com o PIB total sempre mais forte (aproximadamente 0,58 a 0,79).
- **Desvios em 2024:** Estados Unidos, China, Austrália, Grã-Bretanha e França ficam muito acima da referência de seus vizinhos; Arábia Saudita, Espanha, Emirados Árabes Unidos, Canadá e Finlândia ficam abaixo.
- **Individual × equipe (2016):** as contagens por categoria se correlacionam em cerca de 0,49 entre os NOCs medalhistas, ou seja, há correspondência, mas incompleta.

## Limitações

- Entidades históricas sem equivalente no World Bank (como União Soviética e Alemanha Oriental) ficam sem indicadores e saem das análises socioeconômicas.
- Os indicadores do World Bank só existem a partir de 1960, e a cobertura varia entre países e anos.
- As correlações são bivariadas e não controlam outros fatores (país-sede, boicotes, número de eventos, tamanho das delegações); nada aqui estabelece causalidade.

## Autores

Erick Souza Alberti, Felipe Augusto da Silva Cruz e Guilherme Henrique Pereira Cunha.

## Referências

- Olympic Athletes: <https://github.com/moderndive/olympicAthletes>
- World Bank, World Development Indicators: <https://data.worldbank.org/>
- `wbgapi` (cliente Python da API do World Bank): <https://pypi.org/project/wbgapi/>
