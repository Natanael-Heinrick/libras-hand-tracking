from __future__ import annotations

import json
from pathlib import Path


STORE_DIR = Path(__file__).resolve().parent
LOOKS_DIR = STORE_DIR / "assets" / "looks"
STATE_PATH = STORE_DIR / "dados" / "game_state.json"
CATALOG_PATH = STORE_DIR / "dados" / "shop_items.json"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def _read_json(path: Path, default):
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _default_state() -> dict:
    return {
        "points": 0,
        "infinite_points": False,
        "owned_items": [],
        "equipped_item": "",
    }


def load_state() -> dict:
    state = _read_json(STATE_PATH, _default_state())
    default = _default_state()
    default.update(state)
    return default


def save_state(state: dict):
    normalized = _default_state()
    normalized.update(state or {})
    normalized["points"] = max(0, int(normalized.get("points", 0)))
    normalized["owned_items"] = list(dict.fromkeys(normalized.get("owned_items", [])))
    normalized["equipped_item"] = normalized.get("equipped_item", "")
    _write_json(STATE_PATH, normalized)


def get_points() -> int:
    state = load_state()
    if state.get("infinite_points"):
        return 999999
    return int(state.get("points", 0))


def get_points_label() -> str:
    state = load_state()
    if state.get("infinite_points"):
        return "INF"
    return str(int(state.get("points", 0)))


def add_points(delta: int) -> int:
    state = load_state()
    if state.get("infinite_points"):
        return 999999
    state["points"] = max(0, int(state.get("points", 0)) + int(delta))
    save_state(state)
    return state["points"]


def spend_points(cost: int) -> tuple[bool, int]:
    state = load_state()
    if state.get("infinite_points"):
        return True, 999999

    current_points = int(state.get("points", 0))
    if current_points < int(cost):
        return False, current_points

    state["points"] = current_points - int(cost)
    save_state(state)
    return True, state["points"]


def _build_item_from_asset(asset_path: Path) -> dict:
    item_id = asset_path.stem.lower()
    tokens = [token for token in asset_path.stem.split("_") if token]
    name_map = {
        "rato": "Rato",
        "base": "Base",
        "loiro": "Loiro",
        "laranja": "Laranja",
        "lingua": "Lingua",
    }
    display_name = " ".join(name_map.get(token.lower(), token.title()) for token in tokens) or asset_path.stem.title()
    return {
        "id": item_id,
        "name": display_name,
        "price": max(10, len(item_id) * 5),
        "file": asset_path.name,
        "description": "Look desbloqueavel da loja.",
    }


def sync_shop_catalog() -> list[dict]:
    existing_items = {
        item["id"]: item
        for item in _read_json(CATALOG_PATH, [])
        if isinstance(item, dict) and item.get("id")
    }

    catalog = []
    if LOOKS_DIR.exists():
        for asset_path in sorted(LOOKS_DIR.iterdir()):
            if not asset_path.is_file() or asset_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            generated = _build_item_from_asset(asset_path)
            existing = existing_items.get(generated["id"], {})
            merged = generated | {
                "price": int(existing.get("price", generated["price"])),
                "name": existing.get("name", generated["name"]),
                "description": existing.get("description", generated["description"]),
            }
            catalog.append(merged)

    _write_json(CATALOG_PATH, catalog)
    return catalog


def load_shop_items() -> list[dict]:
    if not CATALOG_PATH.exists():
        return sync_shop_catalog()

    catalog = _read_json(CATALOG_PATH, [])
    if not catalog and LOOKS_DIR.exists():
        return sync_shop_catalog()
    return catalog
