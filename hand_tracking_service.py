from collections import Counter
from threading import Lock

import cv2
import mediapipe as mp

from hand_geometry import detectar_dedos
from letter_classifier import calcular_metricas_debug, classificar_letra


class HandTrackingService:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands()
        self.lock = Lock()
        self.reset_state()

    def reset_state(self):
        self.letra = ""
        self.palavra = ""
        self.historico_letras = []
        self.letra_estavel = ""

    def close(self):
        self.hands.close()

    def confirm_letter(self):
        if self.letra_estavel:
            self.palavra += self.letra_estavel

    def clear_word(self):
        self.palavra = ""

    def process_frame(self, frame, draw_landmarks=False):
        with self.lock:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            deteccoes = []

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    dedos = detectar_dedos(hand_landmarks)
                    letra_processada = classificar_letra(dedos, hand_landmarks)

                    if letra_processada:
                        self.historico_letras.append(letra_processada)

                    if len(self.historico_letras) > 8:
                        self.historico_letras.pop(0)

                    if self.historico_letras:
                        self.letra_estavel = Counter(self.historico_letras).most_common(1)[0][0]
                    else:
                        self.letra_estavel = ""

                    self.letra = letra_processada

                    if draw_landmarks:
                        self.mp_draw.draw_landmarks(
                            frame,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                        )

                    deteccoes.append(
                        {
                            "dedos": dedos,
                            "letra_detectada": self.letra,
                            "metricas_debug": calcular_metricas_debug(dedos, hand_landmarks),
                        }
                    )
            else:
                self.letra = ""
                self.letra_estavel = ""

            state = {
                "letra": self.letra,
                "letra_estavel": self.letra_estavel,
                "palavra": self.palavra,
                "maos_detectadas": len(deteccoes),
                "deteccoes": deteccoes,
            }
            return state, frame
