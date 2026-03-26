from collections import Counter
from threading import Lock

import cv2
import mediapipe as mp

from hand_geometry import detectar_dedos
from letter_classifier import classificar_letra


class HandTrackingService:
    DYNAMIC_LETTERS = {"H", "J", "K", "W"}
    DYNAMIC_LATCH_FRAMES = 12
    DYNAMIC_COOLDOWN_FRAMES = 8

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
        self.historico_k = []
        self.historico_h = {
            "inicio": None,
            "inicio_distancia": None,
            "ultimo": None,
            "ultima_distancia": None,
            "frames_pose": 0,
        }
        self.historico_w = {
            "inicio_y": None,
            "ultimo_y": None,
            "frames_pose": 0,
        }
        self.historico_j = []
        self.historico_dedos_j = []
        self.historico_letras_j = []
        self.dynamic_letter_latched = ""
        self.dynamic_latch_frames = 0
        self.dynamic_cooldown_letter = ""
        self.dynamic_cooldown_frames = 0

    def close(self):
        self.hands.close()

    def confirm_letter(self):
        if self.letra_estavel:
            self.palavra += self.letra_estavel

    def clear_word(self):
        self.palavra = ""

    def _tick_dynamic_windows(self):
        if self.dynamic_latch_frames > 0:
            self.dynamic_latch_frames -= 1
            if self.dynamic_latch_frames == 0:
                self.dynamic_letter_latched = ""

        if self.dynamic_cooldown_frames > 0:
            self.dynamic_cooldown_frames -= 1
            if self.dynamic_cooldown_frames == 0:
                self.dynamic_cooldown_letter = ""

    def process_frame(self, frame, draw_landmarks=False):
        with self.lock:
            self._tick_dynamic_windows()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            deteccoes = []

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    dedos = detectar_dedos(hand_landmarks)
                    self.letra = classificar_letra(
                        dedos,
                        hand_landmarks,
                        self.historico_k,
                        self.historico_h,
                        self.historico_w,
                        self.historico_j,
                        self.historico_dedos_j,
                        self.historico_letras_j,
                    )

                    letra_processada = self.letra

                    if (
                        letra_processada in self.DYNAMIC_LETTERS
                        and letra_processada == self.dynamic_cooldown_letter
                    ):
                        letra_processada = ""

                    if letra_processada in self.DYNAMIC_LETTERS:
                        self.dynamic_letter_latched = letra_processada
                        self.dynamic_latch_frames = self.DYNAMIC_LATCH_FRAMES
                        self.dynamic_cooldown_letter = letra_processada
                        self.dynamic_cooldown_frames = self.DYNAMIC_COOLDOWN_FRAMES

                    if letra_processada:
                        self.historico_letras.append(letra_processada)

                    if len(self.historico_letras) > 8:
                        self.historico_letras.pop(0)

                    if self.dynamic_letter_latched:
                        self.letra_estavel = self.dynamic_letter_latched
                    elif self.historico_letras:
                        self.letra_estavel = Counter(self.historico_letras).most_common(1)[0][0]
                    else:
                        self.letra_estavel = ""

                    self.letra = letra_processada or self.dynamic_letter_latched

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
                        }
                    )
            else:
                self.letra = ""
                if self.dynamic_letter_latched:
                    self.letra_estavel = self.dynamic_letter_latched
                else:
                    self.letra_estavel = ""

            state = {
                "letra": self.letra,
                "letra_estavel": self.letra_estavel,
                "palavra": self.palavra,
                "maos_detectadas": len(deteccoes),
                "deteccoes": deteccoes,
            }
            return state, frame
