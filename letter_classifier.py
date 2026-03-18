from hand_geometry import distancia


def classificar_letra(dedos, hand):

    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    if dedos == [1, 0, 0, 0, 0]:

        if (
            indicador.y > hand.landmark[6].y
            and medio.y > hand.landmark[10].y
            and anelar.y > hand.landmark[14].y
            and minimo.y > hand.landmark[18].y
        ):

            return "A"

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

    if dedos == [1, 1, 0, 0, 0]:

        if indicador.y < hand.landmark[6].y:

            if abs(polegar.x - indicador.x) > 0.05:
                return "G"

    if dedos[4] == 1 and dedos[1] == 0 and dedos[2] == 0 and dedos[3] == 0:
        return "I"
    return ""
