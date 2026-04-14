from __future__ import annotations

import csv
import random
import time
from pathlib import Path

import cv2
import numpy as np

from loja.state import add_points, get_points


WINDOW_NAME = "Quiz Visual de LIBRAS"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
DISPLAY_SECONDS_PER_LETTER = 2.0
MAX_LIVES = 3
WORDS_CSV_PATH = Path(__file__).resolve().parent / "dados" / "animais_dificuldade.csv"
FALLBACK_WORDS = ["CASA", "DADO", "BOCA", "SOL", "LATA", "SALA", "MALA", "PATO"]


def load_letter_images() -> dict[str, Path]:
    images_dir = Path(__file__).resolve().parent / "imagens_maos"
    if not images_dir.exists():
        return {}

    letter_images = {}
    for image_path in sorted(images_dir.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        letter = "".join(char for char in image_path.stem.upper() if char.isalpha())
        if len(letter) != 1:
            continue

        letter_images[letter] = image_path

    return letter_images


def load_words(letter_images: dict[str, Path]) -> tuple[list[dict], str]:
    available_letters = set(letter_images.keys())
    words = []

    if WORDS_CSV_PATH.exists():
        with WORDS_CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                word = normalize_word(row.get("animal") or row.get("palavra") or "")
                if not word:
                    continue

                missing_letters = sorted({letter for letter in word if letter not in available_letters})
                if missing_letters:
                    continue

                words.append(
                    {
                        "word": word,
                        "difficulty": normalize_difficulty(row.get("dificuldade") or ""),
                        "source": "csv",
                    }
                )

        if words:
            return words, "csv"

    for word in FALLBACK_WORDS:
        normalized = normalize_word(word)
        if normalized and all(letter in available_letters for letter in normalized):
            words.append(
                {
                    "word": normalized,
                    "difficulty": "fallback",
                    "source": "fallback",
                }
            )

    return words, "fallback"


def normalize_word(value: str) -> str:
    return "".join(char for char in (value or "").upper() if char.isalpha())


def normalize_difficulty(value: str) -> str:
    normalized = (value or "").strip().lower()
    replacements = {
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized or "nao informada"


def create_canvas(width: int = 1280, height: int = 720) -> np.ndarray:
    canvas = np.full((height, width, 3), (18, 24, 38), dtype=np.uint8)
    cv2.rectangle(canvas, (40, 40), (560, 560), (34, 48, 74), -1)
    cv2.rectangle(canvas, (600, 40), (1240, 680), (24, 32, 48), -1)
    return canvas


def fit_image(image: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return cv2.resize(image, new_size)


def draw_text(
    canvas: np.ndarray,
    text: str,
    position: tuple[int, int],
    scale: float,
    color: tuple[int, int, int],
    thickness: int = 2,
):
    cv2.putText(canvas, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def render_screen(
    challenge: dict,
    letter_images: dict[str, Path],
    typed_answer: str,
    feedback: str,
    score: int,
    lives: int,
    round_number: int,
    total_rounds: int,
    stage: str,
    sequence_index: int,
    source_label: str,
) -> np.ndarray:
    canvas = create_canvas()
    current_letter = challenge["word"][sequence_index] if stage == "preview" else None

    image = None
    if current_letter:
        image_path = letter_images.get(current_letter)
        if image_path is not None:
            image = cv2.imread(str(image_path))

    if image is not None:
        fitted = fit_image(image, 480, 480)
        image_y = 60 + (480 - fitted.shape[0]) // 2
        image_x = 60 + (480 - fitted.shape[1]) // 2
        canvas[image_y : image_y + fitted.shape[0], image_x : image_x + fitted.shape[1]] = fitted
    else:
        draw_text(canvas, "Sem imagem", (170, 300), 1.2, (220, 220, 220), 2)

    draw_text(canvas, "Quiz Visual de LIBRAS", (630, 90), 1.0, (255, 255, 255), 2)
    draw_text(canvas, "Veja a sequencia de imagens e depois digite a palavra.", (630, 140), 0.8, (220, 220, 220), 2)
    draw_text(canvas, f"Rodada: {round_number}/{total_rounds}", (630, 190), 0.8, (255, 210, 120), 2)
    draw_text(canvas, f"Pontos: {score}", (630, 230), 0.8, (120, 255, 180), 2)
    draw_text(canvas, f"Vidas: {lives}/{MAX_LIVES}", (630, 270), 0.8, (255, 140, 140), 2)
    draw_text(canvas, f"Fonte: {source_label}", (630, 310), 0.7, (180, 210, 255), 2)
    draw_text(canvas, f"Dificuldade: {challenge.get('difficulty', 'nao informada')}", (630, 345), 0.7, (255, 210, 180), 2)

    if stage == "preview":
        draw_text(canvas, "Mostrando sequencia...", (630, 390), 0.95, (255, 255, 255), 2)
        draw_text(
            canvas,
            f"Imagem {sequence_index + 1} de {len(challenge['word'])}",
            (630, 450),
            0.8,
            (255, 255, 255),
            2,
        )
        draw_text(canvas, "Descubra a letra de cada imagem sem pista textual.", (630, 510), 0.72, (200, 255, 200), 2)
        draw_text(canvas, "Aguarde o fim da sequencia para responder.", (630, 555), 0.72, (200, 255, 200), 2)
        draw_text(canvas, "0 sai", (630, 620), 0.65, (255, 255, 255), 2)
    else:
        draw_text(canvas, "Digite a palavra formada pela sequencia.", (630, 390), 0.9, (255, 255, 255), 2)
        draw_text(canvas, "Sua resposta:", (630, 450), 0.9, (255, 255, 255), 2)
        draw_text(canvas, typed_answer or "_", (630, 505), 1.1, (120, 220, 255), 3)
        draw_text(canvas, feedback, (630, 565), 0.75, (180, 255, 180), 2)
        draw_text(canvas, "ENTER confirma | BACKSPACE apaga | 1 repete | 2 proxima | 0 sai", (630, 620), 0.62, (255, 255, 255), 2)

    draw_text(canvas, f"Palavra com {len(challenge['word'])} letras", (630, 575), 0.65, (210, 210, 210), 1)
    return canvas


def advance_index(index: int, total: int) -> int:
    if total <= 0:
        return 0
    return (index + 1) % total


def main():
    letter_images = load_letter_images()
    if not letter_images:
        raise RuntimeError("Nenhuma imagem de letra encontrada em quiz_visual_libras/imagens_maos")

    challenges, source = load_words(letter_images)
    if not challenges:
        raise RuntimeError("Nenhuma palavra valida encontrada para o quiz visual")

    random.shuffle(challenges)
    challenge_index = 0
    score = get_points()
    lives = MAX_LIVES
    typed_answer = ""
    feedback = "Aguarde a sequencia terminar."
    stage = "preview"
    sequence_index = 0
    last_switch = time.monotonic()

    while True:
        challenge = challenges[challenge_index]
        canvas = render_screen(
            challenge=challenge,
            letter_images=letter_images,
            typed_answer=typed_answer,
            feedback=feedback,
            score=score,
            lives=lives,
            round_number=challenge_index + 1,
            total_rounds=len(challenges),
            stage=stage,
            sequence_index=sequence_index,
            source_label=source,
        )
        cv2.imshow(WINDOW_NAME, canvas)

        wait_ms = 100 if stage == "preview" else 0
        key = cv2.waitKey(wait_ms)

        if key in (27, ord("0")):
            break

        if stage == "preview":
            now = time.monotonic()
            if now - last_switch >= DISPLAY_SECONDS_PER_LETTER:
                sequence_index += 1
                last_switch = now

                if sequence_index >= len(challenge["word"]):
                    stage = "answer"
                    sequence_index = len(challenge["word"]) - 1
                    typed_answer = ""
                    feedback = "Digite a palavra e pressione ENTER."
            continue

        if key in (8, 127):
            typed_answer = typed_answer[:-1]
            continue

        if key in (10, 13):
            normalized = normalize_word(typed_answer)
            if normalized == challenge["word"]:
                score = add_points(1)
                lives = MAX_LIVES
                feedback = f"Acertou: {challenge['word']}. Indo para a proxima."
                challenge_index = advance_index(challenge_index, len(challenges))
                stage = "preview"
                sequence_index = 0
                typed_answer = ""
                last_switch = time.monotonic()
            else:
                lives -= 1
                typed_answer = ""
                if lives <= 0:
                    score = add_points(-1)
                    lives = MAX_LIVES
                    stage = "preview"
                    sequence_index = 0
                    feedback = "Perdeu as 3 chances. Voltando ao inicio da palavra e removendo 1 ponto."
                    last_switch = time.monotonic()
                else:
                    feedback = f"Resposta incorreta. Restam {lives} chance(s)."
            continue

        if key == ord("1"):
            stage = "preview"
            sequence_index = 0
            typed_answer = ""
            feedback = f"Repetindo a sequencia. Vidas atuais: {lives}."
            last_switch = time.monotonic()
            continue

        if key == ord("2"):
            challenge_index = advance_index(challenge_index, len(challenges))
            stage = "preview"
            sequence_index = 0
            typed_answer = ""
            lives = MAX_LIVES
            feedback = "Pulou para a proxima palavra."
            last_switch = time.monotonic()
            continue

        if 32 <= key <= 126:
            typed_answer += chr(key)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
