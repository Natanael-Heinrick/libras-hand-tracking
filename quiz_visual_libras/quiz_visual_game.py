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

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720
SKY_HEIGHT = 500
IMAGE_PANEL = (48, 60, 574, 616)
INFO_PANEL = (628, 54, 1230, 664)

COLOR_SKY_TOP = (255, 178, 78)
COLOR_SKY_BOTTOM = (237, 226, 150)
COLOR_CLOUD = (246, 246, 255)
COLOR_CLOUD_SHADOW = (214, 224, 244)
COLOR_HILL = (62, 120, 62)
COLOR_GRASS = (68, 146, 78)
COLOR_GRASS_TOP = (96, 190, 92)
COLOR_GRASS_SHADOW = (56, 108, 50)
COLOR_WOOD_DARK = (102, 70, 40)
COLOR_WOOD = (132, 93, 55)
COLOR_WOOD_LIGHT = (160, 118, 72)
COLOR_WOOD_SOFT = (182, 140, 92)
COLOR_BORDER = (252, 232, 150)
COLOR_BORDER_SOFT = (255, 245, 170)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_SOFT = (246, 238, 224)
COLOR_MUTED = (236, 228, 210)
COLOR_ACCENT = (104, 216, 250)
COLOR_SUCCESS = (164, 238, 142)
COLOR_WARNING = (255, 240, 160)
COLOR_DANGER = (255, 178, 178)
COLOR_STATUS_BG = (44, 84, 62)
COLOR_CONTROLS = (88, 78, 52)
COLOR_PANEL_BLUE = (82, 120, 164)


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
        "Ã¡": "a",
        "Ã ": "a",
        "Ã¢": "a",
        "Ã£": "a",
        "Ã©": "e",
        "Ãª": "e",
        "Ã­": "i",
        "Ã³": "o",
        "Ã´": "o",
        "Ãµ": "o",
        "Ãº": "u",
        "Ã§": "c",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized or "nao informada"


def draw_text(
    canvas: np.ndarray,
    text: str,
    position: tuple[int, int],
    scale: float,
    color: tuple[int, int, int],
    thickness: int = 2,
):
    cv2.putText(canvas, text, position, cv2.FONT_HERSHEY_DUPLEX, scale, color, thickness, cv2.LINE_AA)


def draw_panel(
    canvas: np.ndarray,
    top_left: tuple[int, int],
    bottom_right: tuple[int, int],
    fill_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
    border_thickness: int = 3,
):
    x1, y1 = top_left
    x2, y2 = bottom_right
    cv2.rectangle(canvas, (x1 + 6, y1 + 6), (x2 + 6, y2 + 6), COLOR_WOOD_DARK, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), fill_color, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), border_color, border_thickness)


def draw_stat_card(
    canvas: np.ndarray,
    top_left: tuple[int, int],
    size: tuple[int, int],
    label: str,
    value: str,
    value_color: tuple[int, int, int],
):
    x, y = top_left
    width, height = size
    draw_panel(
        canvas,
        (x, y),
        (x + width, y + height),
        COLOR_WOOD_LIGHT,
        COLOR_BORDER_SOFT,
        2,
    )
    draw_text(canvas, label, (x + 14, y + 24), 0.48, COLOR_MUTED, 1)
    draw_text(canvas, value, (x + 14, y + 62), 0.84, value_color, 3)


def draw_pixel_cloud(canvas: np.ndarray, x: int, y: int, size: int):
    blocks = [
        (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 1), (4, 1),
        (1, 2), (2, 2), (3, 2),
    ]
    for col, row in blocks:
        x1 = x + col * size
        y1 = y + row * size
        cv2.rectangle(canvas, (x1, y1), (x1 + size, y1 + size), COLOR_CLOUD, -1)
        cv2.rectangle(canvas, (x1, y1 + size - 4), (x1 + size, y1 + size), COLOR_CLOUD_SHADOW, -1)


def create_canvas(width: int = CANVAS_WIDTH, height: int = CANVAS_HEIGHT) -> np.ndarray:
    canvas = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        ratio = min(1.0, y / max(1, SKY_HEIGHT))
        color = (
            int(COLOR_SKY_TOP[0] + (COLOR_SKY_BOTTOM[0] - COLOR_SKY_TOP[0]) * ratio),
            int(COLOR_SKY_TOP[1] + (COLOR_SKY_BOTTOM[1] - COLOR_SKY_TOP[1]) * ratio),
            int(COLOR_SKY_TOP[2] + (COLOR_SKY_BOTTOM[2] - COLOR_SKY_TOP[2]) * ratio),
        )
        cv2.line(canvas, (0, y), (width, y), color, 1)

    draw_pixel_cloud(canvas, 88, 52, 14)
    draw_pixel_cloud(canvas, 392, 38, 10)
    draw_pixel_cloud(canvas, 954, 74, 12)

    cv2.circle(canvas, (130, SKY_HEIGHT + 54), 118, COLOR_HILL, -1)
    cv2.circle(canvas, (412, SKY_HEIGHT + 66), 154, COLOR_HILL, -1)
    cv2.circle(canvas, (1030, SKY_HEIGHT + 60), 142, COLOR_HILL, -1)

    cv2.rectangle(canvas, (0, SKY_HEIGHT), (width, height), COLOR_GRASS, -1)
    cv2.rectangle(canvas, (0, SKY_HEIGHT), (width, SKY_HEIGHT + 16), COLOR_GRASS_TOP, -1)
    cv2.rectangle(canvas, (0, SKY_HEIGHT + 16), (width, SKY_HEIGHT + 34), COLOR_GRASS_SHADOW, -1)

    for x in range(0, width, 40):
        cv2.rectangle(canvas, (x, height - 18), (x + 20, height), COLOR_CONTROLS, -1)
    cv2.rectangle(canvas, (0, height - 18), (width, height), COLOR_WOOD, 2)

    draw_panel(canvas, (IMAGE_PANEL[0], IMAGE_PANEL[1]), (IMAGE_PANEL[2], IMAGE_PANEL[3]), COLOR_WOOD, COLOR_BORDER_SOFT, 4)
    draw_panel(canvas, (INFO_PANEL[0], INFO_PANEL[1]), (INFO_PANEL[2], INFO_PANEL[3]), COLOR_WOOD, COLOR_BORDER, 4)
    draw_panel(canvas, (646, 66), (1210, 118), COLOR_PANEL_BLUE, COLOR_BORDER_SOFT, 3)

    return canvas


def fit_image(image: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
    height, width = image.shape[:2]
    scale = min(max_width / width, max_height / height)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return cv2.resize(image, new_size)


def get_feedback_color(stage: str, feedback: str) -> tuple[int, int, int]:
    if stage == "preview":
        return COLOR_ACCENT
    lowered = (feedback or "").lower()
    if "acertou" in lowered:
        return COLOR_SUCCESS
    if "incorreta" in lowered or "perdeu" in lowered:
        return COLOR_DANGER
    return COLOR_TEXT_SOFT


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

    image_area = (84, 124, 538, 570)
    cv2.rectangle(canvas, (image_area[0], image_area[1]), (image_area[2], image_area[3]), (244, 236, 220), -1)
    cv2.rectangle(canvas, (image_area[0], image_area[1]), (image_area[2], image_area[3]), COLOR_ACCENT, 2)
    draw_text(canvas, "IMAGEM DO DESAFIO", (106, 104), 0.56, COLOR_TEXT, 2)

    if image is not None:
        fitted = fit_image(image, image_area[2] - image_area[0] - 20, image_area[3] - image_area[1] - 20)
        image_y = image_area[1] + ((image_area[3] - image_area[1]) - fitted.shape[0]) // 2
        image_x = image_area[0] + ((image_area[2] - image_area[0]) - fitted.shape[1]) // 2
        canvas[image_y : image_y + fitted.shape[0], image_x : image_x + fitted.shape[1]] = fitted
    else:
        draw_panel(canvas, (180, 282), (444, 410), COLOR_WOOD_LIGHT, COLOR_BORDER_SOFT, 2)
        draw_text(canvas, "Aguardando imagem", (214, 338), 0.78, COLOR_TEXT, 2)
        draw_text(canvas, "Imagem do desafio", (238, 376), 0.5, COLOR_TEXT_SOFT, 1)

    draw_text(canvas, "QUIZ VISUAL DE LIBRAS", (672, 102), 1.02, COLOR_TEXT, 3)
    draw_text(canvas, "Veja a sequencia e digite a palavra formada.", (672, 142), 0.58, COLOR_TEXT_SOFT, 2)

    draw_stat_card(canvas, (666, 170), (114, 74), "Rodada", f"{round_number}/{total_rounds}", COLOR_WARNING)
    draw_stat_card(canvas, (792, 170), (114, 74), "Pontos", str(score), COLOR_SUCCESS)
    draw_stat_card(canvas, (918, 170), (114, 74), "Vidas", f"{lives}/{MAX_LIVES}", COLOR_DANGER)
    draw_stat_card(canvas, (1044, 170), (152, 74), "Dificuldade", challenge.get("difficulty", "nao informada"), COLOR_TEXT)

    draw_panel(canvas, (666, 262), (1196, 312), COLOR_WOOD_LIGHT, COLOR_BORDER_SOFT, 2)
    draw_text(canvas, f"Fonte {source_label}", (688, 293), 0.46, COLOR_MUTED, 1)
    draw_text(canvas, f"Palavra com {len(challenge['word'])} letras", (932, 293), 0.48, COLOR_WARNING, 1)

    instruction_text = (
        f"Mostrando imagem {sequence_index + 1} de {len(challenge['word'])}"
        if stage == "preview"
        else "Digite a palavra formada pela sequencia."
    )
    draw_panel(canvas, (666, 334), (1196, 386), COLOR_PANEL_BLUE, COLOR_BORDER_SOFT, 2)
    draw_text(canvas, instruction_text, (688, 367), 0.58, COLOR_TEXT, 2)

    draw_panel(canvas, (666, 406), (1196, 504), COLOR_WOOD_LIGHT, COLOR_BORDER_SOFT, 3)
    draw_text(canvas, "SUA RESPOSTA", (688, 438), 0.58, COLOR_TEXT, 2)
    response_value = typed_answer if typed_answer else "_"
    response_color = COLOR_WARNING if typed_answer else COLOR_TEXT
    draw_text(canvas, response_value, (688, 482), 1.32, response_color, 3)

    draw_panel(canvas, (666, 524), (1196, 592), COLOR_STATUS_BG, COLOR_SUCCESS, 3)
    draw_text(canvas, "STATUS", (688, 552), 0.52, COLOR_TEXT, 2)
    draw_text(canvas, feedback, (688, 582), 0.56, get_feedback_color(stage, feedback), 2)

    cv2.rectangle(canvas, (650, 614), (1210, 656), COLOR_CONTROLS, -1)
    cv2.rectangle(canvas, (650, 614), (1210, 656), COLOR_BORDER_SOFT, 3)
    draw_text(
        canvas,
        "[ENTER] Confirmar   [BACKSPACE] Apagar   [1] Repetir   [2] Proxima   [0] Sair",
        (668, 641),
        0.4,
        COLOR_TEXT,
        1,
    )

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
