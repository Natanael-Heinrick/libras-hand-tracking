from hand_geometry import distancia


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


def classificar_letra(dedos, hand, historico_k):

    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    historico_k.append(indicador.y)

    if len(historico_k) > 10:
        historico_k.pop(0)

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

    if dedos == [1, 1, 1, 1, 1]:

        d1 = distancia(polegar, indicador)
        d2 = distancia(indicador, minimo)

        print("d1:", d1, "d2:", d2)

        if 0.05 < d1 < 0.30 and d2 < 0.35:
            return "C"

    if dedos[1] == 1 and dedos[2] == 0 and dedos[3] == 0 and dedos[4] == 0:

        d1 = distancia(polegar, medio)
        d2 = distancia(polegar, anelar)

        if d1 < 0.08 and d2 < 0.10:
            return "D"

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
