from __future__ import annotations

import re
import unicodedata


INES_VIDEO_BASE_URL = "https://dicionario.ines.gov.br/public/media/palavras/videos"
GLOSS_STOPWORDS = {
    "a",
    "as",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "e",
    "o",
    "os",
}
GLOSS_SUBJECT_PRONOUNS = {
    "ela",
    "ele",
    "eu",
    "nos",
    "nós",
    "tu",
    "voce",
    "voces",
}
GLOSS_LEMMA_MAP = {
    "ajudo": "ajudar",
    "estou": "estar",
    "faco": "fazer",
    "gosto": "gostar",
    "precisa": "precisar",
    "precisam": "precisar",
    "precisamos": "precisar",
    "preciso": "precisar",
    "quero": "querer",
    "quer": "querer",
    "queremos": "querer",
    "sei": "saber",
    "tenho": "ter",
    "vai": "ir",
    "vamos": "ir",
    "vou": "ir",
}


class InesDictionaryService:
    """Normaliza texto e gera candidatos de video do dicionario do INES."""

    def analyze_text(self, text: str) -> dict:
        original_text = (text or "").strip()
        normalized_text = self._normalize_text(original_text)
        gloss_text = self._build_gloss_text(normalized_text)
        words = [word for word in gloss_text.split() if word]

        phrase_term = "_".join(words)
        candidate_terms = []

        if phrase_term:
            candidate_terms.append(phrase_term)

        for word in words:
            if word not in candidate_terms:
                candidate_terms.append(word)

        candidates = [
            {
                "termo": term,
                "video_url": self._build_video_url(term),
                "variantes_video": self._build_video_variants(term),
            }
            for term in candidate_terms
        ]

        return {
            "rota": "/dicionario-ines/normalizar",
            "fonte": "dicionario-ines",
            "texto_original": original_text,
            "texto_normalizado": normalized_text,
            "texto_gloss_base": gloss_text,
            "palavras_normalizadas": words,
            "termo_principal": candidate_terms[0] if candidate_terms else "",
            "video_url_principal": candidates[0]["video_url"] if candidates else None,
            "candidatos": candidates,
            "observacao": (
                "Bloco 2: esta resposta normaliza o texto e monta URLs candidatas "
                "seguindo o padrao observado no INES."
            ),
        }

    def segment_text(self, text: str, max_group_size: int = 4) -> dict:
        original_text = (text or "").strip()
        normalized_text = self._normalize_text(original_text)
        gloss_text = self._build_gloss_text(normalized_text)
        words = [word for word in gloss_text.split() if word]
        groups = []

        for start_index in range(len(words)):
            candidates = []
            max_size = min(max_group_size, len(words) - start_index)
            for size in range(max_size, 0, -1):
                chunk_words = words[start_index : start_index + size]
                term = "_".join(chunk_words)
                candidates.append(
                    {
                        "termo": term,
                        "palavras": chunk_words,
                        "inicio": start_index,
                        "fim": start_index + size - 1,
                        "tamanho_grupo": size,
                        "video_url": self._build_video_url(term),
                        "variantes_video": self._build_video_variants(term),
                    }
                )

            groups.append(
                {
                    "indice_inicial": start_index,
                    "palavra_inicial": words[start_index],
                    "candidatos": candidates,
                }
            )

        return {
            "rota": "/dicionario-ines/segmentar",
            "fonte": "dicionario-ines",
            "texto_original": original_text,
            "texto_normalizado": normalized_text,
            "texto_gloss_base": gloss_text,
            "palavras_normalizadas": words,
            "grupos_segmentacao": groups,
            "observacao": (
                "Bloco 3: cada posicao da frase recebe candidatos do maior bloco "
                "possivel ate palavras isoladas."
            ),
        }

    def _normalize_text(self, text: str) -> str:
        collapsed = re.sub(r"\s+", " ", text.strip().lower())
        without_accents = self._remove_accents(collapsed)
        alphanumeric = re.sub(r"[^a-z0-9\s-]", "", without_accents)
        normalized_spaces = re.sub(r"[-_]+", " ", alphanumeric)
        return re.sub(r"\s+", " ", normalized_spaces).strip()

    def _remove_accents(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        return "".join(char for char in normalized if unicodedata.category(char) != "Mn")

    def _build_video_url(self, term: str) -> str:
        return f"{INES_VIDEO_BASE_URL}/{term}Sm_Prog001.mp4"

    def _build_video_variants(self, term: str) -> list[dict]:
        variants = []
        variant_terms = []

        def add_variant_term(value: str):
            if value and value not in variant_terms:
                variant_terms.append(value)

        add_variant_term(term)

        if "_" not in term:
            if term.endswith("r"):
                add_variant_term(f"{term}1")
            else:
                add_variant_term(f"{term}r1")

        for variant_term in variant_terms:
            variants.append(
                {
                    "termo": variant_term,
                    "video_url": self._build_video_url(variant_term),
                }
            )

        return variants

    def _build_gloss_text(self, normalized_text: str) -> str:
        gloss_words = []
        words = normalized_text.split()
        for index, word in enumerate(words):
            if word in GLOSS_STOPWORDS:
                continue

            gloss_words.append(self._resolve_gloss_word(word, words, index))

        return " ".join(gloss_words).strip()

    def _resolve_gloss_word(self, word: str, words: list[str], index: int) -> str:
        if word == "como":
            if len(words) == 1:
                return "como"

            previous_word = words[index - 1] if index > 0 else ""
            if previous_word in GLOSS_SUBJECT_PRONOUNS:
                return "comer"

            return "como"

        return GLOSS_LEMMA_MAP.get(word, word)
