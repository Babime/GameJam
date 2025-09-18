
from __future__ import annotations
from pathlib import Path
from typing import Optional, Callable
import pygame
from core.config import ASSETS_DIR, GENERAL_ASSET_DIR, FONT_PATH
from core.actor_sprite import (
    create_car_animator, create_grandma_animator, create_police_animator, create_tony_animator
)

# --- TMX optional ---
try:
    import pytmx
    from pytmx.util_pygame import load_pygame as _tmx_load_pygame
    _PYTMX_OK = True
except Exception:
    _PYTMX_OK = False
    pytmx = None  # type: ignore

# ----------------- Params -----------------
PLAYER_SIZE = 32
SPRITE_DRAW_H = 56
FADE_MS = 900
CAR_SPEED = 240
SCENE_PAUSE_MS = 800

# Background drive for the cellar path
BG_DRIVE_DELAY_MS = 500   # wait 0.5s after Tony disappears
BG_NUDGE_PX       = -20    # go "forward" (down) by 40px
BG_NUDGE_SPEED    = 200   # px/s for the small nudge
BG_RIGHT_PX       = 400   # then drive 400px to the right
BG_RIGHT_SPEED    = 80    # px/s (slow)

# Legacy anchors measured in “fit/contain” screen space
DRIVE_IN_START = (-200, 520)
DRIVE_IN_STOP  = ( 420, 500)
PORCH_POS      = ( 600, 460)
DRIVE_OUT_END  = (1400, 520)

TOP_ENTRY          = (460, -120)
LEFT_HOUSE_PARK    = (460, 540)
LEFT_HOUSE_DOOR    = (280, 470)
TONY_STAND_OFFSET  = (-28, 0)
TONY_STEP_TO_STAND = ( -8, 0)

MARTHA_STEP_PX = 24  # one “step” in screen pixels (we’ll take 2 steps → 48 px)

# ======================================================
# Helpers
# ======================================================
def _ease_in_out(t: float) -> float:
    import math
    return 0.5 - 0.5 * math.cos(max(0.0, min(1.0, t)) * math.pi)

def _blit_tile(surface, img, x, y, tile_h, tileset_off):
    tox, toy = tileset_off
    y += (tile_h - img.get_height())
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

        elif isinstance(layer, pytmx.TiledObjectGroup):
            for obj in layer:
                if hasattr(obj, "gid") and obj.gid:
                    img = tmx.get_tile_image_by_gid(obj.gid)
                    if not img:
                        continue
                    ts = tmx.get_tileset_from_gid(obj.gid)
                    tileset_off = getattr(ts, "tileoffset", (0, 0)) or (0, 0)
                    x = int(obj.x + ox)
                    y = int(obj.y + oy)
                    _blit_tile(raw, img, x, y, th, tileset_off)

        # Image layers intentionally skipped (fixes the white rectangle)

    return raw

def _facing_from_vec(vx: float, vy: float) -> str:
    # Prefer horizontal when equal/similar
    if abs(vx) >= abs(vy):
        return "right" if vx > 0 else "left"
    else:
        return "down" if vy > 0 else "up"

# ======================================================
# Scene
# ======================================================
class CountryHouseScene:
    def __init__(self, win_w: int, win_h: int, gvars):
        self.win_w, self.win_h = win_w, win_h
        self.gvars = gvars

        # Transforms
        self._map_scale   = 1.0
        self._map_offset  = (0, 0)
        self._raw_map_size = (win_w, win_h)
        self._fit_scale   = 1.0
        self._fit_offset  = (0, 0)

    # --- Cellar path background car drive (non-blocking) ---
        self._bg_drive_active = False
        self._bg_state = ""              # "", "delay", "nudge", "turn", "right"
        self._bg_timer_ms = 0
        self._bg_from_xy = pygame.Vector2(0, 0)
        self._bg_to_xy   = pygame.Vector2(0, 0)
        self._bg_total_ms = 1
        self._bg_dur_ms   = 0


        # TMX to fullscreen
        self.map_surface = self._render_tmx_fullscreen(ASSETS_DIR / "village" / "Village.tmx")

        # Convert legacy anchors → map coords
        self.DRIVE_IN_START_MAP   = self._screen_to_map_using_fit(DRIVE_IN_START)
        self.DRIVE_IN_STOP_MAP    = self._screen_to_map_using_fit(DRIVE_IN_STOP)
        self.PORCH_POS_MAP        = self._screen_to_map_using_fit(PORCH_POS)
        self.TOP_ENTRY_MAP        = self._screen_to_map_using_fit(TOP_ENTRY)
        self.LEFT_HOUSE_PARK_MAP  = self._screen_to_map_using_fit(LEFT_HOUSE_PARK)
        self._tony_spawn_center_screen = self.map_to_screen(self.LEFT_HOUSE_PARK_MAP)
        self.LEFT_HOUSE_DOOR_MAP  = self._screen_to_map_using_fit(LEFT_HOUSE_DOOR)

        fit_s = (self._fit_scale or 1.0)
        self.TONY_STAND_OFFSET_MAP  = (TONY_STAND_OFFSET[0]  / fit_s, TONY_STAND_OFFSET[1]  / fit_s)
        self.TONY_STEP_TO_STAND_MAP = (TONY_STEP_TO_STAND[0] / fit_s, TONY_STEP_TO_STAND[1] / fit_s)

        # Entities
        self.car = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.car.center = self.map_to_screen(self.DRIVE_IN_START_MAP)

        self.martha = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.martha.center = self.map_to_screen(self.LEFT_HOUSE_DOOR_MAP)
        self._martha_initial = self.martha.center
        self.martha_visible = False

        self.tony_rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.tony_visible = False

        # Animations
        self.grandma_walker = create_grandma_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H - 2)
        self._grandma_facing_dir = "down"
        self._grandma_moving = False

        self.car_animator = create_car_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H)
        self.police_animator = create_police_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H)
        self._car_facing_dir = "right"
        self._use_police_car = False
        self._car_moving = False

        self.tony_walker = create_tony_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H)
        self._tony_facing_dir = "down"
        self._tony_speed = 110.0

        # Cinematic state
        self._event_name: Optional[str] = None
        self._event_phase: str = ""
        self._on_done: Optional[Callable[[str], None]] = None
        self._timer_ms: int = 0

        self._from_xy = pygame.Vector2(self.car.center)
        self._to_xy   = pygame.Vector2(self.car.center)
        self._move_total_ms = 1
        self._move_dur_ms = 0

        # Tony enter (2-phase path) helpers
        self._enter_target: Optional[pygame.Vector2] = None
        self._enter_phase: str = ""
        self._martha_face_forward_triggered = False
        self._martha_face_turn_timer_ms = 0

        # Audio: siren
        self._siren_sound: Optional[pygame.mixer.Sound] = None
        self._siren_channel: Optional[pygame.mixer.Channel] = None

        # Fades / overlay
        self._fade_ms = 0
        self._fade_dir = 0
        self._fade_alpha = 0
        self._dark_hold = False

        # Dialogue layout guard
        self.safe_bottom = self.win_h

    # ---------- TMX fullscreen ----------
    def _render_tmx_fullscreen(self, tmx_path: Path) -> pygame.Surface:
        W, H = self.win_w, self.win_h

        if _PYTMX_OK and tmx_path.suffix.lower() == ".tmx" and tmx_path.exists():
            tmx = _tmx_load_pygame(str(tmx_path))
            raw = _render_tmx_raw(tmx)
            rw, rh = raw.get_size()
            self._raw_map_size = (rw, rh)

            scale_cover = max(W / rw, H / rh)
            new_w, new_h = int(rw * scale_cover), int(rh * scale_cover)
            ox, oy = ((W - new_w) // 2, (H - new_h) // 2)

            scale_fit = min(W / rw, H / rh)
            fit_w, fit_h = int(rw * scale_fit), int(rh * scale_fit)
            fit_ox, fit_oy = ((W - fit_w) // 2, (H - fit_h) // 2)

            new = pygame.transform.smoothscale(raw, (new_w, new_h))
            surf = pygame.Surface((W, H), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 255))
            surf.blit(new, (ox, oy))

            self._map_scale   = scale_cover
            self._map_offset  = (ox, oy)
            self._fit_scale   = scale_fit
            self._fit_offset  = (fit_ox, fit_oy)
            return surf

        # fallback
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        surf.fill((22, 24, 28, 255))
        pygame.draw.rect(surf, (72, 88, 96), (520, 340, 280, 180))
        pygame.draw.rect(surf, (180, 190, 210), (635, 360, 50, 50))
        pygame.draw.rect(surf, (150, 120, 90), (675, 440, 60, 80))
        self._map_scale = 1.0
        self._map_offset = (0, 0)
        self._raw_map_size = (W, H)
        self._fit_scale = 1.0
        self._fit_offset = (0, 0)
        return surf

    # ---------- Coord transforms ----------
    def _screen_to_map_using_fit(self, p):
        x, y = p
        fx, fy = self._fit_offset
        s = (self._fit_scale or 1.0)
        return ((x - fx) / s, (y - fy) / s)

    def map_to_screen(self, p):
        x, y = p
        ox, oy = self._map_offset
        s = (self._map_scale or 1.0)
        return (int(x * s + ox), int(y * s + oy))

    # ---------- API moteur ----------
    def layout_for_dialogue(self, dialog_top: int):
        margin = 8
        self.safe_bottom = max(0, dialog_top - margin)

    def start_event(self, event_name: str, on_done: Callable[[str], None]):
        self._event_name = event_name
        self._on_done = on_done
        self._event_phase = "run"
        self._timer_ms = 0

        # ---- arrivals/departs ----
        if event_name == "arrival_from_top":
            self._use_police_car = False

            start_xy = self.map_to_screen(self.TOP_ENTRY_MAP)
            stop_xy  = list(self.map_to_screen(self.LEFT_HOUSE_PARK_MAP))

            # (optional) keep your slight downward bias if you want
            stop_xy[1] += BG_NUDGE_PX

            # NO clamp to safe_bottom here
            self._set_move(self.car, start_xy, tuple(stop_xy), pixels_per_sec=CAR_SPEED)
            self._car_facing_dir = "down"
            self._car_moving = True
            self.car_animator.update(self._car_facing_dir, True, 0)

        elif event_name in ("depart", "harold_arrives_chase"):
            self._dark_hold = False
            self._stop_sirens()

            self._use_police_car = True
            self._set_move(
                self.car,
                self.map_to_screen(self.TOP_ENTRY_MAP),
                self.map_to_screen(self.LEFT_HOUSE_PARK_MAP),
                pixels_per_sec=CAR_SPEED
            )
            self._car_facing_dir = "left"
            self._car_moving = True
            self.police_animator.update(self._car_facing_dir, True, 0)

        elif event_name == "tony_exit_car":
            # Make Tony appear left of the car, aligned to the car's vertical midline
            self.tony_visible = True

            car_cx, car_cy = self.car.center

            # Face left so we can measure the correct frame width
            self._tony_facing_dir = "left"
            self.tony_walker.update(self._tony_facing_dir, False, 0)
            tony_w = self.tony_walker.current_frame().get_width()

            # Put Tony's RIGHT edge on the car center line, same Y as the car
            start_x = car_cx - (tony_w // 2)
            start_y = car_cy  # add a small +/− if you want a vertical nudge

            # Optional: tiny step to the left for a bit of life
            step_px = 8

            self.tony_rect.center = (int(start_x), int(start_y))
            self._from_xy = pygame.Vector2(self.tony_rect.center)
            self._to_xy   = pygame.Vector2(start_x - step_px, start_y)

            dist = abs(step_px)
            self._move_total_ms = self._move_dur_ms = max(1, int((dist / 90.0) * 1000))

        elif event_name == "martha_exit_house":
            self.martha_visible = True
            self.martha.center = self.map_to_screen(self.LEFT_HOUSE_DOOR_MAP)
            self._martha_initial = self.martha.center
            self._grandma_facing_dir = "right"
            self._grandma_moving = False
            self.grandma_walker.update(self._grandma_facing_dir, False, 0)
            self._timer_ms = 500

        elif event_name == "martha_greets":
            self.martha_visible = True
            self._grandma_facing_dir = "down"
            self._grandma_moving = False
            self.grandma_walker.update(self._grandma_facing_dir, False, 0)
            self._timer_ms = SCENE_PAUSE_MS

        # ---- fade-y rest events ----
        elif event_name in ("rest_living_room", "rest_cellar", "rest_car",
                            "hide_in_cellar_safe", "force_cellar_stay",
                            "tony_sleeps_car", "avoid_livingroom_sleep_car", "reject_cellar_sleep_car"):
            self._begin_fade_out(FADE_MS if "rest_car" not in event_name else int(FADE_MS * 0.6))

        # ---- Granny small step / Tony enter living ----
        elif event_name == "martha_step_right":
            start = pygame.Vector2(self.martha.center)
            end = pygame.Vector2(start.x + 2 * MARTHA_STEP_PX, start.y)
            self._from_xy = start
            self._to_xy = end
            dist = end.distance_to(start)
            self._move_total_ms = self._move_dur_ms = max(1, int((dist / 90.0) * 1000))
            self._grandma_facing_dir = "right"
            self._grandma_moving = True

        elif event_name == "tony_enter_living":
            self._enter_target = pygame.Vector2(self._martha_initial)
            self._enter_phase = "horiz"
            self._martha_face_forward_triggered = False
            self._martha_face_turn_timer_ms = 0

        elif event_name == "martha_back_home":
            start = pygame.Vector2(self.martha.center)
            end = pygame.Vector2(self._martha_initial)
            self._from_xy = start
            self._to_xy = end
            dist = end.distance_to(start)
            self._move_total_ms = self._move_dur_ms = max(1, int((dist / 90.0) * 1000))
            self._grandma_facing_dir = "left" if end.x < start.x else "right"
            self._grandma_moving = True

        elif event_name == "night_cut_with_sirens":
            self._begin_fade_out(500)
            self._event_phase = "darken"
            self._dark_hold = False
            self._timer_ms = 0

        elif event_name == "stop_sirens":
            self._stop_sirens()
            self._finish_event()
            return

        # ---- NEW (CELLAR PATH): Tony turns & disappears, then background car drive ----
        elif event_name == "cellar_tony_turn_disappear":
            # tiny step to the RIGHT then hide
            self.tony_visible = True
            start = pygame.Vector2(self.tony_rect.center)
            end   = pygame.Vector2(start.x + 16, start.y)
            self._from_xy = start
            self._to_xy   = end
            dist = end.distance_to(start)
            self._move_total_ms = self._move_dur_ms = max(1, int((dist / 120.0) * 1000))
            self._tony_facing_dir = "right"

        elif event_name == "cellar_start_bg_drive":
            # non-blocking: set up a background sequence and immediately finish the event
            self._bg_drive_active = True
            self._bg_state = "delay"
            self._bg_timer_ms = BG_DRIVE_DELAY_MS
            self._finish_event()
            return

        else:
            # no-op to avoid blocking the graph
            self._finish_event()
            return
        

    def handle_event(self, ev: pygame.event.Event):
        pass

    # ---------- Update ----------
    def update(self, dt_ms: int):
        # Fades
        if self._fade_dir != 0 and self._fade_ms > 0:
            step = (255 / max(self._fade_ms, 1)) * dt_ms
            self._fade_alpha = int(max(0, min(255, self._fade_alpha + step * self._fade_dir)))
            self._fade_ms -= dt_ms
            if self._fade_ms <= 0:
                if self._event_name in ("rest_living_room", "rest_cellar", "rest_car",
                                        "hide_in_cellar_safe", "force_cellar_stay",
                                        "tony_sleeps_car", "avoid_livingroom_sleep_car", "reject_cellar_sleep_car"):
                    if self._fade_dir > 0:
                        self._timer_ms = 1200
                        self._fade_dir = 0
                    elif self._fade_dir < 0:
                        self._fade_dir = 0
                        self._finish_event()
                elif self._event_name == "night_cut_with_sirens" and self._event_phase == "darken":
                    self._dark_hold = True
                    self._fade_dir = 0
                    self._fade_alpha = 255
                    self._event_phase = "wait_sirens"
                    self._timer_ms = 2000

        # Timers
        if self._timer_ms > 0:
            self._timer_ms -= dt_ms
            if self._timer_ms <= 0:
                if self._event_name == "martha_greets":
                    self._finish_event()
                elif self._event_name in ("rest_living_room", "rest_cellar", "rest_car",
                                          "hide_in_cellar_safe", "force_cellar_stay",
                                          "tony_sleeps_car", "avoid_livingroom_sleep_car", "reject_cellar_sleep_car"):
                    self._begin_fade_in(FADE_MS)
                elif self._event_name == "martha_exit_house":
                    self._finish_event()
                elif self._event_name == "night_cut_with_sirens" and self._event_phase == "wait_sirens":
                    self._play_sirens()
                    self._finish_event()

        # Car moves (blocking events)
        if self._event_name in ("arrival_from_top", "arrive_house", "depart", "harold_arrives_chase") and self._event_phase == "run":
            prev = pygame.Vector2(self.car.center)
            t = 1.0 - max(self._move_dur_ms, 0) / max(self._move_total_ms, 1)
            cur = self._from_xy.lerp(self._to_xy, _ease_in_out(t))
            self.car.center = (int(cur.x), int(cur.y))

            delta = (cur - prev)
            moving = delta.length_squared() > 0.1
            if moving:
                self._car_facing_dir = _facing_from_vec(delta.x, delta.y)
            self._car_moving = moving

            (self.police_animator if self._use_police_car else self.car_animator)\
                .update(self._car_facing_dir, self._car_moving, dt_ms)

            self._move_dur_ms -= dt_ms
            if self._move_dur_ms <= 0:
                self.car.center = (int(self._to_xy.x), int(self._to_xy.y))
                self._car_moving = False
                (self.police_animator if self._use_police_car else self.car_animator)\
                    .update(self._car_facing_dir, False, dt_ms)
                self._finish_event()

        # Tony step for tony_exit_car
        if self._event_name == "tony_exit_car" and self._event_phase == "run":
            prev = pygame.Vector2(self.tony_rect.center)
            t = 1.0 - max(self._move_dur_ms, 0) / max(self._move_total_ms, 1)
            cur = self._from_xy.lerp(self._to_xy, _ease_in_out(t))
            self.tony_rect.center = (int(cur.x), int(cur.y))
            self._tony_facing_dir = "left"
            self.tony_walker.update(self._tony_facing_dir, True, dt_ms)

            self._move_dur_ms -= dt_ms
            if self._move_dur_ms <= 0:
                self.tony_rect.center = (int(self._to_xy.x), int(self._to_xy.y))
                self.tony_walker.update(self._tony_facing_dir, False, dt_ms)
                self._finish_event()

        # NEW: Tony small step then disappear (cellar path)
        if self._event_name == "cellar_tony_turn_disappear" and self._event_phase == "run":
            prev = pygame.Vector2(self.tony_rect.center)
            t = 1.0 - max(self._move_dur_ms, 0) / max(self._move_total_ms, 1)
            cur = self._from_xy.lerp(self._to_xy, _ease_in_out(t))
            self.tony_rect.center = (int(cur.x), int(cur.y))
            self._tony_facing_dir = "right"
            self.tony_walker.update(self._tony_facing_dir, True, dt_ms)

            self._move_dur_ms -= dt_ms
            if self._move_dur_ms <= 0:
                self.tony_rect.center = (int(self._to_xy.x), int(self._to_xy.y))
                # disappear
                self.tony_visible = False
                self.tony_walker.update(self._tony_facing_dir, False, dt_ms)
                self._finish_event()

        # NEW: Background car drive for the cellar path (non-blocking)
        if self._bg_drive_active:
            if self._bg_state == "delay":
                self._bg_timer_ms -= dt_ms
                if self._bg_timer_ms <= 0:
                    # no Y clamp; keep current y so it can be under the box
                    now = pygame.Vector2(self.car.center)
                    self._bg_from_xy = now
                    self._bg_to_xy   = pygame.Vector2(now.x + BG_RIGHT_PX, now.y)
                    dist = self._bg_to_xy.distance_to(self._bg_from_xy)
                    self._bg_total_ms = self._bg_dur_ms = max(1, int((dist / max(1.0, BG_RIGHT_SPEED)) * 1000))

                    self._car_facing_dir = "right"
                    self._car_moving = True
                    (self.police_animator if self._use_police_car else self.car_animator).update("right", True, 0)
                    self._bg_state = "right"
                    
            elif self._bg_state == "right":
                prev = pygame.Vector2(self.car.center)
                t = 1.0 - max(self._bg_dur_ms, 0) / max(self._bg_total_ms, 1)
                cur = self._bg_from_xy.lerp(self._bg_to_xy, _ease_in_out(t))
                self.car.center = (int(cur.x), int(cur.y))

                delta = cur - prev
                moving = delta.length_squared() > 0.1
                if moving:
                    self._car_facing_dir = _facing_from_vec(delta.x, delta.y)
                (self.police_animator if self._use_police_car else self.car_animator)\
                    .update(self._car_facing_dir, moving, dt_ms)

                self._bg_dur_ms -= dt_ms
                if self._bg_dur_ms <= 0:
                    self.car.center = (int(self._bg_to_xy.x), int(self._bg_to_xy.y))
                    self._car_moving = False
                    (self.police_animator if self._use_police_car else self.car_animator)\
                        .update(self._car_facing_dir, False, dt_ms)
                    self._bg_drive_active = False
                    self._bg_state = ""

        # NEW/OLD: Martha moves (step right/back home)
        if self._event_name in ("martha_step_right", "martha_back_home") and self._event_phase == "run":
            prev = pygame.Vector2(self.martha.center)
            t = 1.0 - max(self._move_dur_ms, 0) / max(self._move_total_ms, 1)
            cur = self._from_xy.lerp(self._to_xy, _ease_in_out(t))
            self.martha.center = (int(cur.x), int(cur.y))

            delta = cur - prev
            self._grandma_moving = (delta.length_squared() > 0.1)
            if self._grandma_moving:
                self._grandma_facing_dir = _facing_from_vec(delta.x, delta.y)

            self._move_dur_ms -= dt_ms
            if self._move_dur_ms <= 0:
                self.martha.center = (int(self._to_xy.x), int(self._to_xy.y))
                self._grandma_moving = False
                if self._event_name == "martha_back_home":
                    self._grandma_facing_dir = "down"
                self._finish_event()

        # Tony enters living (unchanged)
        if self._event_name == "tony_enter_living":
            if self._martha_face_turn_timer_ms > 0:
                self._martha_face_turn_timer_ms -= dt_ms
                if self._martha_face_turn_timer_ms <= 0:
                    self._grandma_facing_dir = "left"

            if self._enter_target is not None:
                cx, cy = self.tony_rect.centerx, self.tony_rect.centery
                tx, ty = int(self._enter_target.x), int(self._enter_target.y)
                step = max(1e-6, self._tony_speed * (dt_ms / 1000.0))

                if self._enter_phase == "horiz":
                    dx = tx - cx
                    if abs(dx) <= step:
                        cx = tx
                        self._enter_phase = "vert"
                    else:
                        cx += step if dx > 0 else -step
                        self._tony_facing_dir = "right" if dx > 0 else "left"
                        if not self._martha_face_forward_triggered and abs(cy - self.martha.centery) <= 2:
                            self._grandma_facing_dir = "down"
                            self._martha_face_forward_triggered = True
                            self._martha_face_turn_timer_ms = 500

                elif self._enter_phase == "vert":
                    dy = ty - cy
                    if abs(dy) <= step:
                        cy = ty
                        self.tony_rect.center = (int(cx), int(cy))
                        self.tony_visible = False
                        self._finish_event()
                    else:
                        cy += step if dy > 0 else -step
                        self._tony_facing_dir = "down" if dy > 0 else "up"

                self.tony_rect.center = (int(round(cx)), int(round(cy)))
            self.tony_walker.update(self._tony_facing_dir, self.tony_visible, dt_ms)


        # Grandma anim (idle/walk)
        if self.martha_visible:
            self.grandma_walker.update(self._grandma_facing_dir, self._grandma_moving, dt_ms)


    # ---------- Draw ----------
    def draw(self, screen: pygame.Surface):
        screen.blit(self.map_surface, (0, 0))

        # car
        car_frame = (self.police_animator.current_frame() if self._use_police_car
                     else self.car_animator.current_frame())
        screen.blit(car_frame, self.car.topleft)

        # Martha
        if self.martha_visible:
            gm_frame = self.grandma_walker.current_frame()
            screen.blit(gm_frame, self.martha.topleft)

        # Tony
        if self.tony_visible:
            tony_frame = self.tony_walker.current_frame()
            screen.blit(tony_frame, self.tony_rect.topleft)

        # Fades and night hold
        if self._fade_dir != 0 or self._dark_hold or (
            self._event_name in ("rest_living_room", "rest_cellar", "rest_car",
                                 "hide_in_cellar_safe", "force_cellar_stay",
                                 "tony_sleeps_car", "avoid_livingroom_sleep_car", "reject_cellar_sleep_car")
            and self._timer_ms > 0
        ):
            overlay = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
            tint = (0, 0, 0)
            if self._event_name in ("rest_cellar", "hide_in_cellar_safe", "force_cellar_stay"):
                tint = (5, 5, 12)
            elif self._event_name == "rest_living_room":
                tint = (12, 8, 4)
            alpha = self._fade_alpha if self._fade_dir != 0 else (255 if self._dark_hold else 200)
            overlay.fill((*tint, max(0, min(255, int(alpha)))))
            screen.blit(overlay, (0, 0))

    # ---------- Helpers ----------
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

    # Audio
    def _play_sirens(self):
        try:
            if self._siren_sound is None:
                siren_path = ASSETS_DIR / "village" / "sound" / "police-siren-397963.mp3"
                self._siren_sound = pygame.mixer.Sound(str(siren_path))
            if (self._siren_channel is None) or (not self._siren_channel.get_busy()):
                self._siren_channel = self._siren_sound.play(loops=-1)
        except Exception:
            pass

    def _stop_sirens(self):
        try:
            if self._siren_channel:
                self._siren_channel.fadeout(500)
                self._siren_channel = None
        except Exception:
            pass