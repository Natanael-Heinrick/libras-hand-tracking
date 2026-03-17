import cv2
import mediapipe as mp
from collections import Counter
from hand_geometry import detectar_dedos
from letter_classifier import classificar_letra


# Inicializa mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# Utilitário para desenhar pontos
mp_draw = mp.solutions.drawing_utils

# Webcam
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
letra = ""
palavra = ""
ultima_letra = ""
historico_letras = []
letra_estavel = ""

while True:
    ret, frame = camera.read()

    if not ret:
        print("Erro ao acessar webcam")
        break

    # Converter BGR para RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Processar imagem
    results = hands.process(rgb_frame)

    # Se detectar mão
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            altura, largura, _ = frame.shape

            dedos = detectar_dedos(hand_landmarks)
            letra = classificar_letra(dedos, hand_landmarks)
            if letra != "":
                historico_letras.append(letra)

            if len(historico_letras) > 8:
                historico_letras.pop(0)

            if historico_letras:
                letra_estavel = Counter(historico_letras).most_common(1)[0][0]
            else:
                letra_estavel = ""

            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):  # espaço
                if letra_estavel != "":
                    palavra += letra_estavel

            if key == ord("c"):
                palavra = ""

            if key == 27:
                break

            print("Letra:", letra)

            print(dedos)
            # Desenhar pontos da mão
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    cv2.putText(
        frame,
        f"Letra: {letra_estavel}",
        (50, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0, 255, 0),
        3,
    )
    cv2.putText(
        frame,
        f"Palavra: {palavra}",
        (50, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 0, 0),
        3,
    )
    cv2.imshow("Hand Tracking", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord(" "):  # espaço adiciona letra
        if letra_estavel != "":
            palavra += letra_estavel
    elif key == ord("c"):  # limpa palavra
        palavra = ""

    elif key == 27:  # ESC sai

        break

camera.release()
cv2.destroyAllWindows()
