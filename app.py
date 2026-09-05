import unicodedata

import pandas as pd
import streamlit as st

from src.calculos import calcular_repasse


# ==================================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================================

st.set_page_config(
    page_title="Repasse ICMS Ceará",
    layout="wide"
)


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def normalizar_municipio(nome):
    nome = str(nome).strip().upper()
    nome = unicodedata.normalize("NFKD", nome)

    nome = "".join(
        caractere
        for caractere in nome
        if not unicodedata.combining(caractere)
    )

    return " ".join(nome.split())


def formatar_moeda(valor):
    texto = f"{valor:,.2f}"

    texto = (
        texto
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"R$ {texto}"


# ==================================================
# TÍTULO
# ==================================================

st.title("Repasse de ICMS aos Municípios do Ceará")

st.write(
    "Cálculo estimado da cota-parte municipal do ICMS "
    "com base nos parâmetros oficiais de 2026."
)


# ==================================================
# LEITURA DOS DADOS
# ==================================================

indices = pd.read_csv(
    "data/indices_2026.csv"
)

bases = pd.read_csv(
    "data/bases_icms_2026.csv"
)

repasses = pd.read_csv(
    "data/repasses_sefaz_2026.csv"
)


# ==================================================
# NORMALIZAÇÃO DOS MUNICÍPIOS
# ==================================================

indices["municipio_chave"] = (
    indices["municipio"]
    .apply(normalizar_municipio)
)

repasses["municipio_chave"] = (
    repasses["municipio"]
    .apply(normalizar_municipio)
)


# ==================================================
# SELEÇÃO
# ==================================================

municipios = (
    indices["municipio"]
    .sort_values()
    .tolist()
)

municipio = st.selectbox(
    "Selecione o município",
    municipios
)

mes = st.selectbox(
    "Selecione o mês",
    bases["mes"].tolist()
)

municipio_chave = normalizar_municipio(
    municipio
)


# ==================================================
# DADOS DO MUNICÍPIO
# ==================================================

dados_municipio = indices.loc[
    indices["municipio_chave"] == municipio_chave
].iloc[0]

indice = dados_municipio["indice_2026"]

indice_vaf = dados_municipio["indice_vaf"]
indice_educacao = dados_municipio["indice_educacao"]
indice_saude = dados_municipio["indice_saude"]
indice_meio_ambiente = dados_municipio["indice_meio_ambiente"]

vaf_2023 = dados_municipio["vaf_2023"]
vaf_2024 = dados_municipio["vaf_2024"]
media_vaf = dados_municipio["media_vaf"]


# ==================================================
# BASE DO MÊS
# ==================================================

base = bases.loc[
    bases["mes"] == mes,
    "base_icms"
].iloc[0]


# ==================================================
# CÁLCULO
# ==================================================

resultado = calcular_repasse(
    base_icms=base,
    indice_percentual=indice
)


# ==================================================
# DADOS UTILIZADOS
# ==================================================

st.subheader("Dados utilizados")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Base ICMS dos municípios",
        formatar_moeda(base)
    )

with col2:
    st.metric(
        "Índice final de participação do município",
        f"{indice:.7f}%"
    )


# ==================================================
# COMPOSIÇÃO DO ÍNDICE
# ==================================================

st.subheader("Composição do índice municipal")

st.write(
    "O índice final de participação é composto por quatro "
    "componentes, conforme os pesos estabelecidos para a "
    "distribuição da cota-parte municipal do ICMS."
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Índice do Valor Adicionado (VAF) — peso 65%",
        f"{indice_vaf:.7f}%"
    )

with col2:
    st.metric(
        "Índice de Educação — peso 18%",
        f"{indice_educacao:.7f}%"
    )

with col3:
    st.metric(
        "Índice de Saúde — peso 15%",
        f"{indice_saude:.7f}%"
    )

with col4:
    st.metric(
        "Índice de Meio Ambiente — peso 2%",
        f"{indice_meio_ambiente:.7f}%"
    )


# ==================================================
# GRÁFICO DA COMPOSIÇÃO DO ÍNDICE
# ==================================================

with st.expander(
    "Visualizar gráfico da composição do índice"
):

    composicao_indice = pd.DataFrame(
        {
            "Componente": [
                "Valor Adicionado (VAF)",
                "Educação",
                "Saúde",
                "Meio Ambiente"
            ],
            "Participação": [
                indice_vaf,
                indice_educacao,
                indice_saude,
                indice_meio_ambiente
            ]
        }
    )

    composicao_indice = (
        composicao_indice
        .set_index("Componente")
    )

    st.bar_chart(
        composicao_indice,
        y="Participação"
    )

    st.caption(
        "O gráfico apresenta a contribuição de cada componente "
        "para o índice final do município selecionado."
    )


# ==================================================
# DETALHES DO VAF
# ==================================================

with st.expander(
    "Detalhes do Valor Adicionado Fiscal (VAF)"
):

    st.write(
        "Valores utilizados na determinação do componente "
        "relacionado ao Valor Adicionado Fiscal."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "VAF 2023",
            formatar_moeda(vaf_2023)
        )

    with col2:
        st.metric(
            "VAF 2024",
            formatar_moeda(vaf_2024)
        )

    with col3:
        st.metric(
            "Média do VAF",
            formatar_moeda(media_vaf)
        )


# ==================================================
# RESULTADO
# ==================================================

st.subheader("Resultado calculado")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Repasse bruto",
        formatar_moeda(
            resultado["repasse_bruto"]
        )
    )

with col2:
    st.metric(
        "FUNDEB",
        formatar_moeda(
            resultado["fundeb"]
        )
    )

with col3:
    st.metric(
        "Repasse líquido",
        formatar_moeda(
            resultado["repasse_liquido"]
        )
    )


# ==================================================
# REPASSE OFICIAL
# ==================================================

repasse_oficial = repasses[
    (
        repasses["municipio_chave"] == municipio_chave
    )
    &
    (
        repasses["mes"] == mes
    )
]


# ==================================================
# COMPARAÇÃO COM A SEFAZ
# ==================================================

if not repasse_oficial.empty:

    valor_oficial = (
        repasse_oficial["repasse_sefaz"]
        .iloc[0]
    )

    diferenca = (
        valor_oficial
        - resultado["repasse_bruto"]
    )

    if valor_oficial != 0:
        diferenca_percentual = (
            abs(diferenca)
            / valor_oficial
        ) * 100
    else:
        diferenca_percentual = 0


    st.subheader("Comparação com a SEFAZ")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Repasse realizado pela SEFAZ",
            formatar_moeda(valor_oficial)
        )

    with col2:
        st.metric(
            "Diferença",
            formatar_moeda(diferenca)
        )

    with col3:
        st.metric(
            "Diferença percentual",
            f"{diferenca_percentual:.4f}%"
        )


    if mes == "Junho":
        st.warning(
            """
            Os valores publicados pela SEFAZ para junho de 2026
            apresentam divergências relevantes em relação aos valores
            calculados com a base de ICMS e os índices oficiais
            disponíveis para 2026.

            A aplicação mantém a mesma metodologia e os mesmos
            parâmetros oficiais utilizados nos demais meses.
            """
        )

else:

    st.warning(
        "Não foi encontrado repasse da SEFAZ para "
        "o município e mês selecionados."
    )


# ==================================================
# GRÁFICO MENSAL: CALCULADO X SEFAZ
# ==================================================

st.subheader(
    "Evolução mensal do repasse"
)

st.write(
    "Comparação entre o valor calculado pela aplicação e "
    "o repasse realizado pela SEFAZ para o município selecionado."
)


ordem_meses = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho"
]


dados_grafico = []


for mes_grafico in ordem_meses:

    linha_base = bases[
        bases["mes"] == mes_grafico
    ]

    if linha_base.empty:
        continue

    base_mes = (
        linha_base["base_icms"]
        .iloc[0]
    )

    calculo_mes = calcular_repasse(
        base_icms=base_mes,
        indice_percentual=indice
    )

    linha_sefaz = repasses[
        (
            repasses["municipio_chave"]
            == municipio_chave
        )
        &
        (
            repasses["mes"]
            == mes_grafico
        )
    ]

    if not linha_sefaz.empty:

        valor_sefaz = (
            linha_sefaz["repasse_sefaz"]
            .iloc[0]
        )

    else:

        valor_sefaz = None


    dados_grafico.append(
        {
            "Mês": mes_grafico,
            "Calculado": calculo_mes[
                "repasse_bruto"
            ],
            "SEFAZ": valor_sefaz
        }
    )


grafico_mensal = pd.DataFrame(
    dados_grafico
)


grafico_mensal["Mês"] = pd.Categorical(
    grafico_mensal["Mês"],
    categories=ordem_meses,
    ordered=True
)


grafico_mensal = (
    grafico_mensal
    .sort_values("Mês")
    .set_index("Mês")
)


st.line_chart(
    grafico_mensal[
        [
            "Calculado",
            "SEFAZ"
        ]
    ]
)


st.caption(
    "Calculado: valor obtido pela aplicação utilizando a "
    "base mensal e o índice oficial de participação. "
    "SEFAZ: valor efetivamente publicado para o município."
)


# ==================================================
# METODOLOGIA
# ==================================================

with st.expander(
    "Como o repasse é calculado?"
):

    st.write(
        """
        A aplicação utiliza a base mensal de ICMS destinada
        à participação dos municípios e o índice oficial de
        participação do município selecionado.
        """
    )

    st.latex(
        r"""
        Repasse\ Bruto =
        Base\ ICMS
        \times 25\%
        \times
        \frac{Indice\ Municipal}{100}
        """
    )

    st.latex(
        r"""
        FUNDEB =
        Repasse\ Bruto
        \times 20\%
        """
    )

    st.latex(
        r"""
        Repasse\ Liquido =
        Repasse\ Bruto
        \times 80\%
        """
    )

    st.write(
        """
        O repasse bruto representa a parcela municipal antes
        da retenção destinada ao FUNDEB. A aplicação apresenta
        separadamente o valor destinado ao FUNDEB e o valor
        líquido resultante.
        """
    )


# ==================================================
# FONTES DOS DADOS
# ==================================================

with st.expander(
    "Fontes dos dados"
):

    st.markdown(
        """
        **Índices municipais de participação**

        Os índices de participação utilizados pela aplicação são
        provenientes dos dados oficiais publicados pela Secretaria
        da Fazenda do Estado do Ceará (SEFAZ-CE) para aplicação
        no exercício de 2026.

        **Valor Adicionado Fiscal (VAF)**

        Os valores de VAF de 2023 e 2024, a média do VAF e o
        respectivo componente do índice são provenientes da tabela
        oficial de índices municipais utilizada para 2026.

        **Educação, Saúde e Meio Ambiente**

        Os componentes referentes à Educação, Saúde e Meio Ambiente
        são obtidos diretamente da tabela oficial de composição dos
        índices municipais.

        **Base mensal do ICMS**

        A base utilizada no cálculo é extraída dos demonstrativos
        mensais da SEFAZ-CE, no campo
        `ICMS BASE DE CÁLCULO MUNICÍPIOS (100%)`.

        **Repasses realizados**

        Os valores apresentados na seção de comparação correspondem
        aos repasses mensais publicados pela SEFAZ-CE. Esses valores
        são utilizados apenas para validação e comparação com o
        resultado calculado pela aplicação.
        """
    )


# ==================================================
# OBSERVAÇÃO
# ==================================================

st.caption(
    "Aplicação acadêmica desenvolvida a partir de dados "
    "públicos oficiais do Estado do Ceará."
)