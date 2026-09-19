from pathlib import Path
import pandas as pd


# ============================================================
# CAMINHOS
# ============================================================

PASTA_PROJETO = Path(__file__).resolve().parent

ARQUIVO_BASE = (
    PASTA_PROJETO
    / "data"
    / "base_iqe_2025.csv"
)

ARQUIVO_SAIDA = (
    PASTA_PROJETO
    / "data"
    / "calculo_iqe_2025.csv"
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def percentual_para_proporcao(valor):
    """
    Converte percentual para proporção.

    Exemplo:
        99.21 -> 0.9921
        100   -> 1.0
    """
    return valor / 100.0


def padronizar_minmax(serie):
    """
    Padronização min-max:

        (x - mínimo) / (máximo - mínimo)
    """

    minimo = serie.min()
    maximo = serie.max()

    if pd.isna(minimo) or pd.isna(maximo):
        raise ValueError(
            "A série contém valores inválidos para "
            "padronização min-max."
        )

    if maximo == minimo:
        raise ValueError(
            "Não é possível realizar a padronização "
            "min-max: máximo igual ao mínimo."
        )

    return (
        (serie - minimo)
        / (maximo - minimo)
    )


def transformar_em_participacao(serie):
    """
    Transforma uma série em participações relativas
    cuja soma é igual a 1.
    """

    soma = serie.sum()

    if pd.isna(soma):
        raise ValueError(
            "A série contém valores inválidos."
        )

    if soma == 0:
        raise ValueError(
            "Não é possível calcular participação relativa: "
            "a soma da série é zero."
        )

    return serie / soma


# ============================================================
# CARREGAMENTO DA BASE
# ============================================================

def carregar_base():

    if not ARQUIVO_BASE.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado:\n{ARQUIVO_BASE}"
        )

    df = pd.read_csv(
        ARQUIVO_BASE,
        encoding="utf-8-sig"
    )

    if len(df) != 184:
        raise ValueError(
            f"A base possui {len(df)} municípios. "
            "Esperados: 184."
        )

    if df["municipio"].duplicated().any():
        raise ValueError(
            "Existem municípios duplicados na base."
        )

    return df


# ============================================================
# IQA
# ============================================================

def fator_universalizacao_iqa(
    abaixo_basico,
    basico,
    proficiente,
    avancado
):
    """
    Fator de universalização utilizado no IQA.
    """

    abaixo_basico = percentual_para_proporcao(
        abaixo_basico
    )

    basico = percentual_para_proporcao(
        basico
    )

    proficiente = percentual_para_proporcao(
        proficiente
    )

    avancado = percentual_para_proporcao(
        avancado
    )

    return (
        (1 - abaixo_basico) ** 2
        * (1 - basico)
        * (1 + proficiente)
        * (1 + avancado) ** 2
    )


def calcular_iqa(df):

    df = df.copy()

    # --------------------------------------------------------
    # Fatores de universalização
    # --------------------------------------------------------

    df["iqa_fator_lp"] = (
        fator_universalizacao_iqa(
            df["iqa_lp_abaixo_basico_2024"],
            df["iqa_lp_basico_2024"],
            df["iqa_lp_proficiente_2024"],
            df["iqa_lp_avancado_2024"]
        )
    )

    df["iqa_fator_mat"] = (
        fator_universalizacao_iqa(
            df["iqa_mat_abaixo_basico_2024"],
            df["iqa_mat_basico_2024"],
            df["iqa_mat_proficiente_2024"],
            df["iqa_mat_avancado_2024"]
        )
    )

    # --------------------------------------------------------
    # Participação
    # --------------------------------------------------------

    df["iqa_part_lp"] = (
        df["iqa_participacao_lp_2024"]
        / 100
    )

    df["iqa_part_mat"] = (
        df["iqa_participacao_mat_2024"]
        / 100
    )

    # --------------------------------------------------------
    # Resultados brutos
    # --------------------------------------------------------

    df["iqa_resultado_lp"] = (
        df["iqa_proficiencia_lp_2024"]
        * df["iqa_part_lp"]
        * df["iqa_fator_lp"]
    )

    df["iqa_resultado_mat"] = (
        df["iqa_proficiencia_mat_2024"]
        * df["iqa_part_mat"]
        * df["iqa_fator_mat"]
    )

    # --------------------------------------------------------
    # Padronização
    # --------------------------------------------------------

    df["iqa_resultado_lp_pad"] = (
        padronizar_minmax(
            df["iqa_resultado_lp"]
        )
    )

    df["iqa_resultado_mat_pad"] = (
        padronizar_minmax(
            df["iqa_resultado_mat"]
        )
    )

    # --------------------------------------------------------
    # Participação relativa
    # --------------------------------------------------------

    df["iqalp_novo_2025"] = (
        transformar_em_participacao(
            df["iqa_resultado_lp_pad"]
        )
    )

    df["iqamt_novo_2025"] = (
        transformar_em_participacao(
            df["iqa_resultado_mat_pad"]
        )
    )

    # --------------------------------------------------------
    # Novo IQA
    #
    # 75% Língua Portuguesa
    # 25% Matemática
    # --------------------------------------------------------

    df["iqa_novo_2025"] = (
        0.75 * df["iqalp_novo_2025"]
        + 0.25 * df["iqamt_novo_2025"]
    )

    # --------------------------------------------------------
    # Transição 2025
    #
    # 75% IQA antigo
    # 25% IQA novo
    # --------------------------------------------------------

    df["iqa_transicao_2025"] = (
        0.75 * df["iqa_2024"]
        + 0.25 * df["iqa_novo_2025"]
    )

    return df


# ============================================================
# IQF
# ============================================================

def fator_ajuste_iqf(
    muito_critico,
    adequado
):
    """
    Fator de ajuste do IQF.
    """

    muito_critico = percentual_para_proporcao(
        muito_critico
    )

    adequado = percentual_para_proporcao(
        adequado
    )

    return (
        (1 - muito_critico) ** 2
        * (1 + adequado) ** 2
    )


def calcular_disciplina_iqf(
    df,
    prefixo,
    disciplina
):

    if prefixo not in [
        "iqf5",
        "iqf9"
    ]:
        raise ValueError(
            "Prefixo deve ser 'iqf5' ou 'iqf9'."
        )

    if disciplina not in [
        "mat",
        "lp"
    ]:
        raise ValueError(
            "Disciplina deve ser 'mat' ou 'lp'."
        )

    # --------------------------------------------------------
    # Resultados 2023 e 2024
    # --------------------------------------------------------

    for ano in [
        2023,
        2024
    ]:

        # Fator

        df[
            f"{prefixo}_{disciplina}_fator_{ano}"
        ] = fator_ajuste_iqf(

            df[
                f"{prefixo}_{disciplina}_"
                f"muito_critico_{ano}"
            ],

            df[
                f"{prefixo}_{disciplina}_"
                f"adequado_{ano}"
            ]
        )

        # Participação

        df[
            f"{prefixo}_{disciplina}_part_{ano}"
        ] = (

            df[
                f"{prefixo}_participacao_"
                f"{disciplina}_{ano}"
            ]

            / 100
        )

        # Resultado bruto

        df[
            f"{prefixo}_{disciplina}_resultado_{ano}"
        ] = (

            df[
                f"{prefixo}_proficiencia_"
                f"{disciplina}_{ano}"
            ]

            * df[
                f"{prefixo}_{disciplina}_part_{ano}"
            ]

            * df[
                f"{prefixo}_{disciplina}_fator_{ano}"
            ]
        )

        # Resultado padronizado

        df[
            f"{prefixo}_{disciplina}_"
            f"resultado_pad_{ano}"
        ] = padronizar_minmax(

            df[
                f"{prefixo}_{disciplina}_"
                f"resultado_{ano}"
            ]
        )

    # --------------------------------------------------------
    # Nível atual
    # --------------------------------------------------------

    df[
        f"{prefixo}_{disciplina}_nivel"
    ] = transformar_em_participacao(

        df[
            f"{prefixo}_{disciplina}_"
            f"resultado_pad_2024"
        ]
    )

    # --------------------------------------------------------
    # Evolução
    # --------------------------------------------------------

    df[
        f"{prefixo}_{disciplina}_evolucao"
    ] = (

        df[
            f"{prefixo}_{disciplina}_"
            f"resultado_pad_2024"
        ]

        -

        df[
            f"{prefixo}_{disciplina}_"
            f"resultado_pad_2023"
        ]
    )

    # --------------------------------------------------------
    # Padronização da evolução
    # --------------------------------------------------------

    df[
        f"{prefixo}_{disciplina}_evolucao_pad"
    ] = padronizar_minmax(

        df[
            f"{prefixo}_{disciplina}_evolucao"
        ]
    )

    # --------------------------------------------------------
    # Participação relativa da evolução
    # --------------------------------------------------------

    df[
        f"{prefixo}_{disciplina}_evolucao_indice"
    ] = transformar_em_participacao(

        df[
            f"{prefixo}_{disciplina}_evolucao_pad"
        ]
    )

    # --------------------------------------------------------
    # Índice da disciplina
    # --------------------------------------------------------

    df[
        f"{prefixo}_indice_{disciplina}"
    ] = (

        0.50
        * df[
            f"{prefixo}_{disciplina}_nivel"
        ]

        +

        0.50
        * df[
            f"{prefixo}_{disciplina}_evolucao_indice"
        ]
    )

    return df


def calcular_iqf(
    df,
    prefixo
):

    df = df.copy()

    # Matemática

    df = calcular_disciplina_iqf(
        df,
        prefixo,
        "mat"
    )

    # Língua Portuguesa

    df = calcular_disciplina_iqf(
        df,
        prefixo,
        "lp"
    )

    # IQF final

    df[
        f"{prefixo}_2025"
    ] = (

        0.50
        * df[
            f"{prefixo}_indice_mat"
        ]

        +

        0.50
        * df[
            f"{prefixo}_indice_lp"
        ]
    )

    return df


# ============================================================
# APROVAÇÃO
# ============================================================

def calcular_aprovacao(df):
    """
    Calcula a participação relativa da taxa média
    de aprovação do Ensino Fundamental.
    """

    df = df.copy()

    coluna = "taxa_aprovacao_2024"

    if coluna not in df.columns:
        raise ValueError(
            f"Coluna '{coluna}' não encontrada."
        )

    if df[coluna].isna().any():

        quantidade = (
            df[coluna]
            .isna()
            .sum()
        )

        raise ValueError(
            "Existem "
            f"{quantidade} valores ausentes "
            "na taxa de aprovação."
        )

    if (df[coluna] < 0).any():
        raise ValueError(
            "Existem taxas de aprovação negativas."
        )

    df["aprovacao_indice_2025"] = (
        transformar_em_participacao(
            df[coluna]
        )
    )

    return df


# ============================================================
# IQE_D
# ============================================================

def calcular_iqe_d(df):
    """
    Calcula o componente de desempenho do IQE.

    IQE_D =
        40% IQA
        30% IQF5
        25% IQF9
         5% Aprovação
    """

    df = df.copy()

    colunas_necessarias = [
        "iqa_transicao_2025",
        "iqf5_2025",
        "iqf9_2025",
        "aprovacao_indice_2025"
    ]

    for coluna in colunas_necessarias:

        if coluna not in df.columns:
            raise ValueError(
                "Coluna necessária ao IQE_D "
                f"não encontrada: {coluna}"
            )

    # Componentes

    df["iqe_d_componente_iqa"] = (
        0.40
        * df["iqa_transicao_2025"]
    )

    df["iqe_d_componente_iqf5"] = (
        0.30
        * df["iqf5_2025"]
    )

    df["iqe_d_componente_iqf9"] = (
        0.25
        * df["iqf9_2025"]
    )

    df["iqe_d_componente_aprovacao"] = (
        0.05
        * df["aprovacao_indice_2025"]
    )

    # IQE_D final

    df["iqe_d_2025"] = (

        df["iqe_d_componente_iqa"]

        + df["iqe_d_componente_iqf5"]

        + df["iqe_d_componente_iqf9"]

        + df["iqe_d_componente_aprovacao"]
    )

    return df


# ============================================================
# IQE_S E IQE FINAL
# ============================================================

def calcular_iqe_s_e_final(df):
    """
    Calcula o componente socioeconômico e o IQE final.

    ISE relativo =
        ISE_i / soma(ISE)

    ISE ajustado =
        IQE_D / ISE relativo

    IQE_S =
        ISE ajustado / soma(ISE ajustado)

    IQE final =
        95% IQE_D + 5% IQE_S

    Coeficiente Educação =
        IQE final * 18
    """

    df = df.copy()

    # IMPORTANTE:
    # Este é o nome real encontrado no base_iqe_2025.csv.
    coluna_ise = "inse_spaece_2024"

    # --------------------------------------------------------
    # Validações
    # --------------------------------------------------------

    colunas_necessarias = [
        "iqe_d_2025",
        coluna_ise
    ]

    for coluna in colunas_necessarias:

        if coluna not in df.columns:
            raise ValueError(
                "Coluna necessária ao cálculo do IQE_S "
                f"não encontrada: {coluna}"
            )

    if df[coluna_ise].isna().any():

        quantidade = (
            df[coluna_ise]
            .isna()
            .sum()
        )

        raise ValueError(
            f"Existem {quantidade} valores ausentes "
            "no indicador socioeconômico."
        )

    if (df[coluna_ise] <= 0).any():
        raise ValueError(
            "Existem valores menores ou iguais a zero "
            "no indicador socioeconômico."
        )

    # --------------------------------------------------------
    # ISE relativo
    # --------------------------------------------------------

    df["ise_relativo_2025"] = (
        transformar_em_participacao(
            df[coluna_ise]
        )
    )

    # --------------------------------------------------------
    # ISE ajustado
    # --------------------------------------------------------

    df["ise_ajustado_2025"] = (
        df["iqe_d_2025"]
        / df["ise_relativo_2025"]
    )

    # --------------------------------------------------------
    # IQE_S
    # --------------------------------------------------------

    df["iqe_s_2025"] = (
        transformar_em_participacao(
            df["ise_ajustado_2025"]
        )
    )

    # --------------------------------------------------------
    # Componentes do IQE final
    # --------------------------------------------------------

    df["iqe_componente_desempenho"] = (
        0.95
        * df["iqe_d_2025"]
    )

    df["iqe_componente_socioeconomico"] = (
        0.05
        * df["iqe_s_2025"]
    )

    # --------------------------------------------------------
    # IQE final
    # --------------------------------------------------------

    df["iqe_final_2025"] = (
        df["iqe_componente_desempenho"]
        + df["iqe_componente_socioeconomico"]
    )

    # --------------------------------------------------------
    # Coeficiente da Educação
    # --------------------------------------------------------

    df["coeficiente_educacao_calculado"] = (
        df["iqe_final_2025"]
        * 18
    )

    return df


# ============================================================
# TESTES DE CONSISTÊNCIA
# ============================================================

def mostrar_testes(df):

    print("\n" + "=" * 70)
    print("TESTES DE CONSISTÊNCIA")
    print("=" * 70)

    # ========================================================
    # IQA
    # ========================================================

    print("\nIQA")

    print(
        "Soma IQALP novo: "
        f"{df['iqalp_novo_2025'].sum():.10f}"
    )

    print(
        "Soma IQAMT novo: "
        f"{df['iqamt_novo_2025'].sum():.10f}"
    )

    print(
        "Soma IQA novo: "
        f"{df['iqa_novo_2025'].sum():.10f}"
    )

    print(
        "Soma IQA antigo: "
        f"{df['iqa_2024'].sum():.10f}"
    )

    print(
        "Soma IQA transição: "
        f"{df['iqa_transicao_2025'].sum():.10f}"
    )

    # ========================================================
    # IQF5
    # ========================================================

    print("\nIQF5")

    print(
        "Soma índice Matemática: "
        f"{df['iqf5_indice_mat'].sum():.10f}"
    )

    print(
        "Soma índice LP: "
        f"{df['iqf5_indice_lp'].sum():.10f}"
    )

    print(
        "Soma IQF5: "
        f"{df['iqf5_2025'].sum():.10f}"
    )

    print(
        "\nEVOLUÇÃO IQF5 — MATEMÁTICA"
    )

    print(
        "Mínimo: "
        f"{df['iqf5_mat_evolucao'].min():.10f}"
    )

    print(
        "Máximo: "
        f"{df['iqf5_mat_evolucao'].max():.10f}"
    )

    print(
        "\nEVOLUÇÃO IQF5 — LP"
    )

    print(
        "Mínimo: "
        f"{df['iqf5_lp_evolucao'].min():.10f}"
    )

    print(
        "Máximo: "
        f"{df['iqf5_lp_evolucao'].max():.10f}"
    )

    # ========================================================
    # IQF9
    # ========================================================

    print("\nIQF9")

    print(
        "Soma índice Matemática: "
        f"{df['iqf9_indice_mat'].sum():.10f}"
    )

    print(
        "Soma índice LP: "
        f"{df['iqf9_indice_lp'].sum():.10f}"
    )

    print(
        "Soma IQF9: "
        f"{df['iqf9_2025'].sum():.10f}"
    )

    print(
        "\nEVOLUÇÃO IQF9 — MATEMÁTICA"
    )

    print(
        "Mínimo: "
        f"{df['iqf9_mat_evolucao'].min():.10f}"
    )

    print(
        "Máximo: "
        f"{df['iqf9_mat_evolucao'].max():.10f}"
    )

    print(
        "\nEVOLUÇÃO IQF9 — LP"
    )

    print(
        "Mínimo: "
        f"{df['iqf9_lp_evolucao'].min():.10f}"
    )

    print(
        "Máximo: "
        f"{df['iqf9_lp_evolucao'].max():.10f}"
    )

    # ========================================================
    # APROVAÇÃO
    # ========================================================

    print("\nAPROVAÇÃO")

    print(
        "Soma índice aprovação: "
        f"{df['aprovacao_indice_2025'].sum():.10f}"
    )

    print(
        "Menor taxa de aprovação: "
        f"{df['taxa_aprovacao_2024'].min():.10f}%"
    )

    print(
        "Maior taxa de aprovação: "
        f"{df['taxa_aprovacao_2024'].max():.10f}%"
    )

    # ========================================================
    # IQE_D
    # ========================================================

    print("\nIQE_D")

    print(
        "Soma componente IQA: "
        f"{df['iqe_d_componente_iqa'].sum():.10f}"
    )

    print(
        "Soma componente IQF5: "
        f"{df['iqe_d_componente_iqf5'].sum():.10f}"
    )

    print(
        "Soma componente IQF9: "
        f"{df['iqe_d_componente_iqf9'].sum():.10f}"
    )

    print(
        "Soma componente aprovação: "
        f"{df['iqe_d_componente_aprovacao'].sum():.10f}"
    )

    print(
        "Soma IQE_D: "
        f"{df['iqe_d_2025'].sum():.10f}"
    )

    print(
        "Menor IQE_D: "
        f"{df['iqe_d_2025'].min():.10f}"
    )

    print(
        "Maior IQE_D: "
        f"{df['iqe_d_2025'].max():.10f}"
    )

    # ========================================================
    # IQE_S
    # ========================================================

    print("\nIQE_S")

    print(
        "Soma ISE relativo: "
        f"{df['ise_relativo_2025'].sum():.10f}"
    )

    print(
        "Soma IQE_S: "
        f"{df['iqe_s_2025'].sum():.10f}"
    )

    print(
        "Menor IQE_S: "
        f"{df['iqe_s_2025'].min():.10f}"
    )

    print(
        "Maior IQE_S: "
        f"{df['iqe_s_2025'].max():.10f}"
    )

    # ========================================================
    # IQE FINAL
    # ========================================================

    print("\nIQE FINAL")

    print(
        "Soma componente desempenho (95%): "
        f"{df['iqe_componente_desempenho'].sum():.10f}"
    )

    print(
        "Soma componente socioeconômico (5%): "
        f"{df['iqe_componente_socioeconomico'].sum():.10f}"
    )

    print(
        "Soma IQE final: "
        f"{df['iqe_final_2025'].sum():.10f}"
    )

    print(
        "Soma coeficiente Educação: "
        f"{df['coeficiente_educacao_calculado'].sum():.10f}"
    )


# ============================================================
# DIAGNÓSTICO — ABAIARA
# ============================================================

def mostrar_abaiara(df):

    linha = df[
        df["municipio"]
        .str.upper()
        == "ABAIARA"
    ]

    if linha.empty:

        print(
            "\nAbaiara não encontrada."
        )

        return

    r = linha.iloc[0]

    print("\n" + "=" * 70)
    print("DIAGNÓSTICO — ABAIARA")
    print("=" * 70)

    # ========================================================
    # IQA
    # ========================================================

    print("\nIQA")

    print(
        "IQA antigo 2024: "
        f"{r['iqa_2024']:.10f}"
    )

    print(
        "IQA novo 2025: "
        f"{r['iqa_novo_2025']:.10f}"
    )

    print(
        "IQA transição 2025: "
        f"{r['iqa_transicao_2025']:.10f}"
    )

    # ========================================================
    # IQF5 — MATEMÁTICA
    # ========================================================

    print("\nIQF5 — MATEMÁTICA")

    print(
        "Fator 2023: "
        f"{r['iqf5_mat_fator_2023']:.10f}"
    )

    print(
        "Fator 2024: "
        f"{r['iqf5_mat_fator_2024']:.10f}"
    )

    print(
        "Resultado bruto 2023: "
        f"{r['iqf5_mat_resultado_2023']:.10f}"
    )

    print(
        "Resultado bruto 2024: "
        f"{r['iqf5_mat_resultado_2024']:.10f}"
    )

    print(
        "Resultado padronizado 2023: "
        f"{r['iqf5_mat_resultado_pad_2023']:.10f}"
    )

    print(
        "Resultado padronizado 2024: "
        f"{r['iqf5_mat_resultado_pad_2024']:.10f}"
    )

    print(
        "Evolução: "
        f"{r['iqf5_mat_evolucao']:.10f}"
    )

    print(
        "Índice Matemática: "
        f"{r['iqf5_indice_mat']:.10f}"
    )

    # ========================================================
    # IQF5 — LP
    # ========================================================

    print("\nIQF5 — LÍNGUA PORTUGUESA")

    print(
        "Fator 2023: "
        f"{r['iqf5_lp_fator_2023']:.10f}"
    )

    print(
        "Fator 2024: "
        f"{r['iqf5_lp_fator_2024']:.10f}"
    )

    print(
        "Resultado bruto 2023: "
        f"{r['iqf5_lp_resultado_2023']:.10f}"
    )

    print(
        "Resultado bruto 2024: "
        f"{r['iqf5_lp_resultado_2024']:.10f}"
    )

    print(
        "Resultado padronizado 2023: "
        f"{r['iqf5_lp_resultado_pad_2023']:.10f}"
    )

    print(
        "Resultado padronizado 2024: "
        f"{r['iqf5_lp_resultado_pad_2024']:.10f}"
    )

    print(
        "Evolução: "
        f"{r['iqf5_lp_evolucao']:.10f}"
    )

    print(
        "Índice LP: "
        f"{r['iqf5_indice_lp']:.10f}"
    )

    print("\nIQF5 FINAL")

    print(
        "IQF5 2025: "
        f"{r['iqf5_2025']:.10f}"
    )

    # ========================================================
    # IQF9 — MATEMÁTICA
    # ========================================================

    print("\nIQF9 — MATEMÁTICA")

    print(
        "Fator 2023: "
        f"{r['iqf9_mat_fator_2023']:.10f}"
    )

    print(
        "Fator 2024: "
        f"{r['iqf9_mat_fator_2024']:.10f}"
    )

    print(
        "Resultado bruto 2023: "
        f"{r['iqf9_mat_resultado_2023']:.10f}"
    )

    print(
        "Resultado bruto 2024: "
        f"{r['iqf9_mat_resultado_2024']:.10f}"
    )

    print(
        "Resultado padronizado 2023: "
        f"{r['iqf9_mat_resultado_pad_2023']:.10f}"
    )

    print(
        "Resultado padronizado 2024: "
        f"{r['iqf9_mat_resultado_pad_2024']:.10f}"
    )

    print(
        "Evolução: "
        f"{r['iqf9_mat_evolucao']:.10f}"
    )

    print(
        "Índice Matemática: "
        f"{r['iqf9_indice_mat']:.10f}"
    )

    # ========================================================
    # IQF9 — LP
    # ========================================================

    print("\nIQF9 — LÍNGUA PORTUGUESA")

    print(
        "Fator 2023: "
        f"{r['iqf9_lp_fator_2023']:.10f}"
    )

    print(
        "Fator 2024: "
        f"{r['iqf9_lp_fator_2024']:.10f}"
    )

    print(
        "Resultado bruto 2023: "
        f"{r['iqf9_lp_resultado_2023']:.10f}"
    )

    print(
        "Resultado bruto 2024: "
        f"{r['iqf9_lp_resultado_2024']:.10f}"
    )

    print(
        "Resultado padronizado 2023: "
        f"{r['iqf9_lp_resultado_pad_2023']:.10f}"
    )

    print(
        "Resultado padronizado 2024: "
        f"{r['iqf9_lp_resultado_pad_2024']:.10f}"
    )

    print(
        "Evolução: "
        f"{r['iqf9_lp_evolucao']:.10f}"
    )

    print(
        "Índice LP: "
        f"{r['iqf9_indice_lp']:.10f}"
    )

    print("\nIQF9 FINAL")

    print(
        "IQF9 2025: "
        f"{r['iqf9_2025']:.10f}"
    )

    # ========================================================
    # APROVAÇÃO
    # ========================================================

    print("\nAPROVAÇÃO")

    print(
        "Taxa de aprovação 2024: "
        f"{r['taxa_aprovacao_2024']:.10f}%"
    )

    print(
        "Índice relativo aprovação: "
        f"{r['aprovacao_indice_2025']:.10f}"
    )

    # ========================================================
    # IQE_D
    # ========================================================

    print("\nIQE_D")

    print(
        "Componente IQA (40%): "
        f"{r['iqe_d_componente_iqa']:.10f}"
    )

    print(
        "Componente IQF5 (30%): "
        f"{r['iqe_d_componente_iqf5']:.10f}"
    )

    print(
        "Componente IQF9 (25%): "
        f"{r['iqe_d_componente_iqf9']:.10f}"
    )

    print(
        "Componente aprovação (5%): "
        f"{r['iqe_d_componente_aprovacao']:.10f}"
    )

    print(
        "IQE_D 2025: "
        f"{r['iqe_d_2025']:.10f}"
    )

    # ========================================================
    # COMPONENTE SOCIOECONÔMICO
    # ========================================================

    print("\nCOMPONENTE SOCIOECONÔMICO")

    print(
        "INSE / ISE SPAECE 2024: "
        f"{r['inse_spaece_2024']:.10f}"
    )

    print(
        "ISE relativo: "
        f"{r['ise_relativo_2025']:.10f}"
    )

    print(
        "ISE ajustado: "
        f"{r['ise_ajustado_2025']:.10f}"
    )

    print(
        "IQE_S 2025: "
        f"{r['iqe_s_2025']:.10f}"
    )

    # ========================================================
    # IQE FINAL
    # ========================================================

    print("\nIQE FINAL")

    print(
        "Componente desempenho (95%): "
        f"{r['iqe_componente_desempenho']:.10f}"
    )

    print(
        "Componente socioeconômico (5%): "
        f"{r['iqe_componente_socioeconomico']:.10f}"
    )

    print(
        "IQE final 2025: "
        f"{r['iqe_final_2025']:.10f}"
    )

    print(
        "Coeficiente Educação calculado: "
        f"{r['coeficiente_educacao_calculado']:.10f}"
    )

    # --------------------------------------------------------
    # Comparação com o coeficiente oficial de Abaiara
    # --------------------------------------------------------

    coeficiente_oficial_abaiara = 0.0753664

    diferenca = (
        r["coeficiente_educacao_calculado"]
        - coeficiente_oficial_abaiara
    )

    diferenca_percentual = (
        diferenca
        / coeficiente_oficial_abaiara
        * 100
    )

    print(
        "Coeficiente Educação oficial esperado: "
        f"{coeficiente_oficial_abaiara:.7f}"
    )

    print(
        "Diferença absoluta para o oficial: "
        f"{diferenca:.10f}"
    )

    print(
        "Diferença percentual para o oficial: "
        f"{diferenca_percentual:.4f}%"
    )


# ============================================================
# EXECUÇÃO
# ============================================================

def main():

    print("=" * 70)

    print(
        "CÁLCULO COMPLETO DO IQE — "
        "IQA + IQF5 + IQF9 + APROVAÇÃO + IQE_D + IQE_S"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Carregamento
    # --------------------------------------------------------

    df = carregar_base()

    print(
        f"\nMunicípios carregados: "
        f"{len(df)}"
    )

    # --------------------------------------------------------
    # IQA
    # --------------------------------------------------------

    print(
        "\nCalculando IQA..."
    )

    df = calcular_iqa(
        df
    )

    # --------------------------------------------------------
    # IQF5
    # --------------------------------------------------------

    print(
        "Calculando IQF do 5º ano..."
    )

    df = calcular_iqf(
        df,
        "iqf5"
    )

    # --------------------------------------------------------
    # IQF9
    # --------------------------------------------------------

    print(
        "Calculando IQF do 9º ano..."
    )

    df = calcular_iqf(
        df,
        "iqf9"
    )

    # --------------------------------------------------------
    # Aprovação
    # --------------------------------------------------------

    print(
        "Calculando índice de aprovação..."
    )

    df = calcular_aprovacao(
        df
    )

    # --------------------------------------------------------
    # IQE_D
    # --------------------------------------------------------

    print(
        "Calculando IQE_D..."
    )

    df = calcular_iqe_d(
        df
    )

    # --------------------------------------------------------
    # IQE_S + IQE final
    # --------------------------------------------------------

    print(
        "Calculando IQE_S e IQE final..."
    )

    df = calcular_iqe_s_e_final(
        df
    )

    # --------------------------------------------------------
    # Testes
    # --------------------------------------------------------

    mostrar_testes(
        df
    )

    # --------------------------------------------------------
    # Diagnóstico de Abaiara
    # --------------------------------------------------------

    mostrar_abaiara(
        df
    )

    # --------------------------------------------------------
    # Exportação
    # --------------------------------------------------------

    df.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"\nArquivo criado:\n"
        f"{ARQUIVO_SAIDA}"
    )

    print(
        f"\nLinhas exportadas: "
        f"{len(df)}"
    )

    print(
        f"Colunas exportadas: "
        f"{len(df.columns)}"
    )

    print("\n" + "=" * 70)

    print(
        "CÁLCULO CONCLUÍDO"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()