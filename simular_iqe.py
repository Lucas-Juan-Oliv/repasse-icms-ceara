import pandas as pd

from calcular_iqe import (
    carregar_base,
    calcular_iqa,
    calcular_iqf,
    calcular_aprovacao,
    calcular_iqe_d,
    calcular_iqe_s_e_final,
)


# ============================================================
# PIPELINE COMPLETO
# ============================================================

def calcular_pipeline(df):

    df = df.copy()

    df = calcular_iqa(df)
    df = calcular_iqf(df, "iqf5")
    df = calcular_iqf(df, "iqf9")
    df = calcular_aprovacao(df)
    df = calcular_iqe_d(df)
    df = calcular_iqe_s_e_final(df)

    return df


# ============================================================
# LOCALIZAR MUNICÍPIO
# ============================================================

def localizar_municipio(df, municipio):

    mascara = (
        df["municipio"]
        .astype(str)
        .str.strip()
        .str.upper()
        == municipio.strip().upper()
    )

    encontrados = df.index[mascara].tolist()

    if not encontrados:
        raise ValueError(
            f"Município não encontrado: {municipio}"
        )

    if len(encontrados) > 1:
        raise ValueError(
            f"Município duplicado: {municipio}"
        )

    return encontrados[0]


# ============================================================
# LIMITADORES
# ============================================================

def limitar(
    valor,
    minimo=0.0,
    maximo=100.0
):

    return max(
        minimo,
        min(valor, maximo)
    )


def aumentar_proficiencia(
    valor,
    percentual
):

    if percentual < -100:
        raise ValueError(
            "A alteração percentual não pode "
            "ser menor que -100%."
        )

    return (
        valor
        * (1 + percentual / 100)
    )


def adicionar_pontos_percentuais(
    valor,
    pontos
):

    return limitar(
        valor + pontos,
        0,
        100
    )


# ============================================================
# MIGRAÇÃO ENTRE NÍVEIS DO IQA
# ============================================================

def migrar_niveis_iqa(
    abaixo_basico,
    basico,
    proficiente,
    avancado,
    percentual_migracao
):
    """
    Desloca uma proporção dos alunos para o nível
    imediatamente superior.

    Fluxo:

        Abaixo do Básico
                ↓
              Básico
                ↓
            Proficiente
                ↓
             Avançado

    Exemplo:

        percentual_migracao = 10

    significa que 10% dos alunos existentes em cada
    categoria, exceto Avançado, avançam uma categoria.

    A soma original é preservada.
    """

    if percentual_migracao < 0:
        raise ValueError(
            "O percentual de migração não pode "
            "ser negativo."
        )

    if percentual_migracao > 100:
        raise ValueError(
            "O percentual de migração não pode "
            "ser superior a 100%."
        )

    taxa = (
        percentual_migracao
        / 100
    )

    # --------------------------------------------------------
    # Quantidade que sai de cada categoria
    # --------------------------------------------------------

    sai_abaixo = (
        abaixo_basico
        * taxa
    )

    sai_basico = (
        basico
        * taxa
    )

    sai_proficiente = (
        proficiente
        * taxa
    )

    # --------------------------------------------------------
    # Nova distribuição
    # --------------------------------------------------------

    novo_abaixo = (
        abaixo_basico
        - sai_abaixo
    )

    novo_basico = (
        basico
        - sai_basico
        + sai_abaixo
    )

    novo_proficiente = (
        proficiente
        - sai_proficiente
        + sai_basico
    )

    novo_avancado = (
        avancado
        + sai_proficiente
    )

    # --------------------------------------------------------
    # Correção numérica residual
    # --------------------------------------------------------

    soma_original = (
        abaixo_basico
        + basico
        + proficiente
        + avancado
    )

    soma_nova = (
        novo_abaixo
        + novo_basico
        + novo_proficiente
        + novo_avancado
    )

    diferenca = (
        soma_original
        - soma_nova
    )

    novo_avancado += diferenca

    return {
        "abaixo_basico": novo_abaixo,
        "basico": novo_basico,
        "proficiente": novo_proficiente,
        "avancado": novo_avancado,
    }


# ============================================================
# SIMULAR UMA DISCIPLINA DO IQA
# ============================================================

def simular_disciplina_iqa(
    df,
    indice,
    disciplina,
    aumento_proficiencia,
    aumento_participacao_pp,
    migracao_niveis_percentual
):

    coluna_proficiencia = (
        f"iqa_proficiencia_{disciplina}_2024"
    )

    coluna_participacao = (
        f"iqa_participacao_{disciplina}_2024"
    )

    coluna_abaixo = (
        f"iqa_{disciplina}_abaixo_basico_2024"
    )

    coluna_basico = (
        f"iqa_{disciplina}_basico_2024"
    )

    coluna_proficiente = (
        f"iqa_{disciplina}_proficiente_2024"
    )

    coluna_avancado = (
        f"iqa_{disciplina}_avancado_2024"
    )

    # --------------------------------------------------------
    # Proficiência
    # --------------------------------------------------------

    df.at[
        indice,
        coluna_proficiencia
    ] = aumentar_proficiencia(
        df.at[
            indice,
            coluna_proficiencia
        ],
        aumento_proficiencia
    )

    # --------------------------------------------------------
    # Participação
    # --------------------------------------------------------

    df.at[
        indice,
        coluna_participacao
    ] = adicionar_pontos_percentuais(
        df.at[
            indice,
            coluna_participacao
        ],
        aumento_participacao_pp
    )

    # --------------------------------------------------------
    # Distribuição dos níveis
    # --------------------------------------------------------

    distribuicao = migrar_niveis_iqa(
        abaixo_basico=df.at[
            indice,
            coluna_abaixo
        ],
        basico=df.at[
            indice,
            coluna_basico
        ],
        proficiente=df.at[
            indice,
            coluna_proficiente
        ],
        avancado=df.at[
            indice,
            coluna_avancado
        ],
        percentual_migracao=(
            migracao_niveis_percentual
        )
    )

    df.at[
        indice,
        coluna_abaixo
    ] = distribuicao[
        "abaixo_basico"
    ]

    df.at[
        indice,
        coluna_basico
    ] = distribuicao[
        "basico"
    ]

    df.at[
        indice,
        coluna_proficiente
    ] = distribuicao[
        "proficiente"
    ]

    df.at[
        indice,
        coluna_avancado
    ] = distribuicao[
        "avancado"
    ]


# ============================================================
# SIMULAR UMA DISCIPLINA DO IQF
# ============================================================

def simular_disciplina_iqf(
    df,
    indice,
    prefixo,
    disciplina,
    aumento_proficiencia,
    aumento_participacao_pp,
    reducao_muito_critico_pp,
    aumento_adequado_pp
):

    coluna_proficiencia = (
        f"{prefixo}_proficiencia_"
        f"{disciplina}_2024"
    )

    coluna_participacao = (
        f"{prefixo}_participacao_"
        f"{disciplina}_2024"
    )

    coluna_muito_critico = (
        f"{prefixo}_{disciplina}_"
        f"muito_critico_2024"
    )

    coluna_adequado = (
        f"{prefixo}_{disciplina}_"
        f"adequado_2024"
    )

    # --------------------------------------------------------
    # Proficiência
    # --------------------------------------------------------

    df.at[
        indice,
        coluna_proficiencia
    ] = aumentar_proficiencia(
        df.at[
            indice,
            coluna_proficiencia
        ],
        aumento_proficiencia
    )

    # --------------------------------------------------------
    # Participação
    # --------------------------------------------------------

    df.at[
        indice,
        coluna_participacao
    ] = adicionar_pontos_percentuais(
        df.at[
            indice,
            coluna_participacao
        ],
        aumento_participacao_pp
    )

    # --------------------------------------------------------
    # Muito Crítico
    # --------------------------------------------------------

    df.at[
        indice,
        coluna_muito_critico
    ] = adicionar_pontos_percentuais(
        df.at[
            indice,
            coluna_muito_critico
        ],
        -reducao_muito_critico_pp
    )

    # --------------------------------------------------------
    # Adequado
    # --------------------------------------------------------

    df.at[
        indice,
        coluna_adequado
    ] = adicionar_pontos_percentuais(
        df.at[
            indice,
            coluna_adequado
        ],
        aumento_adequado_pp
    )


# ============================================================
# APROVAÇÃO
# ============================================================

def simular_aprovacao(
    df,
    indice,
    aumento_pp
):

    atual = df.at[
        indice,
        "taxa_aprovacao_2024"
    ]

    df.at[
        indice,
        "taxa_aprovacao_2024"
    ] = adicionar_pontos_percentuais(
        atual,
        aumento_pp
    )


# ============================================================
# CRIAR CENÁRIO COMPLETO
# ============================================================

def criar_cenario(
    base,
    municipio,

    iqa_aumento_proficiencia,
    iqa_aumento_participacao_pp,
    iqa_migracao_niveis_percentual,

    iqf_aumento_proficiencia,
    iqf_aumento_participacao_pp,
    iqf_reducao_muito_critico_pp,
    iqf_aumento_adequado_pp,

    aumento_aprovacao_pp
):

    simulado = base.copy()

    indice = localizar_municipio(
        simulado,
        municipio
    )

    # ========================================================
    # IQA
    # ========================================================

    for disciplina in [
        "lp",
        "mat"
    ]:

        simular_disciplina_iqa(
            df=simulado,
            indice=indice,
            disciplina=disciplina,
            aumento_proficiencia=(
                iqa_aumento_proficiencia
            ),
            aumento_participacao_pp=(
                iqa_aumento_participacao_pp
            ),
            migracao_niveis_percentual=(
                iqa_migracao_niveis_percentual
            )
        )

    # ========================================================
    # IQF5 + IQF9
    # ========================================================

    for prefixo in [
        "iqf5",
        "iqf9"
    ]:

        for disciplina in [
            "mat",
            "lp"
        ]:

            simular_disciplina_iqf(
                df=simulado,
                indice=indice,
                prefixo=prefixo,
                disciplina=disciplina,
                aumento_proficiencia=(
                    iqf_aumento_proficiencia
                ),
                aumento_participacao_pp=(
                    iqf_aumento_participacao_pp
                ),
                reducao_muito_critico_pp=(
                    iqf_reducao_muito_critico_pp
                ),
                aumento_adequado_pp=(
                    iqf_aumento_adequado_pp
                )
            )

    # ========================================================
    # APROVAÇÃO
    # ========================================================

    simular_aprovacao(
        simulado,
        indice,
        aumento_aprovacao_pp
    )

    return simulado


# ============================================================
# VERIFICAR DISTRIBUIÇÃO IQA
# ============================================================

def verificar_distribuicao_iqa(
    df,
    municipio
):

    indice = localizar_municipio(
        df,
        municipio
    )

    resultados = {}

    for disciplina in [
        "lp",
        "mat"
    ]:

        abaixo = df.at[
            indice,
            f"iqa_{disciplina}_abaixo_basico_2024"
        ]

        basico = df.at[
            indice,
            f"iqa_{disciplina}_basico_2024"
        ]

        proficiente = df.at[
            indice,
            f"iqa_{disciplina}_proficiente_2024"
        ]

        avancado = df.at[
            indice,
            f"iqa_{disciplina}_avancado_2024"
        ]

        soma = (
            abaixo
            + basico
            + proficiente
            + avancado
        )

        resultados[disciplina] = {
            "abaixo_basico": abaixo,
            "basico": basico,
            "proficiente": proficiente,
            "avancado": avancado,
            "soma": soma
        }

    return resultados


# ============================================================
# MOSTRAR DISTRIBUIÇÃO IQA
# ============================================================

def mostrar_distribuicao_iqa(
    atual,
    simulado
):

    print("\n" + "=" * 70)
    print("DISTRIBUIÇÃO DOS NÍVEIS — IQA")
    print("=" * 70)

    nomes = {
        "lp": "Língua Portuguesa",
        "mat": "Matemática"
    }

    for disciplina in [
        "lp",
        "mat"
    ]:

        print(
            f"\n{nomes[disciplina]}"
        )

        print(
            "Abaixo do Básico: "
            f"{atual[disciplina]['abaixo_basico']:.4f}%"
            " -> "
            f"{simulado[disciplina]['abaixo_basico']:.4f}%"
        )

        print(
            "Básico: "
            f"{atual[disciplina]['basico']:.4f}%"
            " -> "
            f"{simulado[disciplina]['basico']:.4f}%"
        )

        print(
            "Proficiente: "
            f"{atual[disciplina]['proficiente']:.4f}%"
            " -> "
            f"{simulado[disciplina]['proficiente']:.4f}%"
        )

        print(
            "Avançado: "
            f"{atual[disciplina]['avancado']:.4f}%"
            " -> "
            f"{simulado[disciplina]['avancado']:.4f}%"
        )

        print(
            "Soma atual: "
            f"{atual[disciplina]['soma']:.10f}%"
        )

        print(
            "Soma simulada: "
            f"{simulado[disciplina]['soma']:.10f}%"
        )


# ============================================================
# MOSTRAR INDICADORES IQF
# ============================================================

def mostrar_iqf_entradas(
    original,
    simulado,
    municipio
):

    i_original = localizar_municipio(
        original,
        municipio
    )

    i_simulado = localizar_municipio(
        simulado,
        municipio
    )

    print("\n" + "=" * 70)
    print("INDICADORES IQF ALTERADOS")
    print("=" * 70)

    nomes = {
        ("iqf5", "mat"):
            "5º ano — Matemática",

        ("iqf5", "lp"):
            "5º ano — Língua Portuguesa",

        ("iqf9", "mat"):
            "9º ano — Matemática",

        ("iqf9", "lp"):
            "9º ano — Língua Portuguesa",
    }

    for (
        prefixo,
        disciplina
    ), nome in nomes.items():

        print(f"\n{nome}")

        col_prof = (
            f"{prefixo}_proficiencia_"
            f"{disciplina}_2024"
        )

        col_part = (
            f"{prefixo}_participacao_"
            f"{disciplina}_2024"
        )

        col_mc = (
            f"{prefixo}_{disciplina}_"
            f"muito_critico_2024"
        )

        col_ad = (
            f"{prefixo}_{disciplina}_"
            f"adequado_2024"
        )

        print(
            "Proficiência: "
            f"{original.at[i_original, col_prof]:.4f}"
            " -> "
            f"{simulado.at[i_simulado, col_prof]:.4f}"
        )

        print(
            "Participação: "
            f"{original.at[i_original, col_part]:.4f}%"
            " -> "
            f"{simulado.at[i_simulado, col_part]:.4f}%"
        )

        print(
            "Muito Crítico: "
            f"{original.at[i_original, col_mc]:.4f}%"
            " -> "
            f"{simulado.at[i_simulado, col_mc]:.4f}%"
        )

        print(
            "Adequado: "
            f"{original.at[i_original, col_ad]:.4f}%"
            " -> "
            f"{simulado.at[i_simulado, col_ad]:.4f}%"
        )


# ============================================================
# COMPARAR RESULTADOS
# ============================================================

def comparar_resultados(
    observado,
    simulado,
    municipio
):

    i_atual = localizar_municipio(
        observado,
        municipio
    )

    i_novo = localizar_municipio(
        simulado,
        municipio
    )

    atual = observado.loc[
        i_atual
    ]

    novo = simulado.loc[
        i_novo
    ]

    resultado = {}

    componentes = {
        "iqa":
            "iqa_transicao_2025",

        "iqf5":
            "iqf5_2025",

        "iqf9":
            "iqf9_2025",

        "aprovacao":
            "aprovacao_indice_2025",

        "iqe_d":
            "iqe_d_2025",

        "iqe_s":
            "iqe_s_2025",

        "iqe":
            "iqe_final_2025",

        "coef":
            "coeficiente_educacao_calculado"
    }

    for nome, coluna in componentes.items():

        resultado[
            f"{nome}_atual"
        ] = atual[coluna]

        resultado[
            f"{nome}_simulado"
        ] = novo[coluna]

        resultado[
            f"{nome}_diferenca"
        ] = (
            novo[coluna]
            - atual[coluna]
        )

    resultado[
        "variacao_coef_percentual"
    ] = (
        resultado["coef_diferenca"]
        / resultado["coef_atual"]
        * 100
    )

    resultado[
        "aprovacao_taxa_atual"
    ] = atual[
        "taxa_aprovacao_2024"
    ]

    resultado[
        "aprovacao_taxa_simulada"
    ] = novo[
        "taxa_aprovacao_2024"
    ]

    return resultado


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

def mostrar_resultados(
    municipio,
    resultado
):

    print("\n" + "=" * 70)
    print("RESULTADO FINAL DA SIMULAÇÃO")
    print("=" * 70)

    print(
        f"\nMunicípio: {municipio}"
    )

    componentes = [
        ("IQA", "iqa"),
        ("IQF5", "iqf5"),
        ("IQF9", "iqf9"),
        ("Índice Aprovação", "aprovacao"),
        ("IQE_D", "iqe_d"),
        ("IQE_S", "iqe_s"),
        ("IQE final", "iqe"),
        ("Coeficiente Educação", "coef"),
    ]

    for titulo, chave in componentes:

        print(f"\n{titulo}")

        print(
            "Atual:     "
            f"{resultado[chave + '_atual']:.10f}"
        )

        print(
            "Simulado:  "
            f"{resultado[chave + '_simulado']:.10f}"
        )

        print(
            "Diferença: "
            f"{resultado[chave + '_diferenca']:.10f}"
        )

    print("\nTaxa de aprovação")

    print(
        "Atual:    "
        f"{resultado['aprovacao_taxa_atual']:.4f}%"
    )

    print(
        "Simulada: "
        f"{resultado['aprovacao_taxa_simulada']:.4f}%"
    )

    print(
        "\nVariação percentual do "
        "coeficiente Educação: "
        f"{resultado['variacao_coef_percentual']:.4f}%"
    )


# ============================================================
# VALIDAR CONSISTÊNCIA
# ============================================================

def validar_consistencia(
    observado,
    simulado,
    distribuicao_iqa_simulada
):

    print("\n" + "=" * 70)
    print("VALIDAÇÃO MATEMÁTICA")
    print("=" * 70)

    print(
        "\nMunicípios observados: "
        f"{len(observado)}"
    )

    print(
        "Municípios simulados: "
        f"{len(simulado)}"
    )

    soma_iqe_atual = (
        observado[
            "iqe_final_2025"
        ].sum()
    )

    soma_iqe_simulada = (
        simulado[
            "iqe_final_2025"
        ].sum()
    )

    soma_coef_atual = (
        observado[
            "coeficiente_educacao_calculado"
        ].sum()
    )

    soma_coef_simulada = (
        simulado[
            "coeficiente_educacao_calculado"
        ].sum()
    )

    print(
        "\nSoma IQE atual: "
        f"{soma_iqe_atual:.10f}"
    )

    print(
        "Soma IQE simulado: "
        f"{soma_iqe_simulada:.10f}"
    )

    print(
        "\nSoma Educação atual: "
        f"{soma_coef_atual:.10f}"
    )

    print(
        "Soma Educação simulada: "
        f"{soma_coef_simulada:.10f}"
    )

    # --------------------------------------------------------
    # Validação das distribuições do IQA
    # --------------------------------------------------------

    print("\nDistribuição IQA simulada:")

    for disciplina in [
        "lp",
        "mat"
    ]:

        soma = (
            distribuicao_iqa_simulada[
                disciplina
            ]["soma"]
        )

        print(
            f"{disciplina.upper()}: "
            f"{soma:.10f}%"
        )

        if abs(
            soma - 100
        ) > 0.01:

            raise ValueError(
                "Distribuição IQA não soma 100% "
                f"em {disciplina}."
            )

    # --------------------------------------------------------
    # Invariantes
    # --------------------------------------------------------

    if len(simulado) != 184:
        raise ValueError(
            "A simulação não possui "
            "184 municípios."
        )

    if abs(
        soma_iqe_simulada - 1
    ) > 1e-9:

        raise ValueError(
            "Soma do IQE simulado diferente de 1."
        )

    if abs(
        soma_coef_simulada - 18
    ) > 1e-9:

        raise ValueError(
            "Soma do componente Educação "
            "diferente de 18."
        )

    print(
        "\nTodos os testes estruturais passaram."
    )


# ============================================================
# REDISTRIBUIÇÃO ENTRE MUNICÍPIOS
# ============================================================

def analisar_redistribuicao(
    observado,
    simulado,
    municipio
):

    atual = observado[
        [
            "municipio",
            "coeficiente_educacao_calculado"
        ]
    ].copy()

    novo = simulado[
        [
            "municipio",
            "coeficiente_educacao_calculado"
        ]
    ].copy()

    atual.columns = [
        "municipio",
        "coef_atual"
    ]

    novo.columns = [
        "municipio",
        "coef_simulado"
    ]

    comparacao = atual.merge(
        novo,
        on="municipio"
    )

    comparacao[
        "diferenca"
    ] = (
        comparacao["coef_simulado"]
        - comparacao["coef_atual"]
    )

    outros = comparacao[
        comparacao["municipio"]
        .str.upper()
        != municipio.upper()
    ]

    print("\n" + "=" * 70)
    print("REDISTRIBUIÇÃO")
    print("=" * 70)

    print(
        "\nMaior perda dos demais: "
        f"{outros['diferenca'].min():.10f}"
    )

    print(
        "Maior variação dos demais: "
        f"{outros['diferenca'].max():.10f}"
    )

    print(
        "Soma das diferenças: "
        f"{comparacao['diferenca'].sum():.10f}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("SIMULADOR EDUCACIONAL DO IQE — VERSÃO 3")
    print("=" * 70)

    municipio = "ABAIARA"

    # ========================================================
    # CENÁRIO
    # ========================================================

    # IQA
    iqa_aumento_proficiencia = 5.0
    iqa_aumento_participacao_pp = 1.0
    iqa_migracao_niveis_percentual = 10.0

    # IQF5 e IQF9
    iqf_aumento_proficiencia = 5.0
    iqf_aumento_participacao_pp = 1.0
    iqf_reducao_muito_critico_pp = 5.0
    iqf_aumento_adequado_pp = 5.0

    # Aprovação
    aumento_aprovacao_pp = 1.0

    print(
        f"\nMunicípio: {municipio}"
    )

    print("\nCENÁRIO IQA")

    print(
        "Proficiência: "
        f"+{iqa_aumento_proficiencia:.2f}%"
    )

    print(
        "Participação: "
        f"+{iqa_aumento_participacao_pp:.2f} p.p."
    )

    print(
        "Migração para nível superior: "
        f"{iqa_migracao_niveis_percentual:.2f}%"
    )

    print("\nCENÁRIO IQF")

    print(
        "Proficiência: "
        f"+{iqf_aumento_proficiencia:.2f}%"
    )

    print(
        "Participação: "
        f"+{iqf_aumento_participacao_pp:.2f} p.p."
    )

    print(
        "Muito Crítico: "
        f"-{iqf_reducao_muito_critico_pp:.2f} p.p."
    )

    print(
        "Adequado: "
        f"+{iqf_aumento_adequado_pp:.2f} p.p."
    )

    print("\nAPROVAÇÃO")

    print(
        f"+{aumento_aprovacao_pp:.2f} p.p."
    )

    # ========================================================
    # BASE
    # ========================================================

    base = carregar_base()

    # Distribuição original IQA

    distribuicao_original = (
        verificar_distribuicao_iqa(
            base,
            municipio
        )
    )

    # ========================================================
    # CÁLCULO OBSERVADO
    # ========================================================

    observado = calcular_pipeline(
        base
    )

    # ========================================================
    # CRIAR CENÁRIO
    # ========================================================

    base_simulada = criar_cenario(
        base=base,
        municipio=municipio,

        iqa_aumento_proficiencia=(
            iqa_aumento_proficiencia
        ),

        iqa_aumento_participacao_pp=(
            iqa_aumento_participacao_pp
        ),

        iqa_migracao_niveis_percentual=(
            iqa_migracao_niveis_percentual
        ),

        iqf_aumento_proficiencia=(
            iqf_aumento_proficiencia
        ),

        iqf_aumento_participacao_pp=(
            iqf_aumento_participacao_pp
        ),

        iqf_reducao_muito_critico_pp=(
            iqf_reducao_muito_critico_pp
        ),

        iqf_aumento_adequado_pp=(
            iqf_aumento_adequado_pp
        ),

        aumento_aprovacao_pp=(
            aumento_aprovacao_pp
        )
    )

    # ========================================================
    # DISTRIBUIÇÃO SIMULADA IQA
    # ========================================================

    distribuicao_simulada = (
        verificar_distribuicao_iqa(
            base_simulada,
            municipio
        )
    )

    mostrar_distribuicao_iqa(
        distribuicao_original,
        distribuicao_simulada
    )

    # ========================================================
    # MOSTRAR IQF
    # ========================================================

    mostrar_iqf_entradas(
        base,
        base_simulada,
        municipio
    )

    # ========================================================
    # CALCULAR CENÁRIO SIMULADO
    # ========================================================

    simulado = calcular_pipeline(
        base_simulada
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    resultado = comparar_resultados(
        observado,
        simulado,
        municipio
    )

    mostrar_resultados(
        municipio,
        resultado
    )

    # ========================================================
    # VALIDAÇÃO
    # ========================================================

    validar_consistencia(
        observado,
        simulado,
        distribuicao_simulada
    )

    # ========================================================
    # REDISTRIBUIÇÃO
    # ========================================================

    analisar_redistribuicao(
        observado,
        simulado,
        municipio
    )

    print("\n" + "=" * 70)
    print("SIMULAÇÃO V3 CONCLUÍDA")
    print("=" * 70)


if __name__ == "__main__":
    main()