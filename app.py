import unicodedata

import pandas as pd
import streamlit as st

from src.calculos import calcular_repasse

from calcular_iqe import carregar_base

from simular_iqe import (
    calcular_pipeline,
    criar_cenario,
    localizar_municipio,
)


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
        "Retenção para o FUNDEB",
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
# SIMULADOR EDUCACIONAL
# ==================================================

st.divider()

st.header(
    "Simulador de melhoria dos indicadores educacionais"
)

st.write(
    """
    Esta ferramenta permite construir um cenário hipotético de
    melhoria dos indicadores educacionais utilizados na formação
    do IQE.

    A aplicação recalcula os indicadores considerando os 184
    municípios e estima o impacto da alteração sobre o componente
    de Educação, o índice geral de participação e o repasse de ICMS.
    """
)

st.info(
    """
    **Cenário contrafactual**

    A simulação mantém constantes os componentes de VAF, Saúde e
    Meio Ambiente e altera somente o componente de Educação.

    Os valores resultantes são estimativas produzidas pelo cenário
    selecionado e não constituem previsão de receita futura.
    """
)


# ==================================================
# CONFIGURAÇÃO DO CENÁRIO
# ==================================================

st.subheader(
    "1. Definição do cenário educacional"
)

st.write(
    f"Município selecionado: **{municipio}**"
)

with st.form(
    "formulario_simulacao_educacional"
):

    # ----------------------------------------------
    # IQA
    # ----------------------------------------------

    st.markdown("### IQA")

    st.caption(
        "Defina as alterações relacionadas ao desempenho "
        "utilizado no cálculo do IQA."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        iqa_aumento_proficiencia = st.slider(
            "Aumento da proficiência — IQA (%)",
            min_value=0.0,
            max_value=30.0,
            value=5.0,
            step=0.5,
            help=(
                "Aumento percentual relativo aplicado às "
                "proficiências de Língua Portuguesa e Matemática."
            )
        )

    with col2:

        iqa_aumento_participacao = st.slider(
            "Aumento da participação — IQA (p.p.)",
            min_value=0.0,
            max_value=20.0,
            value=1.0,
            step=0.5,
            help=(
                "Aumento em pontos percentuais da participação "
                "nas avaliações."
            )
        )

    with col3:

        iqa_migracao = st.slider(
            "Migração para nível superior — IQA (%)",
            min_value=0.0,
            max_value=50.0,
            value=10.0,
            step=1.0,
            help=(
                "Percentual dos estudantes de cada nível que é "
                "deslocado para o nível imediatamente superior."
            )
        )

    # ----------------------------------------------
    # IQF
    # ----------------------------------------------

    st.markdown("### IQF5 e IQF9")

    st.caption(
        "As alterações abaixo são aplicadas aos indicadores "
        "do 5º e do 9º ano."
    )

    col1, col2 = st.columns(2)

    with col1:

        iqf_aumento_proficiencia = st.slider(
            "Aumento da proficiência — IQF (%)",
            min_value=0.0,
            max_value=30.0,
            value=5.0,
            step=0.5
        )

        iqf_reducao_critico = st.slider(
            "Redução de Muito Crítico (p.p.)",
            min_value=0.0,
            max_value=30.0,
            value=5.0,
            step=0.5
        )

    with col2:

        iqf_aumento_participacao = st.slider(
            "Aumento da participação — IQF (p.p.)",
            min_value=0.0,
            max_value=20.0,
            value=1.0,
            step=0.5
        )

        iqf_aumento_adequado = st.slider(
            "Aumento de Adequado (p.p.)",
            min_value=0.0,
            max_value=30.0,
            value=5.0,
            step=0.5
        )

    # ----------------------------------------------
    # APROVAÇÃO
    # ----------------------------------------------

    st.markdown("### Aprovação")

    aumento_aprovacao = st.slider(
        "Aumento da taxa de aprovação (p.p.)",
        min_value=0.0,
        max_value=10.0,
        value=1.0,
        step=0.1
    )

    executar_simulacao = st.form_submit_button(
        "Executar simulação",
        type="primary",
        use_container_width=True
    )


# ==================================================
# EXECUÇÃO DA SIMULAÇÃO
# ==================================================

if executar_simulacao:

    try:

        with st.spinner(
            "Recalculando os indicadores dos 184 municípios..."
        ):

            # ------------------------------------------
            # CARREGAR BASE EDUCACIONAL
            # ------------------------------------------

            base_educacional = carregar_base()

            # ------------------------------------------
            # CENÁRIO OBSERVADO
            # ------------------------------------------

            observado = calcular_pipeline(
                base_educacional
            )

            # ------------------------------------------
            # CRIAR CENÁRIO SIMULADO
            # ------------------------------------------

            base_educacional_simulada = criar_cenario(

                base=base_educacional,

                municipio=municipio,

                # IQA
                iqa_aumento_proficiencia=(
                    iqa_aumento_proficiencia
                ),

                iqa_aumento_participacao_pp=(
                    iqa_aumento_participacao
                ),

                iqa_migracao_niveis_percentual=(
                    iqa_migracao
                ),

                # IQF
                iqf_aumento_proficiencia=(
                    iqf_aumento_proficiencia
                ),

                iqf_aumento_participacao_pp=(
                    iqf_aumento_participacao
                ),

                iqf_reducao_muito_critico_pp=(
                    iqf_reducao_critico
                ),

                iqf_aumento_adequado_pp=(
                    iqf_aumento_adequado
                ),

                # APROVAÇÃO
                aumento_aprovacao_pp=(
                    aumento_aprovacao
                )
            )

            simulado = calcular_pipeline(
                base_educacional_simulada
            )

            # ==========================================
            # LOCALIZAR MUNICÍPIO
            # ==========================================

            posicao_observado = localizar_municipio(
                observado,
                municipio
            )

            posicao_simulado = localizar_municipio(
                simulado,
                municipio
            )

            dados_observados = observado.loc[
                posicao_observado
            ]

            dados_simulados = simulado.loc[
                posicao_simulado
            ]

            # ==========================================
            # INDICADORES
            # ==========================================

            iqa_atual = dados_observados[
                "iqa_transicao_2025"
            ]

            iqa_simulado = dados_simulados[
                "iqa_transicao_2025"
            ]

            iqf5_atual = dados_observados[
                "iqf5_2025"
            ]

            iqf5_simulado = dados_simulados[
                "iqf5_2025"
            ]

            iqf9_atual = dados_observados[
                "iqf9_2025"
            ]

            iqf9_simulado = dados_simulados[
                "iqf9_2025"
            ]

            iqe_d_atual = dados_observados[
                "iqe_d_2025"
            ]

            iqe_d_simulado = dados_simulados[
                "iqe_d_2025"
            ]

            iqe_s_atual = dados_observados[
                "iqe_s_2025"
            ]

            iqe_s_simulado = dados_simulados[
                "iqe_s_2025"
            ]

            iqe_atual = dados_observados[
                "iqe_final_2025"
            ]

            iqe_simulado = dados_simulados[
                "iqe_final_2025"
            ]

            aprovacao_atual = dados_observados[
                "taxa_aprovacao_2024"
            ]

            aprovacao_simulada = dados_simulados[
                "taxa_aprovacao_2024"
            ]

            educacao_calculada_atual = (
                dados_observados[
                    "coeficiente_educacao_calculado"
                ]
            )

            educacao_simulada = (
                dados_simulados[
                    "coeficiente_educacao_calculado"
                ]
            )

            # ==========================================
            # DIFERENÇA EDUCAÇÃO
            # ==========================================

            diferenca_educacao = (
                educacao_simulada
                - educacao_calculada_atual
            )

            if educacao_calculada_atual != 0:

                variacao_educacao_percentual = (
                    diferenca_educacao
                    / educacao_calculada_atual
                ) * 100

            else:

                variacao_educacao_percentual = 0

            # ==========================================
            # ÍNDICE GERAL SIMULADO
            # ==========================================

            indice_geral_atual = indice

            indice_geral_simulado = (
                indice_geral_atual
                + diferenca_educacao
            )

            diferenca_indice = (
                indice_geral_simulado
                - indice_geral_atual
            )

        # ==============================================
        # SIMULAÇÃO CONCLUÍDA
        # ==============================================

        st.success(
            "Simulação concluída."
        )

        # ==============================================
        # RESULTADOS EDUCACIONAIS
        # ==============================================

        st.subheader(
            "2. Resultado dos indicadores educacionais"
        )

        tabela_indicadores = pd.DataFrame(
            {
                "Indicador": [
                    "IQA",
                    "IQF5",
                    "IQF9",
                    "IQE_D",
                    "IQE_S",
                    "IQE final"
                ],

                "Atual": [
                    iqa_atual,
                    iqf5_atual,
                    iqf9_atual,
                    iqe_d_atual,
                    iqe_s_atual,
                    iqe_atual
                ],

                "Simulado": [
                    iqa_simulado,
                    iqf5_simulado,
                    iqf9_simulado,
                    iqe_d_simulado,
                    iqe_s_simulado,
                    iqe_simulado
                ]
            }
        )

        tabela_indicadores[
            "Diferença"
        ] = (
            tabela_indicadores["Simulado"]
            - tabela_indicadores["Atual"]
        )

        st.dataframe(
            tabela_indicadores.style.format(
                {
                    "Atual": "{:.10f}",
                    "Simulado": "{:.10f}",
                    "Diferença": "{:+.10f}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        # ==============================================
        # APROVAÇÃO
        # ==============================================

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Taxa de aprovação atual",
                f"{aprovacao_atual:.4f}%"
            )

        with col2:

            st.metric(
                "Taxa de aprovação simulada",
                f"{aprovacao_simulada:.4f}%"
            )

        with col3:

            st.metric(
                "Variação da aprovação",
                (
                    f"{aprovacao_simulada - aprovacao_atual:+.4f} "
                    "p.p."
                )
            )

        # ==============================================
        # IMPACTO NO ÍNDICE
        # ==============================================

        st.subheader(
            "3. Impacto no índice de participação"
        )

        st.markdown(
            "#### Componente Educação"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Educação atual",
                f"{educacao_calculada_atual:.7f}%"
            )

        with col2:

            st.metric(
                "Educação simulada",
                f"{educacao_simulada:.7f}%"
            )

        with col3:

            st.metric(
                "Diferença",
                f"{diferenca_educacao:+.7f} p.p."
            )

        with col4:

            st.metric(
                "Variação relativa",
                f"{variacao_educacao_percentual:+.4f}%"
            )

        # ==============================================
        # ÍNDICE GERAL
        # ==============================================

        st.markdown(
            "#### Índice geral"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Índice geral atual",
                f"{indice_geral_atual:.7f}%"
            )

        with col2:

            st.metric(
                "Índice geral simulado",
                f"{indice_geral_simulado:.7f}%"
            )

        with col3:

            st.metric(
                "Variação do índice",
                f"{diferenca_indice:+.7f} p.p."
            )

        # ==============================================
        # COMPOSIÇÃO ATUAL X SIMULADA
        # ==============================================

        with st.expander(
            "Visualizar composição atual e simulada"
        ):

            composicao_simulada = pd.DataFrame(
                {
                    "Componente": [
                        "VAF",
                        "Educação",
                        "Saúde",
                        "Meio Ambiente"
                    ],

                    "Atual": [
                        indice_vaf,
                        indice_educacao,
                        indice_saude,
                        indice_meio_ambiente
                    ],

                    "Simulado": [
                        indice_vaf,
                        educacao_simulada,
                        indice_saude,
                        indice_meio_ambiente
                    ]
                }
            )

            st.dataframe(
                composicao_simulada.style.format(
                    {
                        "Atual": "{:.7f}%",
                        "Simulado": "{:.7f}%"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

            grafico_composicao_simulada = (
                composicao_simulada
                .set_index("Componente")
            )

            st.bar_chart(
                grafico_composicao_simulada
            )

        # ==============================================
        # IMPACTO FINANCEIRO
        # ==============================================

        st.subheader(
            "4. Impacto financeiro potencial"
        )

        st.write(
            """
            Para estimar o impacto financeiro, a aplicação utiliza
            as mesmas bases mensais de ICMS e substitui somente o
            índice geral atual pelo índice geral resultante do
            cenário educacional simulado.
            """
        )

        resultados_financeiros = []

        for mes_simulacao in ordem_meses:

            linha_base_simulacao = bases[
                bases["mes"]
                == mes_simulacao
            ]

            if linha_base_simulacao.empty:
                continue

            base_icms_simulacao = (
                linha_base_simulacao[
                    "base_icms"
                ]
                .iloc[0]
            )

            # ------------------------------------------
            # REPASSE ATUAL
            # ------------------------------------------

            repasse_atual_simulacao = (
                calcular_repasse(
                    base_icms=base_icms_simulacao,
                    indice_percentual=(
                        indice_geral_atual
                    )
                )
            )

            # ------------------------------------------
            # REPASSE SIMULADO
            # ------------------------------------------

            repasse_novo_simulacao = (
                calcular_repasse(
                    base_icms=base_icms_simulacao,
                    indice_percentual=(
                        indice_geral_simulado
                    )
                )
            )

            # ------------------------------------------
            # DIFERENÇAS
            # ------------------------------------------

            ganho_bruto = (
                repasse_novo_simulacao[
                    "repasse_bruto"
                ]
                - repasse_atual_simulacao[
                    "repasse_bruto"
                ]
            )

            variacao_fundeb = (
                repasse_novo_simulacao[
                    "fundeb"
                ]
                - repasse_atual_simulacao[
                    "fundeb"
                ]
            )

            ganho_liquido = (
                repasse_novo_simulacao[
                    "repasse_liquido"
                ]
                - repasse_atual_simulacao[
                    "repasse_liquido"
                ]
            )

            resultados_financeiros.append(
                {
                    "Mês": mes_simulacao,

                    "Bruto atual":
                        repasse_atual_simulacao[
                            "repasse_bruto"
                        ],

                    "Bruto simulado":
                        repasse_novo_simulacao[
                            "repasse_bruto"
                        ],

                    "Ganho bruto":
                        ganho_bruto,

                    "Retenção Fundeb atual":
                        repasse_atual_simulacao[
                            "fundeb"
                        ],

                    "Retenção Fundeb simulada":
                        repasse_novo_simulacao[
                            "fundeb"
                        ],

                    "Variação Fundeb":
                        variacao_fundeb,

                    "Líquido atual":
                        repasse_atual_simulacao[
                            "repasse_liquido"
                        ],

                    "Líquido simulado":
                        repasse_novo_simulacao[
                            "repasse_liquido"
                        ],

                    "Ganho líquido":
                        ganho_liquido
                }
            )

        tabela_financeira = pd.DataFrame(
            resultados_financeiros
        )

        # ==============================================
        # TABELA FINANCEIRA
        # ==============================================

        colunas_monetarias = [
            coluna
            for coluna in tabela_financeira.columns
            if coluna != "Mês"
        ]

        formatacao_monetaria = {
            coluna: (
                lambda valor:
                formatar_moeda(valor)
            )
            for coluna in colunas_monetarias
        }

        st.dataframe(
            tabela_financeira.style.format(
                formatacao_monetaria
            ),
            use_container_width=True,
            hide_index=True
        )

        # ==============================================
        # TOTAIS
        # ==============================================

        total_bruto_atual = (
            tabela_financeira[
                "Bruto atual"
            ].sum()
        )

        total_bruto_simulado = (
            tabela_financeira[
                "Bruto simulado"
            ].sum()
        )

        total_ganho_bruto = (
            tabela_financeira[
                "Ganho bruto"
            ].sum()
        )

        total_fundeb_atual = (
            tabela_financeira[
                "Retenção Fundeb atual"
            ].sum()
        )

        total_fundeb_simulado = (
            tabela_financeira[
                "Retenção Fundeb simulada"
            ].sum()
        )

        total_liquido_atual = (
            tabela_financeira[
                "Líquido atual"
            ].sum()
        )

        total_liquido_simulado = (
            tabela_financeira[
                "Líquido simulado"
            ].sum()
        )

        total_ganho_liquido = (
            tabela_financeira[
                "Ganho líquido"
            ].sum()
        )

        # ==============================================
        # RESULTADO ACUMULADO
        # ==============================================

        st.subheader(
            "5. Resultado acumulado — janeiro a junho"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Repasse bruto atual",
                formatar_moeda(
                    total_bruto_atual
                )
            )

            st.metric(
                "Repasse bruto simulado",
                formatar_moeda(
                    total_bruto_simulado
                )
            )

        with col2:

            st.metric(
                "Ganho bruto potencial",
                formatar_moeda(
                    total_ganho_bruto
                )
            )

            st.metric(
                "Aumento da retenção para o Fundeb",
                formatar_moeda(
                    total_fundeb_simulado
                    - total_fundeb_atual
                )
            )

        with col3:

            st.metric(
                "Repasse líquido atual",
                formatar_moeda(
                    total_liquido_atual
                )
            )

            st.metric(
                "Repasse líquido simulado",
                formatar_moeda(
                    total_liquido_simulado
                )
            )

        st.metric(
            "Ganho líquido potencial no período",
            formatar_moeda(
                total_ganho_liquido
            )
        )

        # ==============================================
        # GRÁFICO FINANCEIRO
        # ==============================================

        st.subheader(
            "6. Comparação mensal do cenário"
        )

        grafico_simulacao = (
            tabela_financeira[
                [
                    "Mês",
                    "Bruto atual",
                    "Bruto simulado"
                ]
            ]
            .copy()
        )

        grafico_simulacao["Mês"] = (
            pd.Categorical(
                grafico_simulacao["Mês"],
                categories=ordem_meses,
                ordered=True
            )
        )

        grafico_simulacao = (
            grafico_simulacao
            .sort_values("Mês")
            .set_index("Mês")
        )

        st.line_chart(
            grafico_simulacao
        )

        # ==============================================
        # VALIDAÇÃO MATEMÁTICA
        # ==============================================

        with st.expander(
            "Validação matemática da simulação"
        ):

            soma_iqe_observado = (
                observado[
                    "iqe_final_2025"
                ].sum()
            )

            soma_iqe_simulado = (
                simulado[
                    "iqe_final_2025"
                ].sum()
            )

            soma_educacao_observada = (
                observado[
                    "coeficiente_educacao_calculado"
                ].sum()
            )

            soma_educacao_simulada = (
                simulado[
                    "coeficiente_educacao_calculado"
                ].sum()
            )

            st.write(
                "**Municípios recalculados:** "
                f"{len(simulado)}"
            )

            st.write(
                "**Soma do IQE observado:** "
                f"{soma_iqe_observado:.10f}"
            )

            st.write(
                "**Soma do IQE simulado:** "
                f"{soma_iqe_simulado:.10f}"
            )

            st.write(
                "**Soma do componente Educação observado:** "
                f"{soma_educacao_observada:.10f}"
            )

            st.write(
                "**Soma do componente Educação simulado:** "
                f"{soma_educacao_simulada:.10f}"
            )

            if (
                abs(
                    soma_iqe_simulado - 1
                ) < 1e-9
                and
                abs(
                    soma_educacao_simulada - 18
                ) < 1e-9
            ):

                st.success(
                    "A estrutura relativa da distribuição "
                    "foi preservada."
                )

            else:

                st.error(
                    "A simulação apresentou uma inconsistência "
                    "na distribuição."
                )

        # ==============================================
        # NOTA METODOLÓGICA
        # ==============================================

        st.warning(
            """
            **Interpretação dos resultados**

            A simulação altera os indicadores educacionais do
            município selecionado e recalcula o IQE considerando
            os 184 municípios.

            O impacto financeiro é estimado mantendo constantes
            os componentes VAF, Saúde e Meio Ambiente e utilizando
            as bases mensais de ICMS disponíveis para janeiro a
            junho de 2026.

            Portanto, o resultado representa um cenário
            contrafactual e não uma previsão do valor que o
            município efetivamente receberá em períodos futuros.
            """
        )

    except Exception as erro:

        st.error(
            "Não foi possível executar a simulação."
        )

        st.exception(
            erro
        )


# ==================================================
# METODOLOGIA
# ==================================================

st.divider()

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
        Retencao\ Fundeb =
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
        da retenção destinada ao Fundeb. A aplicação apresenta
        separadamente o valor destinado ao fundo e o valor
        líquido resultante.
        """
    )


# ==================================================
# METODOLOGIA DA SIMULAÇÃO
# ==================================================

with st.expander(
    "Como funciona a simulação educacional?"
):

    st.markdown(
        """
        A simulação utiliza a mesma estrutura de cálculo do
        **Índice de Qualidade da Educação (IQE)** empregada na
        base educacional utilizada pelo projeto.

        O processo é realizado em etapas:

        1. O usuário define alterações hipotéticas nos indicadores
        educacionais do município selecionado.

        2. São recalculados o **IQA**, o **IQF do 5º ano**, o
        **IQF do 9º ano**, o indicador de aprovação e os demais
        componentes necessários à obtenção do IQE.

        3. Como os indicadores possuem natureza relativa, o cálculo
        é realizado novamente considerando os **184 municípios**.

        4. O novo IQE determina um novo componente de Educação.

        5. Para o cenário financeiro, os componentes de **VAF,
        Saúde e Meio Ambiente são mantidos constantes**.

        6. A diferença do componente Educação é incorporada ao
        índice geral utilizado na simulação.

        7. O índice simulado é aplicado às mesmas bases mensais de
        ICMS utilizadas no cálculo do cenário observado.

        Dessa forma, é possível estimar o impacto financeiro
        associado exclusivamente ao cenário educacional definido
        pelo usuário.
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

        **Base educacional**

        A simulação utiliza a base de dados empregada no cálculo
        do IQE, incluindo informações relacionadas ao IQA, IQF do
        5º ano, IQF do 9º ano, aprovação e indicador socioeconômico.

        **Base mensal do ICMS**

        A base utilizada no cálculo é extraída dos demonstrativos
        mensais da SEFAZ-CE, no campo
        `ICMS BASE DE CÁLCULO MUNICÍPIOS (100%)`.

        **Repasses realizados**

        Os valores apresentados na seção de comparação correspondem
        aos repasses mensais publicados pela SEFAZ-CE. Esses valores
        são utilizados para validação e comparação com o resultado
        calculado pela aplicação.
        """
    )


# ==================================================
# OBSERVAÇÃO
# ==================================================

st.caption(
    "Aplicação acadêmica desenvolvida a partir de dados "
    "públicos oficiais do Estado do Ceará."
)