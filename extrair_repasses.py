import pandas as pd
from pathlib import Path


PASTA_FONTES = Path("fontes")
ARQUIVO_SAIDA = Path("data/repasses_sefaz_2026.csv")

ARQUIVOS = {
    "Janeiro": "portaria_jan_2026.xls",
    "Fevereiro": "portaria_fev_2026.xls",
    "Março": "portaria_mar_2026.xls",
    "Abril": "portaria_abr_2026.xls",
    "Maio": "portaria_mai_2026.xls",
    "Junho": "portaria_jun_2026.xls",
}


todos_repasses = []


for mes, nome_arquivo in ARQUIVOS.items():

    caminho = PASTA_FONTES / nome_arquivo

    print(f"\nProcessando {mes}...")
    print(caminho)

    # Lê a planilha sem assumir cabeçalho
    df = pd.read_excel(
        caminho,
        header=None,
        engine="xlrd"
    )

    # Pelo modelo oficial:
    # coluna 0 = Município
    # coluna 1 = ICMS Total
    # coluna 2 = ICMS Líquido
    # coluna 3 = FUNDEB
    df = df.iloc[:, 0:4].copy()

    df.columns = [
        "municipio",
        "repasse_sefaz",
        "repasse_liquido_sefaz",
        "fundeb_sefaz"
    ]

    # Converte valores financeiros
    colunas_numericas = [
        "repasse_sefaz",
        "repasse_liquido_sefaz",
        "fundeb_sefaz"
    ]

    for coluna in colunas_numericas:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce"
        )

    # Mantém apenas linhas que possuem valor de ICMS
    df = df.dropna(subset=["repasse_sefaz"])

    # Remove a linha Total
    df = df[
        df["municipio"]
        .astype(str)
        .str.strip()
        .str.lower()
        != "total"
    ]

    # Limpeza do nome
    df["municipio"] = (
        df["municipio"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    # Adiciona mês
    df.insert(0, "mes", mes)

    print(
        f"Municípios encontrados: {len(df)}"
    )

    todos_repasses.append(df)


# Junta os seis meses
resultado = pd.concat(
    todos_repasses,
    ignore_index=True
)


# --------------------------------------------------
# VALIDAÇÕES
# --------------------------------------------------

print("\n================================")
print("VALIDAÇÃO FINAL")
print("================================")

print(
    f"Registros encontrados: {len(resultado)}"
)

print("\nRegistros por mês:")

print(
    resultado
    .groupby("mes")
    .size()
)


# --------------------------------------------------
# SALVA CSV
# --------------------------------------------------

resultado.to_csv(
    ARQUIVO_SAIDA,
    index=False,
    encoding="utf-8-sig"
)

print("\nArquivo gerado:")
print(ARQUIVO_SAIDA)