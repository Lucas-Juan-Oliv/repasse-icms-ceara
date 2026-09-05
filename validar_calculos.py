import unicodedata
import pandas as pd

from src.calculos import calcular_repasse


# ==================================================
# ARQUIVOS
# ==================================================

ARQUIVO_INDICES = "data/indices_2026.csv"
ARQUIVO_BASES = "data/bases_icms_2026.csv"
ARQUIVO_REPASSES = "data/repasses_sefaz_2026.csv"

ARQUIVO_SAIDA = "data/validacao_2026.csv"


# ==================================================
# FUNÇÃO DE NORMALIZAÇÃO DOS MUNICÍPIOS
# ==================================================

def normalizar_municipio(nome):
    """
    Padroniza o nome do município para permitir
    o cruzamento entre diferentes fontes.

    Exemplos:
        Acaraú -> ACARAU
        São Gonçalo do Amarante -> SAO GONCALO DO AMARANTE
    """

    nome = str(nome).strip().upper()

    nome = unicodedata.normalize(
        "NFKD",
        nome
    )

    nome = "".join(
        caractere
        for caractere in nome
        if not unicodedata.combining(caractere)
    )

    nome = " ".join(nome.split())

    return nome


# ==================================================
# LEITURA DOS DADOS
# ==================================================

indices = pd.read_csv(
    ARQUIVO_INDICES
)

bases = pd.read_csv(
    ARQUIVO_BASES
)

repasses = pd.read_csv(
    ARQUIVO_REPASSES
)


# ==================================================
# NORMALIZAÇÃO DOS NOMES
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
# GERA OS 1.104 REPASSES CALCULADOS
# ==================================================

resultados = []


for _, municipio in indices.iterrows():

    for _, mes in bases.iterrows():

        calculo = calcular_repasse(
            base_icms=mes["base_icms"],
            indice_percentual=municipio["indice_2026"]
        )

        resultados.append(
            {
                "municipio": municipio["municipio"],
                "municipio_chave": municipio["municipio_chave"],
                "mes": mes["mes"],
                "indice_2026": municipio["indice_2026"],
                "base_icms": mes["base_icms"],
                "repasse_calculado": calculo["repasse_bruto"],
                "fundeb_calculado": calculo["fundeb"],
                "liquido_calculado": calculo["repasse_liquido"]
            }
        )


calculados = pd.DataFrame(
    resultados
)


# ==================================================
# JUNTA COM OS REPASSES OFICIAIS DA SEFAZ
# ==================================================

validacao = calculados.merge(
    repasses[
        [
            "municipio_chave",
            "mes",
            "repasse_sefaz",
            "fundeb_sefaz",
            "repasse_liquido_sefaz"
        ]
    ],
    on=[
        "municipio_chave",
        "mes"
    ],
    how="left"
)


# ==================================================
# MÉTRICAS DE ERRO
# ==================================================

validacao["diferenca"] = (
    validacao["repasse_sefaz"]
    - validacao["repasse_calculado"]
)


validacao["erro_absoluto"] = (
    validacao["diferenca"]
    .abs()
)


validacao["erro_percentual"] = (
    validacao["erro_absoluto"]
    / validacao["repasse_sefaz"]
) * 100


# ==================================================
# VALIDAÇÃO DA BASE
# ==================================================

print("\n========================================")
print("VALIDAÇÃO DA BASE")
print("========================================")


print(
    f"Registros calculados: "
    f"{len(calculados)}"
)


print(
    f"Registros após cruzamento: "
    f"{len(validacao)}"
)


sem_sefaz = (
    validacao["repasse_sefaz"]
    .isna()
    .sum()
)


print(
    f"Registros sem correspondência SEFAZ: "
    f"{sem_sefaz}"
)


# ==================================================
# REGISTROS VÁLIDOS PARA AS MÉTRICAS
# ==================================================

validos = validacao.dropna(
    subset=[
        "repasse_sefaz",
        "repasse_calculado"
    ]
).copy()


# ==================================================
# MÉTRICAS GERAIS
# ==================================================

mae = (
    validos["erro_absoluto"]
    .mean()
)


erro_mediano = (
    validos["erro_absoluto"]
    .median()
)


mape = (
    validos["erro_percentual"]
    .mean()
)


erro_maximo = (
    validos["erro_absoluto"]
    .max()
)


print("\n========================================")
print("MÉTRICAS GERAIS")
print("========================================")


print(
    f"MAE: "
    f"R$ {mae:,.2f}"
)


print(
    f"Erro absoluto mediano: "
    f"R$ {erro_mediano:,.2f}"
)


print(
    f"MAPE: "
    f"{mape:.6f}%"
)


print(
    f"Maior erro absoluto: "
    f"R$ {erro_maximo:,.2f}"
)


# ==================================================
# 15 MAIORES ERROS
# ==================================================

maiores_erros = (
    validos
    .sort_values(
        "erro_absoluto",
        ascending=False
    )
    .head(15)
)


print("\n========================================")
print("15 MAIORES ERROS")
print("========================================")


print(
    maiores_erros[
        [
            "municipio",
            "mes",
            "repasse_calculado",
            "repasse_sefaz",
            "diferenca",
            "erro_absoluto",
            "erro_percentual"
        ]
    ].to_string(
        index=False
    )
)


# ==================================================
# MÉTRICAS POR MÊS
# ==================================================

por_mes = (
    validos
    .groupby("mes")
    .agg(
        registros=(
            "municipio",
            "count"
        ),
        mae=(
            "erro_absoluto",
            "mean"
        ),
        erro_mediano=(
            "erro_absoluto",
            "median"
        ),
        erro_maximo=(
            "erro_absoluto",
            "max"
        ),
        mape=(
            "erro_percentual",
            "mean"
        )
    )
    .reset_index()
)


print("\n========================================")
print("MÉTRICAS POR MÊS")
print("========================================")


print(
    por_mes.to_string(
        index=False
    )
)


# ==================================================
# MUNICÍPIOS SEM CORRESPONDÊNCIA
# ==================================================

if sem_sefaz > 0:

    print("\n========================================")
    print("MUNICÍPIOS SEM CORRESPONDÊNCIA")
    print("========================================")

    faltantes = (
        validacao[
            validacao["repasse_sefaz"]
            .isna()
        ][
            [
                "municipio",
                "municipio_chave",
                "mes"
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "municipio",
                "mes"
            ]
        )
    )

    print(
        faltantes.to_string(
            index=False
        )
    )


# ==================================================
# SALVA O RESULTADO
# ==================================================

validacao.to_csv(
    ARQUIVO_SAIDA,
    index=False,
    encoding="utf-8-sig"
)


print("\n========================================")
print("ARQUIVO GERADO")
print("========================================")


print(
    ARQUIVO_SAIDA
)