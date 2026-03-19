from hand_geometry import distancia


def classificar_letra(dedos, hand):

    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

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

        if indicador.x > medio.x:

            d = distancia(indicador, medio)

            if d < 0.05:
                return "R"

    if dedos == [0, 0, 0, 0, 0]:

        dedos_y = (indicador.y + medio.y + anelar.y) / 3
        dx = abs(polegar.x - indicador.x)

        print("dx:", dx, "polegar.y:", polegar.y, "dedos_y:", dedos_y)

        # ✅ M → polegar escondido (alto + centralizado)
        if polegar.y < dedos_y and dx < 0.03:
            return "M"

        # ✅ S → polegar visível (mais lateral)
        if dx >= 0.03:
            return "S"

    print("distancia O:", distancia(polegar, indicador))
    return ""
