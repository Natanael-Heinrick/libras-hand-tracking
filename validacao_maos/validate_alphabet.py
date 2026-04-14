"""
Script interativo para validação manual do alfabeto LIBRAS.

Permite validar letra por letra, visualizar dados coletados,
e registrar o status de validação.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FOTOS_DIR = ROOT_DIR / "fotos_maos"
LANDMARKS_DIR = ROOT_DIR / "landmarks_json"
VALIDATION_REPORT = ROOT_DIR / "validation_status.json"

# Letras do alfabeto LIBRAS disponíveis (baseado em seus dados)
ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'I', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V']


def load_validation_status() -> dict:
    """Carrega status anterior de validação, se existir."""
    if VALIDATION_REPORT.exists():
        return json.loads(VALIDATION_REPORT.read_text(encoding="utf-8"))
    return {letter: {"status": "pendente", "timestamp": None} for letter in ALPHABET}


def save_validation_status(status: dict) -> None:
    """Salva status de validação em arquivo."""
    VALIDATION_REPORT.write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def count_photos_by_letter(letter: str) -> dict:
    """Conta fotos disponíveis para uma letra."""
    pattern = f"{letter}_*.jpg"
    pattern_jpg = list(FOTOS_DIR.glob(f"{letter}_*.jpg"))
    pattern_jpeg = list(FOTOS_DIR.glob(f"{letter}_*.jpeg"))
    pattern_jpeg2 = list(FOTOS_DIR.glob(f"{letter}_*.JPEG"))
    pattern_jpg2 = list(FOTOS_DIR.glob(f"{letter}_*.JPG"))
    
    all_photos = pattern_jpg + pattern_jpeg + pattern_jpeg2 + pattern_jpg2
    
    # Agrupar por participante e sessão
    stats = defaultdict(lambda: {"total": 0, "s01": 0, "s02": 0})
    for photo in all_photos:
        # Formato: A_p01_s01_001.jpg
        parts = photo.stem.split('_')
        if len(parts) >= 3:
            participant = parts[1]  # p01, p02, etc
            session = parts[2]      # s01, s02
            stats[participant]["total"] += 1
            if session == "s01":
                stats[participant]["s01"] += 1
            elif session == "s02":
                stats[participant]["s02"] += 1
    
    return dict(stats)


def count_landmarks_by_letter(letter: str) -> dict:
    """Conta landmarks disponíveis para uma letra."""
    landmark_path = LANDMARKS_DIR / "test" / letter
    if not landmark_path.exists():
        return {"total": 0, "variações": []}
    
    json_files = list(landmark_path.glob("*.json"))
    variations = [f.stem for f in json_files]
    
    return {
        "total": len(json_files),
        "variações": variations[:5] + (["..."] if len(variations) > 5 else [])
    }


def get_landmark_quality_report(letter: str) -> dict:
    """Obtém relatório de qualidade dos landmarks (usa audit_landmarks.py)."""
    try:
        import audit_landmarks
        payloads = audit_landmarks.load_payloads()
        summary = audit_landmarks.summarize(payloads)
        
        if letter in summary["por_classe"]:
            return summary["por_classe"][letter]
    except Exception as e:
        print(f"[!] Erro ao obter relatório de qualidade: {e}")
    
    return {"total": 0, "sem_mao": 0, "multimao": 0}


def open_photos(letter: str) -> None:
    """Abre as fotos da letra no explorador/visualizador padrão."""
    photos = list(FOTOS_DIR.glob(f"{letter}_*.*"))
    
    if not photos:
        print(f"[!] Nenhuma foto encontrada para a letra '{letter}'")
        return
    
    print(f"\n[*] Abrindo {len(photos)} foto(s) da letra '{letter}'...")
    
    # Tentar abrir com o visualizador padrão (funciona em Windows, macOS, Linux)
    for photo in photos[:3]:  # Abrir apenas as 3 primeiras para não sobrecarregar
        try:
            if sys.platform == 'win32':
                subprocess.Popen(['start', str(photo)], shell=True)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(photo)])
            else:  # Linux
                subprocess.Popen(['xdg-open', str(photo)])
        except Exception as e:
            print(f"[!] Erro ao abrir foto {photo.name}: {e}")
    
    if len(photos) > 3:
        print(f"[*] ... e mais {len(photos) - 3} foto(s)")


def display_letter_info(letter: str) -> None:
    """Exibe informações detalhadas sobre uma letra."""
    print(f"\n{'='*70}")
    print(f"  LETRA: {letter}")
    print(f"{'='*70}")
    
    # Fotos
    photo_stats = count_photos_by_letter(letter)
    total_photos = sum(s["total"] for s in photo_stats.values())
    print(f"\n[FOTOS] Total: {total_photos}")
    for participant, stats in sorted(photo_stats.items()):
        print(f"  {participant}: {stats['total']} foto(s) (mão direita: {stats['s01']}, mão esquerda: {stats['s02']})")
    
    # Landmarks
    landmark_stats = count_landmarks_by_letter(letter)
    print(f"\n[LANDMARKS] Total: {landmark_stats['total']}")
    if landmark_stats['variações']:
        print(f"  Variações: {', '.join(landmark_stats['variações'])}")
    
    # Qualidade
    quality = get_landmark_quality_report(letter)
    if quality.get("total", 0) > 0:
        print(f"\n[QUALIDADE DOS LANDMARKS]")
        print(f"  Total de detecções: {quality['total']}")
        print(f"  Sem mão detectada: {quality.get('sem_mao', 0)}")
        print(f"  Múltiplas mãos: {quality.get('multimao', 0)}")
        
        if quality.get('sem_mao', 0) > 0 or quality.get('multimao', 0) > 0:
            print(f"  ⚠️  ATENÇÃO: Problemas detectados!")


def validate_letter(letter: str, status: dict) -> bool:
    """Interface interativa para validar uma letra."""
    display_letter_info(letter)
    
    print(f"\n[VALIDAÇÃO]")
    print(f"Status anterior: {status[letter]['status']}")
    print(f"Abrir fotos? [s/n]:  ", end="")
    
    if input().strip().lower() == 's':
        open_photos(letter)
    
    while True:
        print(f"\nValidar a letra '{letter}' como OK? [s/n/revisar]:  ", end="")
        choice = input().strip().lower()
        
        if choice == 's':
            status[letter]["status"] = "validado"
            print(f"✓ Letra '{letter}' marcada como VALIDADO")
            return True
        elif choice == 'n':
            status[letter]["status"] = "rejeitado"
            print(f"✗ Letra '{letter}' marcada como REJEITADO")
            print(f"Motivo de rejeição (opcional):  ", end="")
            motivo = input().strip()
            if motivo:
                status[letter]["motivo"] = motivo
            return False
        elif choice == 'revisar':
            print(f"Execute: python validacao_maos/generate_landmarks.py")
            print(f"para regenerar landmarks, ou")
            print(f"colete mais fotos em: {FOTOS_DIR}")
            return None
        else:
            print("Opção inválida. Digite 's' (sim), 'n' (não) ou 'revisar'")


def show_summary(status: dict) -> None:
    """Exibe resumo do progresso."""
    validados = sum(1 for s in status.values() if s["status"] == "validado")
    rejeitados = sum(1 for s in status.values() if s["status"] == "rejeitado")
    pendentes = sum(1 for s in status.values() if s["status"] == "pendente")
    
    print(f"\n{'='*70}")
    print(f"  RESUMO DO PROGRESSO")
    print(f"{'='*70}")
    print(f"✓ Validados:  {validados}/{len(status)}")
    print(f"✗ Rejeitados: {rejeitados}/{len(status)}")
    print(f"⏳ Pendentes:  {pendentes}/{len(status)}")
    print(f"{'='*70}\n")


def main():
    """Função principal - loop de validação."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║   VALIDAÇÃO MANUAL DO ALFABETO LIBRAS                            ║
║   Valide letra por letra até completar o alfabeto               ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    status = load_validation_status()
    
    # Encontrar primeira letra pendente
    start_idx = 0
    for i, letter in enumerate(ALPHABET):
        if status[letter]["status"] == "pendente":
            start_idx = i
            break
    
    for i, letter in enumerate(ALPHABET[start_idx:], start=start_idx):
        print(f"\n[{i+1}/{len(ALPHABET)}] Validando letra '{letter}'...")
        
        result = validate_letter(letter, status)
        save_validation_status(status)
        
        if result is not None:
            show_summary(status)
            
            print(f"Continuar para próxima letra? [s/n]:  ", end="")
            if input().strip().lower() != 's':
                print("Validação pausada. Progresso salvo.")
                break
        else:
            print("\nRevisar dados antes de continuar.")
            break
    
    print("\n✓ Validação concluída!")
    show_summary(status)


if __name__ == "__main__":
    main()
