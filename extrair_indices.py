import pandas as pd


ARQUIVO_ENTRADA = "fontes/indices_icms_2026.xlsx"
ARQUIVO_SAIDA = "data/indices_2026.csv"


# ==================================================
# LEITURA DO EXCEL
# ==================================================

df = pd.read_excel(
    ARQUIVO_ENTRADA,
    sheet_name=0,
    header=1
)


# ==================================================
# PADRONIZAÇÃO DOS NOMES DAS COLUNAS
# ==================================================

df.columns = [
    str(coluna).strip()
    for coluna in df.columns
]


# ==================================================
# SELEÇÃO DAS COLUNAS NECESSÁRIAS
# ==================================================

df = df[
    [
        "Cód. Município",
        "Município",
        "VAF 2023",
        "VAF 2024",
        "Média VAF",
        "Índice Valor Adicionado",
        "Índice Educação",
        "Índice Saúde",
        "Índice Meio Ambiente",
        "Índice 2026"
    ]
].copy()


# ==================================================
# RENOMEIA AS COLUNAS
# ==================================================

df = df.rename(
    columns={
        "Cód. Município": "codigo_municipio",
        "Município": "municipio",
        "VAF 2023": "vaf_2023",
        "VAF 2024": "vaf_2024",
        "Média VAF": "media_vaf",
        "Índice Valor Adicionado": "indice_vaf",
        "Índice Educação": "indice_educacao",
        "Índice Saúde": "indice_saude",
        "Índice Meio Ambiente": "indice_meio_ambiente",
        "Índice 2026": "indice_2026"
    }
)


# ==================================================
# LIMPEZA
# ==================================================

df = df.dropna(
    subset=[
        "codigo_municipio",
        "municipio",
        "indice_2026"
    ]
)


df["codigo_municipio"] = pd.to_numeric(
    df["codigo_municipio"],
    errors="coerce"
)


df = df.dropna(
    subset=[
        "codigo_municipio"
    ]
)


df["codigo_municipio"] = (
    df["codigo_municipio"]
    .astype(int)
)


# ==================================================
# CONVERSÃO DAS COLUNAS NUMÉRICAS
# ==================================================

colunas_numericas = [
    "vaf_2023",
    "vaf_2024",
    "media_vaf",
    "indice_vaf",
    "indice_educacao",
    "indice_saude",
    "indice_meio_ambiente",
    "indice_2026"
]


for coluna in colunas_numericas:

    df[coluna] = pd.to_numeric(
        df[coluna],
        errors="coerce"
    )


# ==================================================
# ORDENAÇÃO
# ==================================================

df = df.sort_values(
    "municipio"
).reset_index(
    drop=True
)


# ==================================================
# SALVA O CSV
# ==================================================

df.to_csv(
    ARQUIVO_SAIDA,
    index=False,
    encoding="utf-8-sig"
)


# ==================================================
# RESULTADO
# ==================================================

print("\n==============================")
print("EXTRAÇÃO DOS ÍNDICES CONCLUÍDA")
print("==============================")

print(
    f"Municípios encontrados: {len(df)}"
)

print(
    f"Arquivo gerado: {ARQUIVO_SAIDA}"
)

print("\nColunas geradas:")

for coluna in df.columns:
    print(f"- {coluna}")