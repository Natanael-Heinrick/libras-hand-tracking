from __future__ import annotations

import base64
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
HAND_IMAGE_DIR = PROJECT_ROOT / "image"


def get_floating_hands_css() -> str:
    return """
        .floating-hands {
            position: fixed;
            inset: 0;
            overflow: hidden;
            pointer-events: none;
            z-index: 0;
        }
        .floating-hands img {
            position: absolute;
            width: var(--size);
            opacity: .72;
            filter: drop-shadow(0 12px 18px rgba(29, 45, 68, .16));
            animation: floatHand var(--duration) ease-in-out infinite alternate;
            animation-delay: var(--delay);
        }
        .floating-hands img:nth-child(1) { left: 3%; top: 9%; --size: 86px; --duration: 8s; --delay: -.5s; transform: rotate(-12deg); }
        .floating-hands img:nth-child(2) { right: 7%; top: 7%; --size: 78px; --duration: 9s; --delay: -2s; transform: rotate(10deg); }
        .floating-hands img:nth-child(3) { left: 7%; bottom: 8%; --size: 96px; --duration: 10s; --delay: -1s; transform: rotate(14deg); }
        .floating-hands img:nth-child(4) { right: 4%; bottom: 12%; --size: 104px; --duration: 11s; --delay: -3s; transform: rotate(-8deg); }
        .floating-hands img:nth-child(5) { left: 45%; top: 3%; --size: 70px; --duration: 9.5s; --delay: -1.8s; transform: rotate(8deg); }
        .floating-hands img:nth-child(6) { right: 32%; bottom: 4%; --size: 82px; --duration: 10.5s; --delay: -2.5s; transform: rotate(-14deg); }
        @keyframes floatHand {
            from { translate: 0 0; }
            to { translate: 0 -18px; }
        }
        @media (max-width: 760px) {
            .floating-hands img { opacity: .38; }
            .floating-hands img:nth-child(5),
            .floating-hands img:nth-child(6) { display: none; }
        }
    """


def get_floating_hands_markup() -> str:
    images = sorted(HAND_IMAGE_DIR.glob("hand_float_*.png"))
    if not images:
        return ""

    tags = []
    for image_path in images[:6]:
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        tags.append(
            f'<img src="data:image/png;base64,{encoded}" alt="" aria-hidden="true">'
        )
    return '<div class="floating-hands" aria-hidden="true">' + "".join(tags) + "</div>"
