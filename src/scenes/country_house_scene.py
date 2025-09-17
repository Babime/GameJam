# src/scenes/country_house_scene.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, Callable
import pygame
from core.config import FONT_PATH
from core.actor_sprite import create_car_animator, create_grandma_animator, create_police_animator, create_tony_animator


# --- (optionnel) rendu TMX via pytmx ---
try:
    import pytmx
    from pytmx.util_pygame import load_pygame as _tmx_load_pygame
    _PYTMX_OK = True
except Exception:
    _PYTMX_OK = False
    pytmx = None  # type: ignore

# ---------- Imports projet : mêmes conventions que scène 1 ----------
from core.config import ASSETS_DIR, GENERAL_ASSET_DIR  # ASSETS_DIR pour la carte, GENERAL_ASSET_DIR pour les sprites
from core.actor_sprite import create_grandma_animator, create_police_animator

# ----------------- Paramètres visuels / gameplay -----------------
PLAYER_SIZE = 32          # hitbox logique (comme ta scène 1)
SPRITE_DRAW_H = 56        # hauteur visuelle des sprites (Tony-like)
FADE_MS = 900
CAR_SPEED = 240           # px/s
SCENE_PAUSE_MS = 800

# Points-clefs (écran) — ajuste si besoin selon ta carte .tmx
DRIVE_IN_START = (-200, 520)   # hors-écran gauche
DRIVE_IN_STOP  = ( 420, 520)   # allée devant la maison
PORCH_POS      = ( 600, 460)   # porche (Martha)
DRIVE_OUT_END  = (1400, 520)   # hors-écran droite

# --- Chorégraphie "arrivée par le haut -> maison gauche" ---
TOP_ENTRY          = (460, -120)   # arrive depuis le haut (x centré sur la route du haut)
LEFT_HOUSE_PARK    = (460, 500)    # place de parking devant la maison orange (à ajuster)
LEFT_HOUSE_DOOR    = (280, 470)    # devant la porte de la maison orange (à ajuster)
TONY_STAND_OFFSET  = (-28, 0)      # offset pour faire apparaître Tony à gauche de la voiture
TONY_STEP_TO_STAND = ( -8, 0)      # petit pas (esthétique) en sortant

# ----------------- Outils -----------------
def _ease_in_out(t: float) -> float:
    import math
    return 0.5 - 0.5 * math.cos(min(max(t, 0.0), 1.0) * math.pi)

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

def _facing_from_vec(vx: float, vy: float) -> str:
    if abs(vx) > abs(vy):
        return "right" if vx > 0 else "left"
    else:
        return "down" if vy > 0 else "up"

# ======================================================
#                    CountryHouseScene
# ======================================================
class CountryHouseScene:
    """
    Scène 2 (Maison de campagne) — même protocole que VaultRoomScene :
      - layout_for_dialogue(dialog_top)
      - start_event(event_name, on_done)
      - update(dt_ms)
      - draw(screen)
      - handle_event(ev)
    Aucune DialogueBox / DialogueRunner ici (gérés par le scene_runner).
    """
    def __init__(self, win_w: int, win_h: int, gvars):
        self.win_w, self.win_h = win_w, win_h
        self.gvars = gvars

        pygame.font.init()
        self.hud_font = (
            pygame.font.Font(str(FONT_PATH), 18)
            if FONT_PATH and Path(FONT_PATH).exists()
            else pygame.font.SysFont("monospace", 18)
        )
        self.hud_color = (230, 230, 230)
        self.hud_pos = (12, 8)

        # --- Chargement TMX (plein écran ou fallback)
        self.map_surface = self._render_tmx_fullscreen(ASSETS_DIR / "village" / "Village.tmx")

        # --- Entités (Rect collisions) : alignées sur scène 1 -> PLAYER_SIZE
        self.car = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.car.center = DRIVE_IN_START

        self.martha = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.martha.center = PORCH_POS
        self.martha_visible = False

        # --- Sprites animés (4-dir API identique à Tony)
        self.grandma_walker = create_grandma_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H - 2)  # un poil plus petite
        self._grandma_facing_dir = "down"
        self._grandma_moving = False

        # --- Animations voiture (civile et police)
        self.car_animator = create_car_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H)
        self.police_animator = create_police_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H)

        self._car_facing_dir = "up"
        self._car_moving = False

        # Flag pour choisir quel sprite afficher
        self._use_police_car = False


        # --- Tony (apparition à la sortie de voiture)
        self.tony_rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.tony_visible = False
        self.tony_walker = create_tony_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H)
        self._tony_facing_dir = "down"
        self._tony_moving = False
        self._tony_target: Optional[pygame.Vector2] = None
        self._tony_speed = 110.0  # petit pas en sortie

        # --- État cinématique
        self._event_name: Optional[str] = None
        self._event_phase: str = ""
        self._on_done: Optional[Callable[[str], None]] = None
        self._timer_ms: int = 0
        self._from_xy = pygame.Vector2(self.car.center)
        self._to_xy   = pygame.Vector2(self.car.center)
        self._move_dur_ms = 0
        self._move_total_ms = 1

        # --- Fades
        self._fade_ms = 0
        self._fade_dir = 0   # -1 out, +1 in, 0 none
        self._fade_alpha = 0

        # --- Layout dialogue
        self.safe_bottom = self.win_h  # zone de jeu sous la boîte de dialogue

    # ---------- TMX ----------
    def _render_tmx_fullscreen(self, tmx_path: Path) -> pygame.Surface:
        W, H = self.win_w, self.win_h

        if _PYTMX_OK and tmx_path.suffix.lower() == ".tmx" and tmx_path.exists():
            tmx = _tmx_load_pygame(str(tmx_path))
            raw = _render_tmx_raw(tmx)
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
        # garder la voiture en bas de la zone visible
        cx, _ = self.car.center
        self.car.center = (cx, min(self.safe_bottom - self.car.h // 2, DRIVE_IN_STOP[1]))

    def start_event(self, event_name: str, on_done: Callable[[str], None]):
        """
        Appelée par le scene_runner sur les noeuds wait_scene.
        On lance la mini-cinématique, puis on appelle on_done(event_name).
        """
        self._event_name = event_name
        self._on_done = on_done
        self._event_phase = "init"
        self._timer_ms = 0

        if event_name == "arrive_house":
            # voiture roule jusqu'à l'allée
            self._use_police_car = True
            self._set_move(self.car, TOP_ENTRY, LEFT_HOUSE_PARK, pixels_per_sec=CAR_SPEED)
            self._car_facing_dir = "right"
            self._car_moving = True
            self.police_animator.update(self._car_facing_dir, True, 0)
        
        elif event_name == "arrival_from_top":
            self._use_police_car = False
            self._set_move(self.car, TOP_ENTRY, LEFT_HOUSE_PARK, pixels_per_sec=CAR_SPEED)
            self._car_facing_dir = "up"
            self._car_moving = True
            self.car_animator.update(self._car_facing_dir, True, 0)

        elif event_name == "tony_exit_car":
            # Tony apparaît à côté de la voiture (à gauche par défaut), fait un petit pas et s'arrête
            self.tony_visible = True
            base = pygame.Vector2(self.car.center)
            off = pygame.Vector2(TONY_STAND_OFFSET)
            self.tony_rect.center = (int(base.x + off.x), int(base.y + off.y))
            # petit pas esthétique
            step_to = (self.tony_rect.centerx + TONY_STEP_TO_STAND[0],
                    self.tony_rect.centery + TONY_STEP_TO_STAND[1])
            self._start_tony_step_to(step_to)

        elif event_name == "martha_exit_house":
            # Mamie sort et se place devant la porte (on la téléporte ou on joue une courte marche)
            self.martha_visible = True
            self.martha.center = LEFT_HOUSE_DOOR
            self._grandma_facing_dir = "right"  # tournée vers Tony/voiture
            self.grandma_walker.update(self._grandma_facing_dir, False, 0)
            # petite pause pour laisser “respirer”
            self._timer_ms = 500

        elif event_name == "martha_greets":
            # Martha apparaît sur le porche, idle face caméra
            self.martha_visible = True
            self._grandma_facing_dir = "down"
            self._grandma_moving = False
            self.grandma_walker.update(self._grandma_facing_dir, False, 0)
            self._timer_ms = SCENE_PAUSE_MS

        elif event_name == "rest_living_room":
            self._begin_fade_out(FADE_MS)

        elif event_name == "rest_cellar":
            self._begin_fade_out(FADE_MS)

        elif event_name == "rest_car":
            self._begin_fade_out(int(FADE_MS * 0.6))

        elif event_name == "depart":
            self._use_police_car = True
            self._set_move(self.car, TOP_ENTRY, LEFT_HOUSE_PARK, pixels_per_sec=CAR_SPEED)
            self._car_facing_dir = "left"
            self._car_moving = True
            self.police_animator.update(self._car_facing_dir, True, 0)

        # --- Événements supplémentaires du graphe (scene3_country_house) ---
        elif event_name == "harold_arrives_chase":
            self._use_police_car = True
            self._set_move(self.car, TOP_ENTRY, LEFT_HOUSE_PARK, pixels_per_sec=CAR_SPEED)
            self._car_facing_dir = "left"
            self._car_moving = True
            self.police_animator.update(self._car_facing_dir, True, 0)

        elif event_name in ("hide_in_cellar_safe", "force_cellar_stay"):
            self._begin_fade_out(FADE_MS)

        elif event_name in ("tony_sleeps_car", "avoid_livingroom_sleep_car", "reject_cellar_sleep_car"):
            self._begin_fade_out(int(FADE_MS * 0.6))

        else:
            # inconnu -> finir immédiatement pour ne pas bloquer le graphe
            self._finish_event()
            return

        self._event_phase = "run"

    def handle_event(self, ev):
        # cinématique pure (pas d'input)
        pass

    # ---------- Update ----------
    def update(self, dt_ms: int):
        # Fades
        if self._fade_dir != 0 and self._fade_ms > 0:
            step = (255 / max(self._fade_ms, 1)) * dt_ms
            self._fade_alpha = int(max(0, min(255, self._fade_alpha + step * self._fade_dir)))
            self._fade_ms -= dt_ms
            if self._fade_ms <= 0:
                # (out -> repos -> in)
                if self._event_name in ("rest_living_room", "rest_cellar", "rest_car",
                                        "hide_in_cellar_safe", "force_cellar_stay",
                                        "tony_sleeps_car", "avoid_livingroom_sleep_car", "reject_cellar_sleep_car"):
                    if self._fade_dir > 0:
                        self._timer_ms = 1200
                        self._fade_dir = 0
                    elif self._fade_dir < 0:
                        self._fade_dir = 0
                        self._finish_event()

        # Temporisations
        if self._timer_ms > 0:
            self._timer_ms -= dt_ms
            if self._timer_ms <= 0:
                if self._event_name == "martha_greets":
                    self._finish_event()
                elif self._event_name in ("rest_living_room", "rest_cellar", "rest_car",
                                          "hide_in_cellar_safe", "force_cellar_stay",
                                          "tony_sleeps_car", "avoid_livingroom_sleep_car", "reject_cellar_sleep_car"):
                    self._begin_fade_in(FADE_MS)

       # Déplacements voiture (arrive/depart/chase)
        if self._event_name in ("arrive_house", "depart", "harold_arrives_chase", "arrival_from_top") and self._event_phase == "run":
            prev = pygame.Vector2(self.car.center)
            t = 1.0 - max(self._move_dur_ms, 0) / max(self._move_total_ms, 1)
            t_eased = _ease_in_out(t)
            cur = self._from_xy.lerp(self._to_xy, t_eased)
            self.car.center = (int(cur.x), int(cur.y))

            delta = (cur - prev)
            moving = delta.length_squared() > 0.1
            if moving:
                self._car_facing_dir = _facing_from_vec(delta.x, delta.y)
            self._car_moving = moving

            # Choisir l'animator selon le flag
            animator = self.police_animator if self._use_police_car else self.car_animator
            animator.update(self._car_facing_dir, self._car_moving, dt_ms)

            self._move_dur_ms -= dt_ms
            if self._move_dur_ms <= 0:
                self.car.center = (int(self._to_xy.x), int(self._to_xy.y))
                self._car_moving = False
                animator.update(self._car_facing_dir, False, dt_ms)
                self._finish_event()

        if self._car_moving:
            self.car_animator.update(self._car_facing_dir, True, dt_ms)
        else:
            self.car_animator.update(self._car_facing_dir, False, dt_ms)

        if self._tony_target is not None:
            if self._update_tony_step(dt_ms):
                self._finish_event()
        else:
            if self.tony_visible:
                self.tony_walker.update(self._tony_facing_dir, False, dt_ms)

        # Sécurité : si la boîte de dialogue remonte, éviter chevauchement
        if self.car.bottom > self.safe_bottom:
            self.car.bottom = self.safe_bottom

        # Martha idle anim si visible
        if self.martha_visible:
            self.grandma_walker.update(self._grandma_facing_dir, False, dt_ms)

    # ---------- Draw ----------
    def draw(self, screen: pygame.Surface):
        # fond (tmx)
        screen.blit(self.map_surface, (0, 0))

        # sprites
        if self._use_police_car:
            car_frame = self.police_animator.current_frame()
        else:
            car_frame = self.car_animator.current_frame()
        screen.blit(car_frame, self.car.topleft)

        if self.martha_visible:
            gm_frame = self.grandma_walker.current_frame()
            screen.blit(gm_frame, (self.martha.x, self.martha.y))

        # Tony (si visible)
        if self.tony_visible:
            tony_frame = self.tony_walker.current_frame()
            screen.blit(tony_frame, (self.tony_rect.x, self.tony_rect.y))


        # --- HUD Trust / PoliceGap (comme scène 1)
        trust = getattr(self.gvars, "trust", "?")
        pgap  = getattr(self.gvars, "police_gap", "?")
        hud_txt = f"Trust: {trust}   PoliceGap: {pgap}"
        hud_surf = self.hud_font.render(hud_txt, True, self.hud_color)
        screen.blit(hud_surf, self.hud_pos)
        
        # Fades
        if self._fade_dir != 0 or (self._event_name in ("rest_living_room", "rest_cellar", "rest_car",
                                                        "hide_in_cellar_safe", "force_cellar_stay",
                                                        "tony_sleeps_car", "avoid_livingroom_sleep_car", "reject_cellar_sleep_car")
                                   and self._timer_ms > 0):
            overlay = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
            # teintes légères selon le lieu de repos (optionnel)
            tint = (0, 0, 0)
            if self._event_name in ("rest_cellar", "hide_in_cellar_safe", "force_cellar_stay"):
                tint = (5, 5, 12)
            elif self._event_name == "rest_living_room":
                tint = (12, 8, 4)
            alpha = self._fade_alpha if self._fade_dir != 0 else 200
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

    def _start_tony_step_to(self, target_xy: tuple[int, int]):
        self._tony_target = pygame.Vector2(target_xy)
        self._tony_moving = True
        dx = self._tony_target.x - self.tony_rect.centerx
        dy = self._tony_target.y - self.tony_rect.centery
        self._tony_facing_dir = "right" if dx > 0 else "left" if abs(dx) > abs(dy) else ("down" if dy > 0 else "up")
        self.tony_walker.update(self._tony_facing_dir, True, 0)

    def _update_tony_step(self, dt_ms: int) -> bool:
        if self._tony_target is None:
            return False
        pos = pygame.Vector2(self.tony_rect.center)
        to_go = self._tony_target - pos
        step = max(1e-6, self._tony_speed * (dt_ms / 1000.0))
        if to_go.length() <= step:
            self.tony_rect.center = (int(self._tony_target.x), int(self._tony_target.y))
            self._tony_target = None
            self._tony_moving = False
            self.tony_walker.update(self._tony_facing_dir, False, 0)
            return True
        move = to_go.normalize() * step
        self.tony_rect.centerx += int(round(move.x))
        self.tony_rect.centery += int(round(move.y))
        self._tony_facing_dir = "right" if move.x > 0 else "left" if abs(move.x) > abs(move.y) else ("down" if move.y > 0 else "up")
        self.tony_walker.update(self._tony_facing_dir, True, dt_ms)
        return False
