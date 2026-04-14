from hand_geometry import distancia


def detectar_c(dedos, hand):
    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    vetores_aceitos = (
        dedos == [1, 1, 1, 1, 1]
        or dedos == [1, 0, 0, 0, 0]
        or dedos == [1, 0, 0, 0, 1]
    )
    if not vetores_aceitos:
        return False

    d_polegar_indicador = distancia(polegar, indicador)
    d_indicador_minimo = distancia(indicador, minimo)
    curvatura_vertical = max(
        abs(indicador.y - medio.y),
        abs(medio.y - anelar.y),
        abs(anelar.y - minimo.y),
    )
    polegar_indicador_proximos_em_x = abs(polegar.x - indicador.x) < 0.08

    return (
        0.14 <= d_polegar_indicador <= 0.26
        and 0.03 <= d_indicador_minimo <= 0.11
        and curvatura_vertical <= 0.04
        and polegar_indicador_proximos_em_x
    )


def detectar_b(dedos, hand):
    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    if dedos[1:] != [1, 1, 1, 1]:
        return False

    y_pontas = [indicador.y, medio.y, anelar.y, minimo.y]
    alinhamento_dedos = max(y_pontas) - min(y_pontas)

    d_indicador_medio = distancia(indicador, medio)
    d_medio_anelar = distancia(medio, anelar)
    d_anelar_minimo = distancia(anelar, minimo)

    dedos_juntos = (
        d_indicador_medio < 0.12
        and d_medio_anelar < 0.12
        and d_anelar_minimo < 0.12
    )

    polegar_recolhido = (
        distancia(polegar, hand.landmark[9]) < 0.20
        and polegar.y > indicador.y
        and polegar.y > hand.landmark[5].y
        and polegar.y < hand.landmark[0].y
    )

    return alinhamento_dedos < 0.10 and dedos_juntos and polegar_recolhido


def detectar_l(dedos, hand):
    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    if dedos[1:] != [1, 0, 0, 0]:
        return False

    abertura = distancia(polegar, indicador)
    polegar_lateral = abs(polegar.x - indicador.x)

    outros_fechados = (
        medio.y > hand.landmark[10].y
        and anelar.y > hand.landmark[14].y
        and minimo.y > hand.landmark[18].y
    )

    indicador_vertical = indicador.y < hand.landmark[6].y
    polegar_horizontal = abs(polegar.y - hand.landmark[2].y) < 0.18

    return (
        abertura > 0.14
        and polegar_lateral > 0.09
        and indicador_vertical
        and polegar_horizontal
        and outros_fechados
    )


def detectar_q(hand):
    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    abertura = distancia(polegar, indicador)

    indicador_para_baixo = (
        indicador.y > hand.landmark[6].y
        and indicador.y > hand.landmark[5].y
    )

    outros_fechados = (
        medio.y > hand.landmark[10].y
        and anelar.y > hand.landmark[14].y
        and minimo.y > hand.landmark[18].y
    )

    indicador_proximo_do_polegar = abs(indicador.x - polegar.x) < 0.12

    return (
        0.14 < abertura < 0.22
        and indicador_para_baixo
        and outros_fechados
        and indicador_proximo_do_polegar
    )


def detectar_q_ajustado(dedos, hand):
    polegar = hand.landmark[4]
    indicador = hand.landmark[8]

    vetores_aceitos = (
        dedos == [1, 0, 1, 1, 1]
        or dedos == [1, 0, 0, 0, 0]
    )
    if not vetores_aceitos:
        return False

    abertura = distancia(polegar, indicador)
    indicador_para_baixo = indicador.y > hand.landmark[0].y and indicador.y > hand.landmark[6].y
    indicador_proximo_do_polegar = abs(indicador.x - polegar.x) < 0.10

    return (
        0.14 <= abertura <= 0.22
        and indicador_para_baixo
        and indicador_proximo_do_polegar
    )


def detectar_p(dedos, hand):
    polegar = hand.landmark[4]
    indicador = hand.landmark[8]

    vetores_aceitos = (
        dedos == [1, 0, 1, 0, 0]
        or dedos == [1, 1, 0, 1, 1]
    )
    if not vetores_aceitos:
        return False

    d_polegar_indicador = distancia(polegar, indicador)
    dx_polegar_indicador = abs(polegar.x - indicador.x)
    indicador_acima_punho = indicador.y < hand.landmark[0].y
    indicador_acima_base = indicador.y < hand.landmark[6].y

    return (
        0.14 <= d_polegar_indicador <= 0.24
        and dx_polegar_indicador >= 0.09
        and indicador_acima_punho
        and indicador_acima_base
    )


def classificar_letra(dedos, hand):
    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    if detectar_b(dedos, hand):
        return "B"

    if detectar_c(dedos, hand):
        return "C"

    if dedos[1] == 1 and dedos[2] == 0 and dedos[3] == 0 and dedos[4] == 0:
        d1 = distancia(polegar, medio)
        d2 = distancia(polegar, anelar)

        if d1 < 0.08 and d2 < 0.10:
            return "D"

    if detectar_l(dedos, hand):
        return "L"

    if dedos == [0, 0, 1, 1, 1]:
        if distancia(polegar, indicador) < 0.05:
            return "F"

    if detectar_p(dedos, hand):
        return "P"

    if dedos == [1, 1, 0, 0, 0]:
        if indicador.y < hand.landmark[6].y and abs(polegar.x - indicador.x) > 0.05:
            return "G"

    if dedos[4] == 1 and dedos[1] == 0 and dedos[2] == 0 and dedos[3] == 0:
        return "I"

    if dedos == [0, 0, 0, 1, 1]:
        if polegar.y < indicador.y and polegar.y < medio.y and polegar.y > anelar.y:
            return "N"

    if detectar_q_ajustado(dedos, hand) or detectar_q(hand):
        return "Q"

    if dedos == [1, 0, 0, 0, 0]:
        if distancia(polegar, indicador) < 0.07:
            return "O"
        return "A"

    if dedos == [0, 1, 1, 0, 0]:
        d = distancia(indicador, medio)
        base = distancia(indicador, anelar)
        d_norm = d / base
        dy = abs(indicador.y - medio.y)

        if d_norm < 0.4 and dy > 0.02:
            return "U"
        if d_norm < 0.6 and dy <= 0.02:
            return "R"
        return "V"

    if dedos == [0, 0, 0, 0, 0]:
        media_y_dedos = (indicador.y + medio.y + anelar.y) / 3
        dx = abs(polegar.x - indicador.x)

        d1 = distancia(polegar, indicador)
        d2 = distancia(polegar, medio)
        d3 = distancia(polegar, anelar)
        media = (d1 + d2 + d3) / 3

        if media < 0.09:
            return "S"
        if media < 0.13 and polegar.y > media_y_dedos:
            return "E"
        if polegar.y < media_y_dedos and dx < 0.03:
            return "M"

    if dedos == [1, 0, 1, 1, 1]:
        media_y_dedos = (indicador.y + medio.y + anelar.y) / 3
        dx = abs(polegar.x - indicador.x)

        if polegar.y > media_y_dedos and dx < 0.06:
            return "T"

    return ""


def calcular_metricas_debug(dedos, hand):
    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    return {
        "dedos": str(dedos),
        "c_d_polegar_indicador": round(distancia(polegar, indicador), 4),
        "c_d_indicador_minimo": round(distancia(indicador, minimo), 4),
        "c_curvatura_vertical": round(
            max(
                abs(indicador.y - medio.y),
                abs(medio.y - anelar.y),
                abs(anelar.y - minimo.y),
            ),
            4,
        ),
        "p_indicador_abaixo_punho": round(indicador.y - hand.landmark[0].y, 4),
        "p_d_polegar_indicador": round(distancia(polegar, indicador), 4),
        "q_abertura": round(distancia(polegar, indicador), 4),
        "q_indicador_abaixo_base": round(indicador.y - hand.landmark[6].y, 4),
        "q_dx_polegar_indicador": round(abs(indicador.x - polegar.x), 4),
        "q_outros_fechados": int(
            medio.y > hand.landmark[10].y
            and anelar.y > hand.landmark[14].y
            and minimo.y > hand.landmark[18].y
        ),
    }
