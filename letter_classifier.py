from hand_geometry import distancia


def classificar_letra(dedos, hand):

    polegar = hand.landmark[4]
    indicador = hand.landmark[8]
    medio = hand.landmark[12]
    anelar = hand.landmark[16]
    minimo = hand.landmark[20]

    polegar = hand.landmark[4]

    if dedos == [1, 0, 0, 0, 0]:

        if (
            indicador.y > hand.landmark[6].y
            and medio.y > hand.landmark[10].y
            and anelar.y > hand.landmark[14].y
            and minimo.y > hand.landmark[18].y
        ):

            return "A"

    return ""
