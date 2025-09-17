# src/audio/bgm.py
from __future__ import annotations
from pathlib import Path
import pygame

# adapte si ton dossier audio est ailleurs
try:
    from core.config import ASSETS_DIR
    AUDIO_DIR = Path(ASSETS_DIR) / "audio"
except Exception:
    AUDIO_DIR = Path("assets/audio")

def _resolve_audio(name: str) -> str:
    """Accepte 'theme', 'theme.ogg', 'theme.mp3' ou un chemin relatif/absolu."""
    p = Path(name)
    if p.suffix:                        # 'scene3.mp3' ou 'music/loop.ogg'
        full = p if p.is_absolute() else (AUDIO_DIR / p)
    else:                               # pas d’extension -> on tente .ogg puis .mp3
        ogg = AUDIO_DIR / f"{name}.ogg"
        mp3 = AUDIO_DIR / f"{name}.mp3"
        full = ogg if ogg.exists() else mp3
    return str(full)

def play_bgm(name: str, volume: float = 0.7, fade_ms: int = 300) -> None:
    """
    Joue une musique en BOUCLE (-1) et remplace l’actuelle s’il y en a une.
    - name: 'scene3' ou 'scene3.mp3' (cherché dans assets/audio/)
    - volume: 0.0..1.0
    - fade_ms: fondu d’entrée (ms)
    """
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    path = _resolve_audio(name)
    pygame.mixer.music.stop()
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(max(0.0, min(1.0, float(volume))))
    pygame.mixer.music.play(loops=-1, fade_ms=max(0, int(fade_ms)))
