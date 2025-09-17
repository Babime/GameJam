# country_house_scene.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, Callable
import pygame
import pytmx

# --- (optionnel) rendu TMX via pytmx ---
try:
    from pytmx.util_pygame import load_pygame as _tmx_load_pygame
    _PYTMX_OK = True
except Exception:
    _PYTMX_OK = False

# ----------------- Paramètres visuels -----------------
HUD_PAD = 10
FADE_MS = 900
CAR_SPEED = 240              # px/s pour les déplacements "voiture"
FOOTSTEP_SPEED = 120         # px/s pour les déplacements "à pied" (si besoin)
SCENE_PAUSE_MS = 800

# Points-clefs (écran) — ajuste si besoin pour ton .tmx
# On part du principe que le .tmx est rendu plein écran.
DRIVE_IN_START = ( -200, 520)   # hors-écran gauche
DRIVE_IN_STOP  = (  420, 520)   # allée devant la maison
PORCH_POS      = (  600, 460)   # porche / porte d'entrée (repère pour Martha)
BACK_CELLAR    = (  940, 560)   # arrière maison (entrée cave)
DRIVE_OUT_END  = ( 1400, 520)   # hors-écran droite

# ----------------- Outils -----------------
def _ease_in_out(t: float) -> float:
    # lissage simple 0..1
    import math
    return 0.5 - 0.5 * math.cos(min(max(t, 0.0), 1.0) * math.pi)

def _text(surface, font, msg, pos, color=(235,235,235)):
    surf = font.render(msg, True, color)
    surface.blit(surf, pos)

def _blit_tile(surface, img, x, y, tile_h, tileset_off):
    tox, toy = tileset_off
    y += (tile_h - img.get_height())  # aligne sur le bas de la cellule
    surface.blit(img, (x + tox, y + toy))

def _render_tmx_raw(tmx) -> pygame.Surface:
    tw, th = tmx.tilewidth, tmx.tileheight
    map_w = tmx.width * tw
    map_h = tmx.height * th
    raw = pygame.Surface((map_w, map_h), pygame.SRCALPHA)

    for layer in tmx.layers:
        if not layer.visible:
            continue
        ox = getattr(layer, "offsetx", 0) or 0
        oy = getattr(layer, "offsety", 0) or 0

        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if not gid:
                    continue
                img = tmx.get_tile_image_by_gid(gid)
                if not img:
                    continue
                ts = tmx.get_tileset_from_gid(gid)
                tileset_off = getattr(ts, "tileoffset", (0, 0)) or (0, 0)
                wx = x * tw + ox
                wy = y * th + oy
                _blit_tile(raw, img, wx, wy, th, tileset_off)

        elif isinstance(layer, pytmx.TiledImageLayer) and layer.image:
            raw.blit(layer.image, (ox, oy))

        elif isinstance(layer, pytmx.TiledObjectGroup):
            for obj in layer:
                if hasattr(obj, "gid") and obj.gid:
                    img = tmx.get_tile_image_by_gid(obj.gid)
                    if not img:
                        continue
                    ts = tmx.get_tileset_from_gid(obj.gid)
                    tileset_off = getattr(ts, "tileoffset", (0, 0)) or (0, 0)
                    # position bas-gauche en Tiled
                    x = int(obj.x + ox)
                    y = int(obj.y + oy)
                    _blit_tile(raw, img, x, y, th, tileset_off)
    return raw

# ======================================================
#                    CountryHouseScene
# ======================================================
class CountryHouseScene:
    """
    Interface compatible avec VaultRoomScene :
      - __init__(win_w, win_h, asset_dir_or_map, hud_font_path, game_vars)
      - layout_for_dialogue(dialog_top: int)
      - start_event(event_name: str, on_done: Callable[[str], None])
      - update(dt_ms: int)
      - draw(screen: pygame.Surface)
      - handle_event(pygame_event)
    Événements supportés (à appeler depuis le graphe):
      - 'arrive_house'       : voiture entre et s'arrête devant la maison
      - 'martha_greets'      : Martha sort, courte pause d’ambiance
      - 'rest_living_room'   : fondu maison -> repos canapé -> fin
      - 'rest_cellar'        : fondu maison -> repos cave -> fin
      - 'rest_car'           : fondu léger -> repos dans la voiture -> fin
      - 'depart'             : Tony repart avant l’arrivée d’Harold
    """
    def __init__(self, win_w: int, win_h: int, map_path_or_dir: Path,
                 hud_font_path: Optional[Path], game_vars):
        self.win_w, self.win_h = win_w, win_h
        self.gvars = game_vars

        # --- Police HUD
        pygame.font.init()
        self.hud_font = pygame.font.Font(str(hud_font_path), 18) if hud_font_path else pygame.font.SysFont(None, 18)

        # --- Chargement TMX (plein écran)
        self.map_surface = self._render_tmx_fullscreen(map_path_or_dir)

        # --- Entités "icônes"
        self.car = pygame.Rect(0, 0, 90, 42)
        self.car.center = DRIVE_IN_START
        self.martha = pygame.Rect(0, 0, 26, 38)  # simple silhouette
        self.martha.center = PORCH_POS
        self.martha_visible = False

        # --- État cinématique
        self._event_name: Optional[str] = None
        self._event_phase: str = ""
        self._on_done: Optional[Callable[[str], None]] = None
        self._timer_ms: int = 0
        self._from_xy = pygame.Vector2(self.car.center)
        self._to_xy   = pygame.Vector2(self.car.center)
        self._move_dur_ms = 0

        # --- Fades
        self._fade_ms = 0
        self._fade_dir = 0   # -1 out, +1 in, 0 none
        self._fade_alpha = 0

        # --- Layout dialogue
        self.safe_bottom = self.win_h  # zone de jeu sous la boîte de dialogue

    # ---------- TMX ----------
    def _render_tmx_fullscreen(self, map_path_or_dir: Path) -> pygame.Surface:
        W, H = self.win_w, self.win_h

        tmx_path = Path(map_path_or_dir)
        if tmx_path.is_dir():
            found = list(tmx_path.glob("*.tmx"))
            if found:
                tmx_path = found[0]

        if _PYTMX_OK and tmx_path.suffix.lower() == ".tmx" and tmx_path.exists():
            import pytmx
            tmx = _tmx_load_pygame(str(tmx_path))
            raw = _render_tmx_raw(tmx)  # ✅ rendu “fidèle Tiled”
            rw, rh = raw.get_size()
            scale = min(W / rw, H / rh)
            new = pygame.transform.smoothscale(raw, (int(rw * scale), int(rh * scale)))
            surf = pygame.Surface((W, H))
            surf.fill((0, 0, 0))
            surf.blit(new, ((W - new.get_width()) // 2, (H - new.get_height()) // 2))
            return surf

        # Fallback minimal si pas de TMX
        surf = pygame.Surface((W, H))
        surf.fill((22, 24, 28))
        pygame.draw.rect(surf, (72, 88, 96), (520, 340, 280, 180))
        pygame.draw.rect(surf, (180, 190, 210), (635, 360, 50, 50))
        pygame.draw.rect(surf, (150, 120, 90), (675, 440, 60, 80))
        return surf


    # ---------- API moteur ----------
    def layout_for_dialogue(self, dialog_top: int):
        margin = 8
        self.safe_bottom = max(0, dialog_top - margin)
        # on garde la voiture en bas de la zone visible
        cx, _ = self.car.center
        self.car.center = (cx, min(self.safe_bottom - self.car.h // 2, DRIVE_IN_STOP[1]))

    def start_event(self, event_name: str, on_done: Callable[[str], None]):
        self._event_name = event_name
        self._on_done = on_done
        self._event_phase = "init"
        self._timer_ms = 0

        if event_name == "arrive_house":
            # voiture roule jusqu'à l'allée
            self._set_move(self.car, DRIVE_IN_START, DRIVE_IN_STOP,
                           pixels_per_sec=CAR_SPEED)

        elif event_name == "martha_greets":
            # Martha apparaît sur le porche, bruit de pas (à intégrer côté sfx)
            self.martha_visible = True
            self._timer_ms = SCENE_PAUSE_MS

        elif event_name == "rest_living_room":
            # fondu, "repos canapé", fondu retour
            self._begin_fade_out(FADE_MS)

        elif event_name == "rest_cellar":
            self._begin_fade_out(FADE_MS)

        elif event_name == "rest_car":
            self._begin_fade_out(int(FADE_MS * 0.6))

        elif event_name == "depart":
            # Tony repart avant Harold : la voiture quitte vers la droite
            self._set_move(self.car, self.car.center, DRIVE_OUT_END,
                           pixels_per_sec=CAR_SPEED)

        else:
            # événement inconnu : terminer tout de suite pour ne pas bloquer
            self._finish_event()
            return

        self._event_phase = "run"

    def handle_event(self, ev):
        # Pas d'input joueur dans cette scène (cinématique pure)
        pass

    # ---------- Update ----------
    def update(self, dt_ms: int):
        # Fades
        if self._fade_dir != 0 and self._fade_ms > 0:
            step = (255 / max(self._fade_ms, 1)) * dt_ms
            self._fade_alpha = int(max(0, min(255, self._fade_alpha + step * self._fade_dir)))
            self._fade_ms -= dt_ms
            if self._fade_ms <= 0:
                # Transition de phase (out -> "repos" -> in)
                if self._event_name in ("rest_living_room", "rest_cellar", "rest_car"):
                    if self._fade_dir > 0:
                        # fini de fondre au noir => simuler repos court, puis fondre au clair
                        self._timer_ms = 1200
                        self._fade_dir = 0
                    elif self._fade_dir < 0:
                        # fini de revenir au clair
                        self._fade_dir = 0
                        self._finish_event()

        # Temporisations
        if self._timer_ms > 0:
            self._timer_ms -= dt_ms
            if self._timer_ms <= 0:
                if self._event_name == "martha_greets":
                    self._finish_event()
                elif self._event_name in ("rest_living_room", "rest_cellar", "rest_car"):
                    # après le "repos", fade-in
                    self._begin_fade_in(FADE_MS)

        # Déplacements
        if self._event_name in ("arrive_house", "depart") and self._event_phase == "run":
            t = 1.0 - max(self._move_dur_ms, 0) / max(self._move_total_ms, 1)
            t_eased = _ease_in_out(t)
            cur = self._from_xy.lerp(self._to_xy, t_eased)
            self.car.center = (int(cur.x), int(cur.y))
            self._move_dur_ms -= dt_ms
            if self._move_dur_ms <= 0:
                # clamp fin
                self.car.center = (int(self._to_xy.x), int(self._to_xy.y))
                self._finish_event()

        # Sécurité : si la boîte de dialogue remonte, on évite le chevauchement visuel
        if self.car.bottom > self.safe_bottom:
            self.car.bottom = self.safe_bottom

    # ---------- Draw ----------
    def draw(self, screen: pygame.Surface):
        # fond (tmx rendu en “plein écran”)
        screen.blit(self.map_surface, (0, 0))

        # silhouettes simples (placeholders lisibles)
        # voiture
        pygame.draw.rect(screen, (30, 150, 200), self.car, border_radius=8)
        # jantes
        pygame.draw.circle(screen, (10, 40, 60), (self.car.left + 14, self.car.bottom - 6), 6)
        pygame.draw.circle(screen, (10, 40, 60), (self.car.right - 14, self.car.bottom - 6), 6)

        # Martha (si visible)
        if self.martha_visible:
            pygame.draw.rect(screen, (220, 210, 190), self.martha, border_radius=6)
            # petite tête
            pygame.draw.circle(screen, (230, 220, 200), (self.martha.centerx, self.martha.top - 6), 8)

        # HUD (trust, police_gap, fatigue si dispo)
        trust = getattr(self.gvars, "trust", "?")
        pgap  = getattr(self.gvars, "police_gap", "?")
        fatigue = getattr(self.gvars, "fatigue", None)
        hud_msg = f"Trust: {trust}   PoliceGap: {pgap}"
        if fatigue is not None:
            hud_msg += f"   Fatigue: {fatigue}"
        _text(screen, self.hud_font, hud_msg, (HUD_PAD, HUD_PAD))

        # Fades
        if self._fade_dir != 0 or (self._event_name in ("rest_living_room", "rest_cellar", "rest_car") and self._timer_ms > 0):
            overlay = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
            # teinte différente selon lieu de repos (très léger)
            tint = (0, 0, 0)
            if self._event_name == "rest_cellar":
                tint = (5, 5, 12)
            elif self._event_name == "rest_living_room":
                tint = (12, 8, 4)
            elif self._event_name == "rest_car":
                tint = (0, 0, 0)
            alpha = self._fade_alpha if self._fade_dir != 0 else 200  # pendant “repos”
            overlay.fill((*tint, max(0, min(255, int(alpha)))))
            screen.blit(overlay, (0, 0))

    # ---------- Helpers cinématiques ----------
    def _set_move(self, rect: pygame.Rect, start_xy, end_xy, pixels_per_sec=200):
        self._from_xy = pygame.Vector2(start_xy)
        self._to_xy   = pygame.Vector2(end_xy)
        dist = self._to_xy.distance_to(self._from_xy)
        dur = max(1, int((dist / max(1.0, float(pixels_per_sec))) * 1000))
        self._move_total_ms = dur
        self._move_dur_ms = dur
        rect.center = start_xy

    def _begin_fade_out(self, ms: int):
        self._fade_dir = +1
        self._fade_ms = ms
        self._fade_alpha = 0

    def _begin_fade_in(self, ms: int):
        self._fade_dir = -1
        self._fade_ms = ms
        self._fade_alpha = 255

    def _finish_event(self):
        name = self._event_name or ""
        self._event_name = None
        self._event_phase = ""
        self._timer_ms = 0
        self._fade_dir = 0
        self._fade_ms = 0
        self._fade_alpha = 0
        if self._on_done:
            cb = self._on_done
            self._on_done = None
            cb(name)
