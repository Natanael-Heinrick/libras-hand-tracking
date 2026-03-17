def distancia(p1, p2):
    return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5


def dedo_estendido(hand, tip, pip):
    ponta = hand.landmark[tip].y
    junta = hand.landmark[pip].y

    return ponta < junta


def detectar_dedos(hand):

    dedos = []

    # polegar
    if hand.landmark[4].x > hand.landmark[3].x:
        dedos.append(1)
    else:
        dedos.append(0)

    # indicador
    dedos.append(1 if dedo_estendido(hand, 8, 6) else 0)

    # médio
    dedos.append(1 if dedo_estendido(hand, 12, 10) else 0)

    # anelar
    dedos.append(1 if dedo_estendido(hand, 16, 14) else 0)

    # mínimo
    dedos.append(1 if dedo_estendido(hand, 20, 18) else 0)

    return dedos
