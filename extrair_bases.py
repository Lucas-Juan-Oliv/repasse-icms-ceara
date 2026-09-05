import re
from pathlib import Path

import pandas as pd
import pdfplumber


PASTA_FONTES = Path("fontes")
ARQUIVO_SAIDA = Path("data/bases_icms_2026.csv")


ARQUIVOS = {
    "Janeiro": "portaria_jan_2026.pdf",
    "Fevereiro": "portaria_fev_2026.pdf",
    "Março": "portaria_mar_2026.pdf",
    "Abril": "portaria_abr_2026.pdf",
    "Maio": "portaria_mai_2026.pdf",
    "Junho": "portaria_jun_2026.pdf",
}


def converter_moeda_brasileira(valor):
    """
    Converte:
        1.923.303.904,52

    para:
        1923303904.52
    """

    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    return float(valor)


def extrair_texto_pdf(caminho):
    """
    Extrai todo o texto de um PDF.
    """

    texto_completo = ""

    with pdfplumber.open(caminho) as pdf:

        for pagina in pdf.pages:

            texto = pagina.extract_text()

            if texto:
                texto_completo += texto + "\n"

    return texto_completo


def extrair_base_icms(texto):
    """
    Localiza no texto:

    ICMS BASE DE CÁLCULO MUNICÍPIOS (100%) = R$ X
    """

    padrao = (
        r"ICMS\s+BASE\s+DE\s+C[ÁA]LCULO\s+MUNIC[ÍI]PIOS"
        r"\s*\(100%\)\s*=\s*R\$\s*"
        r"([\d\.]+,\d{2})"
    )

    resultado = re.search(
        padrao,
        texto,
        flags=re.IGNORECASE
    )

    if resultado is None:
        return None

    valor_texto = resultado.group(1)

    return converter_moeda_brasileira(valor_texto)


# ==================================================
# EXTRAÇÃO
# ==================================================

dados = []


for mes, arquivo in ARQUIVOS.items():

    caminho = PASTA_FONTES / arquivo

    print(f"Processando {mes}...")

    texto = extrair_texto_pdf(caminho)

    base_icms = extrair_base_icms(texto)

    if base_icms is None:

        print(
            f"ERRO: Base de ICMS não encontrada em {mes}."
        )

        continue

    print(
        f"Base encontrada: R$ {base_icms:,.2f}"
    )

    dados.append(
        {
            "mes": mes,
            "base_icms": base_icms
        }
    )


# ==================================================
# DATAFRAME
# ==================================================

df = pd.DataFrame(dados)


# ==================================================
# VALIDAÇÕES
# ==================================================

print("\n================================")
print("VALIDAÇÃO")
print("================================")

print(
    f"Meses encontrados: {len(df)}"
)

print()

print(
    df.to_string(index=False)
)


if len(df) != 6:
    raise ValueError(
        "ERRO: deveriam ter sido encontradas "
        "6 bases mensais."
    )


# ==================================================
# SALVA O CSV
# ==================================================

df.to_csv(
    ARQUIVO_SAIDA,
    index=False,
    encoding="utf-8-sig"
)


print("\n================================")
print("ARQUIVO GERADO")
print("================================")

print(ARQUIVO_SAIDA)