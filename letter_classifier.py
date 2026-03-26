from hand_geometry import distancia


H_DISTANCE_DELTA_MIN = 0.025
H_Z_DELTA_MIN = 0.010
H_MIN_POSE_FRAMES = 4
W_UP_DELTA_MIN = 0.035
W_MIN_POSE_FRAMES = 4


def inicio_j_valido(dedos):
    return dedos[4] == 1


def detectar_j_sequencia(historico):

    if len(historico) < 10:
        return False

    inicio = historico[0]
    fim = historico[-1]

    inicio_ok = inicio_j_valido(inicio)
    fim_ok = fim[4] == 1 and fim[0] == 1

    meio_valido = any(
        dedos in ([0, 0, 0, 0, 0], [1, 0, 0, 0, 0], [0, 0, 0, 1, 0])
        for dedos in historico
    )

    return inicio_ok and fim_ok and meio_valido


def dedos_parecidos_com_j(dedos):
    # aceita pequenas variações
    return (
        dedos[4] == 1  # mindinho levantado
        and sum(dedos[:4]) <= 1  # no máximo 1 dedo extra levantado
    )


def detectar_j(dedos, historico_j, historico_dedos_j):

    curva = movimento_curva_j(historico_j)
    sequencia = detectar_j_sequencia(historico_dedos_j)

    if curva or sequencia:
        historico_j.clear()
        historico_dedos_j.clear()
        return True

    return False


def detectar_k(dedos, hand, historico_k):

    polegar = hand.landmark[4]
    medio = hand.landmark[12]

    if dedos == [1, 1, 1, 0, 0]:

        d = distancia(polegar, medio)

        if 0.15 < d < 0.40:
            if movimento_para_cima(historico_k):
                historico_k.clear()
                return True

    return False


def pose_parecida_com_h(dedos, hand):
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    dedos_base_validos = (
        dedos[1] == 1 and dedos[2] == 1 and dedos[3] == 0 and dedos[4] == 0
    )

    dedos_juntos = distancia(indicador, medio) < 0.12
    dedos_restantes_fechados = (
        anelar.y > hand.landmark[14].y and minimo.y > hand.landmark[18].y
    )

    return dedos_base_validos and dedos_juntos and dedos_restantes_fechados


def detectar_h(dedos, hand, estado_h):
    indicador = hand.landmark[8]
    medio = hand.landmark[12]

    if not pose_parecida_com_h(dedos, hand):
        estado_h["inicio"] = None
        estado_h["ultimo"] = None
        estado_h["frames_pose"] = 0
        return False

    profundidade_media = (indicador.z + medio.z) / 2
    distancia_dedos = distancia(indicador, medio)

    if estado_h["inicio"] is None:
        estado_h["inicio"] = profundidade_media
        estado_h["inicio_distancia"] = distancia_dedos
        estado_h["ultimo"] = profundidade_media
        estado_h["ultima_distancia"] = distancia_dedos
        estado_h["frames_pose"] = 1
        return False

    estado_h["ultimo"] = profundidade_media
    estado_h["ultima_distancia"] = distancia_dedos
    estado_h["frames_pose"] += 1

    if estado_h["frames_pose"] < H_MIN_POSE_FRAMES:
        return False

    diferenca_z = abs(estado_h["ultimo"] - estado_h["inicio"])
    diferenca_distancia = abs(estado_h["ultima_distancia"] - estado_h["inicio_distancia"])

    if diferenca_z > H_Z_DELTA_MIN or diferenca_distancia > H_DISTANCE_DELTA_MIN:
        estado_h["inicio"] = None
        estado_h["inicio_distancia"] = None
        estado_h["ultimo"] = None
        estado_h["ultima_distancia"] = None
        estado_h["frames_pose"] = 0
        return True

    return False


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


def detectar_y(dedos, hand):
    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    dedos_centrais_fechados = (
        indicador.y > hand.landmark[6].y
        and medio.y > hand.landmark[10].y
        and anelar.y > hand.landmark[14].y
    )

    minimo_levantado = minimo.y < hand.landmark[18].y
    abertura_polegar_minimo = distancia(polegar, minimo)
    polegar_afastado = abs(polegar.x - hand.landmark[2].x) > 0.05

    return (
        dedos_centrais_fechados
        and minimo_levantado
        and abertura_polegar_minimo > 0.18
        and polegar_afastado
    )


def pose_parecida_com_w(dedos, hand):
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    dedos_base_validos = (
        dedos[1] == 1 and dedos[2] == 1 and dedos[3] == 1 and dedos[4] == 0
    )

    minimo_fechado = minimo.y > hand.landmark[18].y
    dedos_levantados = (
        indicador.y < hand.landmark[6].y
        and medio.y < hand.landmark[10].y
        and anelar.y < hand.landmark[14].y
    )

    return dedos_base_validos and minimo_fechado and dedos_levantados


def detectar_w(dedos, hand, estado_w):
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]

    if not pose_parecida_com_w(dedos, hand):
        estado_w["inicio_y"] = None
        estado_w["ultimo_y"] = None
        estado_w["frames_pose"] = 0
        return False

    y_medio_mao = (indicador.y + medio.y + anelar.y) / 3

    if estado_w["inicio_y"] is None:
        estado_w["inicio_y"] = y_medio_mao
        estado_w["ultimo_y"] = y_medio_mao
        estado_w["frames_pose"] = 1
        return False

    estado_w["ultimo_y"] = y_medio_mao
    estado_w["frames_pose"] += 1

    if estado_w["frames_pose"] < W_MIN_POSE_FRAMES:
        return False

    subida = estado_w["inicio_y"] - estado_w["ultimo_y"]

    if subida > W_UP_DELTA_MIN:
        estado_w["inicio_y"] = None
        estado_w["ultimo_y"] = None
        estado_w["frames_pose"] = 0
        return True

    return False


def classificar_letra(
    dedos,
    hand,
    historico_k,
    historico_h,
    historico_w,
    historico_j,
    historico_dedos_j,
    historico_letras_j,
):

    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    if dedos_parecidos_com_j(dedos):
        historico_dedos_j.append(dedos)
        historico_j.append((minimo.x, minimo.y))

        if len(historico_dedos_j) > 20:
            historico_dedos_j.pop(0)

        if len(historico_j) > 20:
            historico_j.pop(0)
    else:
        historico_dedos_j.clear()
        historico_j.clear()

    print("HISTÓRICO:", historico_dedos_j)

    historico_k.append(indicador.y)

    if len(historico_k) > 10:
        historico_k.pop(0)

    letra_base = ""

    if dedos[4] == 1 and sum(dedos[:4]) <= 1:
        letra_base = "I"

    elif dedos == [0, 0, 0, 0, 0]:
        letra_base = "S"

    # salva histórico
    if letra_base:
        historico_letras_j.append(letra_base)

        # limita tamanho (janela deslizante)
        if len(historico_letras_j) > 20:
            historico_letras_j.pop(0)

    # prioridade J > K >:(
    if dedos_parecidos_com_j(dedos) and detectar_j(
        historico_dedos_j[-1], historico_j, historico_dedos_j
    ):
        return "J"

    if detectar_h(dedos, hand, historico_h):
        return "H"

    if detectar_w(dedos, hand, historico_w):
        return "W"

    # prioridade movimento do K >:(
    if detectar_k(dedos, hand, historico_k):
        return "K"

    # if dedos == [1, 0, 0, 0, 0]:

    #    if (
    #        indicador.y > hand.landmark[6].y
    #        and medio.y > hand.landmark[10].y
    #        and anelar.y > hand.landmark[14].y
    #       and minimo.y > hand.landmark[18].y
    #   ):

    #       print("distancia O:", distancia(polegar, indicador))
    #       return "A"

    if detectar_b(dedos, hand):
        return "B"

    if detectar_y(dedos, hand):
        return "Y"

    if dedos == [1, 1, 1, 1, 1]:

        d1 = distancia(polegar, indicador)
        d2 = distancia(indicador, minimo)
        curvatura_vertical = max(
            abs(indicador.y - medio.y),
            abs(medio.y - anelar.y),
            abs(anelar.y - minimo.y),
        )

        print("d1:", d1, "d2:", d2)

        if 0.08 < d1 < 0.22 and d2 < 0.35 and curvatura_vertical > 0.03:
            return "C"

    if dedos[1] == 1 and dedos[2] == 0 and dedos[3] == 0 and dedos[4] == 0:

        d1 = distancia(polegar, medio)
        d2 = distancia(polegar, anelar)

        if d1 < 0.08 and d2 < 0.10:
            return "D"

    if detectar_l(dedos, hand):
        return "L"

    if dedos == [0, 0, 1, 1, 1]:

        d = distancia(polegar, indicador)

        if d < 0.05:
            return "F"

    if dedos == [1, 0, 1, 0, 0]:
        if indicador.y > hand.landmark[0].y:

            d = distancia(polegar, indicador)

            if d > 0.10:
                return "P"

    if dedos == [1, 1, 0, 0, 0]:

        if indicador.y < hand.landmark[6].y:

            if abs(polegar.x - indicador.x) > 0.05:
                return "G"

    if dedos[4] == 1 and dedos[1] == 0 and dedos[2] == 0 and dedos[3] == 0:
        return "I"

    if dedos == [0, 0, 0, 1, 1]:

        if sum(dedos) <= 2:

            if polegar.y < indicador.y and polegar.y < medio.y and polegar.y > anelar.y:
                return "N"

    if detectar_q(hand):
        return "Q"

    if dedos == [1, 0, 0, 0, 0]:

        d = distancia(polegar, indicador)

        print("distancia O:", d)

        if d < 0.07:
            return "O"

        return "A"

    if dedos == [0, 1, 1, 0, 0]:

        d = distancia(indicador, medio)
        base = distancia(indicador, anelar)

        d_norm = d / base
        dx = abs(indicador.x - medio.x)
        dy = abs(indicador.y - medio.y)

        if d_norm < 0.4 and dy > 0.02:
            return "U"

        elif d_norm < 0.6 and dy <= 0.02:
            return "R"

        else:
            return "V"

    if dedos == [0, 0, 0, 0, 0]:

        dedos_y = (indicador.y + medio.y + anelar.y) / 3
        dx = abs(polegar.x - indicador.x)

        d1 = distancia(polegar, indicador)
        d2 = distancia(polegar, medio)
        d3 = distancia(polegar, anelar)

        media = (d1 + d2 + d3) / 3

        if media < 0.09:
            return "S"

        elif media < 0.13 and polegar.y > dedos_y:
            return "E"

        elif polegar.y < dedos_y and dx < 0.03:
            return "M"

    if dedos == [1, 0, 1, 1, 1]:

        dedos_y = (indicador.y + medio.y + anelar.y) / 3
        dx = abs(polegar.x - indicador.x)

        if polegar.y > dedos_y and dx < 0.06:
            return "T"

    indicador = hand.landmark[8]

    print("distancia O:", distancia(polegar, indicador))
    return ""


def movimento_para_cima(historico):
    if len(historico) < 3:
        return False

    subidas = 0

    for i in range(1, len(historico)):
        if historico[i] < historico[i - 1]:
            subidas += 1

    return subidas >= len(historico) * 0.7


def movimento_curva_j(historico):

    if len(historico) < 10:
        return False

    inicio = historico[0]
    meio = historico[len(historico) // 2]
    fim = historico[-1]

    dy_total = fim[1] - inicio[1]
    dx_total = fim[0] - inicio[0]

    desceu = meio[1] > inicio[1]
    subiu = fim[1] < meio[1]

    lateral = abs(dx_total) > 0.005

    curvatura = abs(meio[0] - inicio[0]) > 0.01

    return desceu and subiu and lateral and curvatura


def detectar_j_movimento(historico):

    if len(historico) < 10:
        return False

    xs = [p[0] for p in historico]
    ys = [p[1] for p in historico]

    dx_total = xs[-1] - xs[0]
    dy_total = ys[-1] - ys[0]

    # movimento geral (tem que se mover)
    movimento = abs(dx_total) > 0.01 or abs(dy_total) > 0.01

    # curva: desce e depois sobe
    meio = len(ys) // 2

    desceu = ys[meio] > ys[0]
    subiu = ys[-1] < ys[meio]

    return movimento and desceu and subiu


def detectar_j_por_dedos(historico):

    if len(historico) < 8:
        return False

    for i in range(len(historico)):

        inicio = historico[i]

        if inicio[4] == 1 and sum(inicio[:4]) <= 1:

            for j in range(i + 3, len(historico)):  # 👈 distância mínima

                fim = historico[j]

                if fim[4] == 1 and fim[0] == 1:
                    return True

    return False
