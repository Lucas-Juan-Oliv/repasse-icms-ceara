def calcular_repasse(base_icms, indice_percentual):
    cota_municipios = base_icms * 0.25
    repasse_bruto = cota_municipios * (indice_percentual / 100)

    fundeb = repasse_bruto * 0.20
    repasse_liquido = repasse_bruto * 0.80

    return {
        "cota_municipios": cota_municipios,
        "repasse_bruto": repasse_bruto,
        "fundeb": fundeb,
        "repasse_liquido": repasse_liquido
    }