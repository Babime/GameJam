from __future__ import annotations
from pathlib import Path
from typing import Optional, Callable
import math
import pygame

from core.config import ASSETS_DIR, GENERAL_ASSET_DIR
from core.actor_sprite import create_tony_animator


def _scale_to_height(img: pygame.Surface, target_h: int) -> pygame.Surface:
    w, h = img.get_size()
    if h <= 0:
        return img
    new_w = max(1, int(round(w * (target_h / h))))
    return pygame.transform.smoothscale(img, (new_w, target_h))


class StreetScene2Static:
    """
    Scene 2 – static background:
      - Draws assets/street/scene2.png (scaled to window width, centered vertically)
      - Places TONY at screen(605, 16) (TOPLEFT anchor), 2× size, facing down (idle)
      - Places JOHN (stranger) at screen(416, 289) (MIDBOTTOM anchor), 2× size
      - Subtle police light spill from the left edge (red/blue crossfade, soft falloff, jitter)

      Animated events handled here:

      Garage (right) move set variants
        * go_to_garage                : Tony down→right→up to (x=890, y=231)
        * garage_ignore_wrong_part1   : Tony down only to y=400 (beat for a mid-line)
        * garage_ignore_wrong_part2   : Tony right to x=890, then up to y=231 (faces up)

      “Ignore helpful advice” path (goes left first, sees cops, then bolts right & up)
        * ignore_help_go_left         : Tony LEFT to x=290
        * ignore_help_escape_right_up : Tony RIGHT (fast) to x=890, then UP to y=231 (faces up)
        * ignore_help_escape_right    : Tony RIGHT (fast) to x=890 (stops there)
        * ignore_help_up              : Tony faces UP, then UP to y=231

      Escape
        * drive_away                  : Tony hides 2s, car appears there, car drives down off-screen
    """
    # Requested placements
    STRANGER_POS = (416, 289)  # midbottom anchor (feet planted)
    TONY_POS     = (605,  16)  # topleft anchor (explicit pixel)

    # Sprite sizes (doubled here only)
    BASE_H = 56
    BIG_H  = BASE_H * 2  # ← twice as big

    # Movement speeds (px/sec)
    TONY_SPEED       = 220
    TONY_SPEED_FAST  = 340
    CAR_SPEED        = 280

    def __init__(self, win_w: int, win_h: int, gvars):
        self.win_w = win_w
        self.win_h = win_h
        self.gvars = gvars

        # Police light params
        self._police_speed_hz   = 1.3   # 1–2 Hz
        self._police_intensity  = 0.9   # 0..1
        self._police_falloff_px = 24.0  # gaussian sigma along X
        self._police_noise_amp  = 0.22  # 0..1 small shimmer
        self._light_cache: dict[tuple[int, int, int], list[list[float]]] = {}

        # ---- Load and scale background ----
        img_path = ASSETS_DIR / "street" / "scene2.png"
        try:
            raw = pygame.image.load(str(img_path)).convert_alpha()
        except Exception:
            raw = pygame.Surface((1536, 102), pygame.SRCALPHA)
            raw.fill((20, 20, 20, 255))

        rw, rh = raw.get_size()
        scale = (self.win_w / rw) if rw else 1.0
        new_w = max(1, int(round(rw * scale)))
        new_h = max(1, int(round(rh * scale)))
        self.bg = pygame.transform.smoothscale(raw, (new_w, new_h))
        self.bg_rect = self.bg.get_rect(center=(win_w // 2, win_h // 2))

        # ---- Tony sprite (idle on first DOWN frame) – now 2x size ----
        self.walker = create_tony_animator(GENERAL_ASSET_DIR, target_height=self.BIG_H)
        self._facing = "down"
        self._moving = False
        frame = self.walker.current_frame()
        self.tony_rect = frame.get_rect(topleft=self.TONY_POS)
        self.tony_visible = True

        # ---- Stranger (John) – back-facing, 2x ----
        try:
            stranger_raw = pygame.image.load(
                str(GENERAL_ASSET_DIR / "stranger_walk_facing_back_1.png")
            ).convert_alpha()
        except Exception:
            stranger_raw = self.walker.current_frame().copy()
        self.stranger_img = _scale_to_height(stranger_raw, self.BIG_H)
        self.stranger_rect = self.stranger_img.get_rect(midbottom=self.STRANGER_POS)
        self.stranger_visible = True

        # ---- Car (front) for escape ----
        try:
            car_raw = pygame.image.load(str(GENERAL_ASSET_DIR / "car_front.png")).convert_alpha()
        except Exception:
            car_raw = pygame.Surface((80, 56), pygame.SRCALPHA)
            pygame.draw.rect(car_raw, (120, 120, 120, 255), car_raw.get_rect(), border_radius=8)
        self.car_img = _scale_to_height(car_raw, self.BIG_H)
        self.car_rect = self.car_img.get_rect()
        self.car_visible = False

        # --- event state ---
        self._event_name: Optional[str] = None
        self._event_phase: Optional[str] = None
        self._event_timer_ms: int = 0
        self._on_done: Optional[Callable[[str], None]] = None

        self.safe_bottom = win_h

    # ---------- Scene<->Dialogue bridge ----------
    def layout_for_dialogue(self, dialog_top: int):
        self.safe_bottom = max(0, dialog_top - 8)

    def start_event(self, event_name: str, on_done: Callable[[str], None]):
        """
        Supported events:
          - 'go_to_garage'               : (down→right→up) to x=890, y=231
          - 'garage_ignore_wrong_part1'  : down to y=400
          - 'garage_ignore_wrong_part2'  : right to x=890, then up to y=231
          - 'ignore_help_go_left'        : left to x=290
          - 'ignore_help_escape_right_up': right (FAST) to x=890, then up to y=231
          - 'ignore_help_escape_right'   : right (FAST) to x=890
          - 'ignore_help_up'             : face up, then up to y=231
          - 'drive_away'                 : hide Tony 2s, spawn car there, car goes down off-screen
        Others resolve immediately.
        """
        self._on_done = on_done
        self._event_name = event_name
        self._event_timer_ms = 0

        if event_name == "go_to_garage":
            self._event_phase = "garage_down"
            self._facing = "down"
            self._moving = True

        elif event_name == "garage_ignore_wrong_part1":
            self._event_phase = "giw_down"
            self._facing = "down"
            self._moving = True

        elif event_name == "garage_ignore_wrong_part2":
            self._event_phase = "giw_right"
            self._facing = "right"
            self._moving = True

        elif event_name == "ignore_help_go_left":
            self._event_phase = "ihl_left"
            self._facing = "left"
            self._moving = True

        elif event_name == "ignore_help_escape_right_up":
            self._event_phase = "ihe_right"
            self._facing = "right"
            self._moving = True

        elif event_name == "ignore_help_escape_right":
            self._event_phase = "iher_only_right"
            self._facing = "right"
            self._moving = True

        elif event_name == "ignore_help_up":
            self._event_phase = "iher_only_up"
            self._facing = "up"
            self._moving = True

        elif event_name == "drive_away":
            self._event_phase = "hide_tony_wait"
            self._event_timer_ms = 2000
            self.tony_visible = False
            self.car_visible = False

        else:
            self._finish_event_immediately()

    def _finish_event_immediately(self):
        if self._on_done and self._event_name:
            cb = self._on_done
            name = self._event_name
            self._event_name = None
            self._event_phase = None
            self._on_done = None
            self._event_timer_ms = 0
            cb(name)

    # ---------- Input (unused) ----------
    def handle_event(self, event: pygame.event.Event):
        return  # AI-only

    # ---------- Update ----------
    def update(self, dt_ms: int):
        dt = dt_ms / 1000.0
        moved = False

        # --------- Standard "go_to_garage" ---------
        if self._event_name == "go_to_garage":
            if self._event_phase == "garage_down":
                self._facing = "down"
                target_y = 400
                if self.tony_rect.top < target_y:
                    step = int(round(self.TONY_SPEED * dt))
                    self.tony_rect.top = min(target_y, self.tony_rect.top + step)
                    moved = True
                if self.tony_rect.top >= target_y:
                    self.tony_rect.top = target_y
                    self._event_phase = "garage_right"

            elif self._event_phase == "garage_right":
                self._facing = "right"
                target_x = 890
                if self.tony_rect.left < target_x:
                    step = int(round(self.TONY_SPEED * dt))
                    self.tony_rect.left = min(target_x, self.tony_rect.left + step)
                    moved = True
                if self.tony_rect.left >= target_x:
                    self.tony_rect.left = target_x
                    self._event_phase = "garage_up"
                    self._facing = "up"

            elif self._event_phase == "garage_up":
                self._facing = "up"
                target_y = 231
                if self.tony_rect.top > target_y:
                    step = int(round(self.TONY_SPEED * dt))
                    self.tony_rect.top = max(target_y, self.tony_rect.top - step)
                    moved = True
                if self.tony_rect.top <= target_y:
                    self.tony_rect.top = target_y
                    self._facing = "up"
                    self._moving = False
                    self._event_phase = None
                    self._finish_event_immediately()

            self._moving = moved

        # --------- Ignore-wrong, part 1: down to 400 (mid-line beat happens after) ---------
        elif self._event_name == "garage_ignore_wrong_part1":
            if self._event_phase == "giw_down":
                self._facing = "down"
                target_y = 400
                if self.tony_rect.top < target_y:
                    step = int(round(self.TONY_SPEED * dt))
                    self.tony_rect.top = min(target_y, self.tony_rect.top + step)
                    moved = True
                if self.tony_rect.top >= target_y:
                    self.tony_rect.top = target_y
                    self._event_phase = None
                    self._moving = False
                    self._finish_event_immediately()
            self._moving = moved

        # --------- Ignore-wrong, part 2: right to 890, then up to 231 ---------
        elif self._event_name == "garage_ignore_wrong_part2":
            if self._event_phase == "giw_right":
                self._facing = "right"
                target_x = 890
                if self.tony_rect.left < target_x:
                    step = int(round(self.TONY_SPEED * dt))
                    self.tony_rect.left = min(target_x, self.tony_rect.left + step)
                    moved = True
                if self.tony_rect.left >= target_x:
                    self.tony_rect.left = target_x
                    self._event_phase = "giw_up"
                    self._facing = "up"

            elif self._event_phase == "giw_up":
                self._facing = "up"
                target_y = 231
                if self.tony_rect.top > target_y:
                    step = int(round(self.TONY_SPEED * dt))
                    self.tony_rect.top = max(target_y, self.tony_rect.top - step)
                    moved = True
                if self.tony_rect.top <= target_y:
                    self.tony_rect.top = target_y
                    self._facing = "up"
                    self._moving = False
                    self._event_phase = None
                    self._finish_event_immediately()

            self._moving = moved

        # --------- Ignore-helpful branch: go LEFT first ---------
        elif self._event_name == "ignore_help_go_left":
            if self._event_phase == "ihl_left":
                self._facing = "left"
                target_x = 290
                if self.tony_rect.left > target_x:
                    step = int(round(self.TONY_SPEED * dt))
                    self.tony_rect.left = max(target_x, self.tony_rect.left - step)
                    moved = True
                if self.tony_rect.left <= target_x:
                    self.tony_rect.left = target_x
                    self._event_phase = None
                    self._moving = False
                    self._finish_event_immediately()
            self._moving = moved

        # --------- Ignore-helpful: RIGHT fast to 890, then UP to 231 (single event) ---------
        elif self._event_name == "ignore_help_escape_right_up":
            if self._event_phase == "ihe_right":
                self._facing = "right"
                target_x = 890
                if self.tony_rect.left < target_x:
                    step = int(round(self.TONY_SPEED_FAST * dt))
                    self.tony_rect.left = min(target_x, self.tony_rect.left + step)
                    moved = True
                if self.tony_rect.left >= target_x:
                    self.tony_rect.left = target_x
                    self._event_phase = "ihe_up"
                    self._facing = "up"

            elif self._event_phase == "ihe_up":
                self._facing = "up"
                target_y = 231
                if self.tony_rect.top > target_y:
                    step = int(round(self.TONY_SPEED * dt))
                    self.tony_rect.top = max(target_y, self.tony_rect.top - step)
                    moved = True
                if self.tony_rect.top <= target_y:
                    self.tony_rect.top = target_y
                    self._facing = "up"
                    self._moving = False
                    self._event_phase = None
                    self._finish_event_immediately()
            self._moving = moved

        # --------- RIGHT fast only (stop at 890) ---------
        elif self._event_name == "ignore_help_escape_right":
            if self._event_phase == "iher_only_right":
                self._facing = "right"
                target_x = 890
                if self.tony_rect.left < target_x:
                    step = int(round(self.TONY_SPEED_FAST * dt))
                    self.tony_rect.left = min(target_x, self.tony_rect.left + step)
                    moved = True
                if self.tony_rect.left >= target_x:
                    self.tony_rect.left = target_x
                    self._event_phase = None
                    self._moving = False
                    self._finish_event_immediately()
            self._moving = moved

        # --------- UP only (face up, go to 231) ---------
        elif self._event_name == "ignore_help_up":
            if self._event_phase == "iher_only_up":
                self._facing = "up"
                target_y = 231
                if self.tony_rect.top > target_y:
                    step = int(round(self.TONY_SPEED * dt))
                    self.tony_rect.top = max(target_y, self.tony_rect.top - step)
                    moved = True
                if self.tony_rect.top <= target_y:
                    self.tony_rect.top = target_y
                    self._facing = "up"
                    self._moving = False
                    self._event_phase = None
                    self._finish_event_immediately()
            self._moving = moved

        # --------- Car drive away ---------
        elif self._event_name == "drive_away":
            if self._event_phase == "hide_tony_wait":
                self._event_timer_ms -= dt_ms
                self._facing = "up"
                self._moving = False
                if self._event_timer_ms <= 0:
                    self.car_rect = self.car_img.get_rect()
                    self.car_rect.midbottom = self.tony_rect.midbottom
                    self.car_visible = True
                    self._event_phase = "car_drive_down"

            elif self._event_phase == "car_drive_down":
                step = int(round(self.CAR_SPEED * dt))
                self.car_rect.top += step
                if self.car_rect.top >= self.win_h:
                    self.car_visible = False
                    self._event_phase = None
                    self._finish_event_immediately()

            self.tony_visible = False

        else:
            self._moving = False

        # Update Tony's animator
        self.walker.update(self._facing, self._moving, dt_ms)

    # --- Police light FX: skinny, heavily blurred vertical beam ---
    def _draw_police_lights(
        self,
        screen: pygame.Surface,
        *,
        band_top: int = 420,
        band_bottom: int = 490,
        spill_x_max: int = 20,
        speed_hz: float = 1.3,
        intensity: float = 0.9,
        falloff_px: float = 24.0,
        noise_amp: float = 0.22
    ):
        band_h = max(0, band_bottom - band_top)
        spill_w = max(1, min(int(spill_x_max), 256))
        if band_h <= 0 or spill_w <= 0:
            return

        # time + crossfade
        t = pygame.time.get_ticks() * 0.001
        TAU = 2.0 * math.pi
        s = math.sin(TAU * max(0.01, speed_hz) * t)  # -1..1
        m = 0.5 * (s + 1.0)  # 0..1
        red  = (255,  64,  64)
        blue = ( 64, 128, 255)
        col = (
            int(red[0]  * (1.0 - m) + blue[0]  * m),
            int(red[1]  * (1.0 - m) + blue[1]  * m),
            int(red[2]  * (1.0 - m) + blue[2]  * m),
        )
        pulse_width = 0.28
        pulse = math.exp(- (s * s) / (pulse_width * pulse_width))
        amp = max(0.0, min(1.0, intensity)) * (0.75 + 0.25 * pulse)

        key = (spill_w, band_h, int(falloff_px * 1000))
        base = self._light_cache.get(key)
        if base is None:
            gx = [math.exp(- (x / max(1e-3, float(falloff_px))) ** 2) for x in range(spill_w)]
            cy = (band_h - 1) * 0.5
            sigma_y = band_h * 0.6
            gy = [math.exp(- (((y - cy) / max(1e-3, sigma_y)) ** 2)) for y in range(band_h)]
            base = [[gx[x] * gy[y] for x in range(spill_w)] for y in range(band_h)]
            self._light_cache[key] = base

        surf = pygame.Surface((spill_w, band_h), pygame.SRCALPHA)

        def _noise(xf: float, yf: float, tf: float) -> float:
            v = math.sin((xf * 12.9898 + yf * 78.233 + tf * 3.113) * 43758.5453)
            return v - math.floor(v)

        wobble_mag = 1
        for y in range(band_h):
            wobble = int(round(math.sin(0.8 * t + y * 0.05) * wobble_mag))
            row = base[y]
            for x in range(spill_w):
                sx = x + wobble
                if sx < 0 or sx >= spill_w:
                    continue
                b = row[sx]
                if b <= 0.002:
                    continue
                n = _noise(x, y, t)
                mod = 1.0 + noise_amp * (n - 0.5)
                a = int(max(0, min(255, 255.0 * amp * b * mod)))
                if a <= 0:
                    continue
                surf.set_at((x, y), (col[0], col[1], col[2], a))

        screen.blit(surf, (0, band_top), special_flags=pygame.BLEND_ADD)

    # ---------- Draw ----------
    def draw(self, screen: pygame.Surface):
        screen.fill((0, 0, 0))
        screen.blit(self.bg, self.bg_rect.topleft)

        # subtle, naturalistic police light from the left edge
        self._draw_police_lights(
            screen,
            band_top=420, band_bottom=490,
            spill_x_max=20,
            speed_hz=self._police_speed_hz,
            intensity=self._police_intensity,
            falloff_px=self._police_falloff_px,
            noise_amp=self._police_noise_amp
        )

        # John / stranger
        if self.stranger_visible:
            screen.blit(self.stranger_img, self.stranger_rect.topleft)

        # Tony
        if self.tony_visible:
            frame = self.walker.current_frame()
            screen.blit(frame, self.tony_rect.topleft)

        # Car
        if self.car_visible:
            screen.blit(self.car_img, self.car_rect.topleft)