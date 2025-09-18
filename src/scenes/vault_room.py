from __future__ import annotations
from pathlib import Path
import math
import random
import pygame
from typing import Optional, Callable
from core.config import GENERAL_ASSET_DIR
from core.actor_sprite import create_tony_animator

# ----------------- Room Config -----------------
WALL_H = 128
FLOOR_TILE_TARGET = 160
PLAYER_SIZE = 32           # collision box (kept as before)
PLAYER_SPEED = 240         # cinematic speed
SPRITE_DRAW_H = 56         # visual sprite height (scaled uniformly)
BUTTON_TARGET_H = 40
BUTTON_OFFSET_Y = 20
BUTTON_SPACING_X = 110
DOOR_MARGIN = 12

# Lighting
DEFAULT_DARK_ENABLED = True
DARK_ALPHA = 200
VISION_LENGTH = 240
FOV_DEG = 65
SOFT_EDGE = True
FEATHER_STEPS = 8

# ----------------- Utilities -----------------
def _load_image(path: Path) -> pygame.Surface:
    return pygame.image.load(str(path)).convert_alpha()

def _scale_to_width(img: pygame.Surface, width: int) -> pygame.Surface:
    w, h = img.get_size()
    new_h = int(round(h * (width / w)))
    return pygame.transform.scale(img, (width, new_h))

def _scale_to_height(img: pygame.Surface, height: int) -> pygame.Surface:
    w, h = img.get_size()
    new_w = int(round(w * (height / h)))
    return pygame.transform.scale(img, (new_w, height))

def _crop_center(img: pygame.Surface, crop_w: int, crop_h: int) -> pygame.Surface:
    w, h = img.get_size()
    x = max(0, (w - crop_w) // 2)
    y = max(0, (h - crop_h) // 2)
    rect = pygame.Rect(x, y, crop_w, crop_h)
    return img.subsurface(rect).copy()

def _angle_to_vec(angle_deg: float):
    rad = math.radians(angle_deg)
    return math.cos(rad), math.sin(rad)

def _cone_polygon(origin, angle_deg, fov_deg, length, arc_segments=18):
    ox, oy = origin
    half = fov_deg / 2.0
    start = angle_deg - half
    end = angle_deg + half
    pts = [origin]
    for i in range(arc_segments + 1):
        t = i / arc_segments
        a = start + t * (end - start)
        dx, dy = _angle_to_vec(a)
        pts.append((ox + dx * length, oy + dy * length))
    return pts

def _subtract_polygon_alpha(base_surf: pygame.Surface, poly_points, subtract_amount: int):
    if subtract_amount <= 0: return
    temp = pygame.Surface(base_surf.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(temp, (255, 255, 255, subtract_amount), poly_points)
    base_surf.blit(temp, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

def _make_darkness_cone(size, alpha, origin, angle_deg, fov_deg, length,
                        soft=True, feather_steps=8) -> pygame.Surface:
    w, h = size
    darkness = pygame.Surface((w, h), pygame.SRCALPHA)
    darkness.fill((0, 0, 0, alpha))
    inner_fov = fov_deg * 0.7
    inner_len = length * 0.85
    inner_poly = _cone_polygon(origin, angle_deg, inner_fov, inner_len)
    _subtract_polygon_alpha(darkness, inner_poly, 255)
    for i in range(feather_steps):
        t = (i + 1) / feather_steps
        fov_i = inner_fov + t * (fov_deg - inner_fov)
        len_i = inner_len + t * (length - inner_len)
        amt = int((1.0 - t) * 200)
        if amt <= 0: continue
        poly_i = _cone_polygon(origin, angle_deg, fov_i, len_i)
        _subtract_polygon_alpha(darkness, poly_i, amt)
    return darkness

# ----------------- Scene -----------------
class VaultRoomScene:
    """
    Encapsulates the vault room: assets, layout, scripted input, update, draw.
    Tony is always AI-driven; the player never moves him.

    Supported events:
      - 'go_to_medkit'         : walk to medkit, hide on contact, finish
      - 'wander_then_medkit'   : wander aimlessly ~3s, then go to medkit, finish
      - 'go_to_door'           : walk to center spot in front of both buttons
      - 'press_red_wait'       : walk to red, press, wait 1s, finish
      - 'press_green_open'     : walk to green, press, open door, finish
      - 'go_near_medkit_pause' : walk toward medkit but stop well before it, finish
    """
    def __init__(self, win_w: int, win_h: int, bank_asset_dir: Path, hud_font_path: Optional[Path], game_vars):
        self.win_w = win_w
        self.win_h = win_h
        self.bank_asset_dir = bank_asset_dir
        self.gvars = game_vars

        # ----- Load assets -----
        floor_raw = _load_image(bank_asset_dir / "floor_tile_1.png")
        wall_raw  = _load_image(bank_asset_dir / "wall.png")
        self.door_closed_raw = _load_image(bank_asset_dir / "door_closed.png")
        self.door_opened_raw = _load_image(bank_asset_dir / "door_opened.png")
        self.red_btn_up_raw   = _load_image(bank_asset_dir / "red_btn_not_pressed.png")
        self.red_btn_down_raw = _load_image(bank_asset_dir / "red_btn_pressed.png")
        self.green_btn_up_raw    = _load_image(bank_asset_dir / "green_btn_not_pressed.png")
        self.green_btn_down_raw  = _load_image(bank_asset_dir / "green_btn_pressed.png")
        self.medkit_raw = _load_image(bank_asset_dir / "health_kit.png")

        self.floor_tile = _crop_center(floor_raw, FLOOR_TILE_TARGET, FLOOR_TILE_TARGET)
        self.wall_img = pygame.transform.scale(wall_raw, (win_w, WALL_H))

        # Door
        max_door_h = max(1, WALL_H - DOOR_MARGIN * 2)
        door_closed_img = _scale_to_height(self.door_closed_raw, max_door_h)
        if door_closed_img.get_width() > win_w - DOOR_MARGIN * 2:
            door_closed_img = _scale_to_width(door_closed_img, win_w - DOOR_MARGIN * 2)
        door_opened_img = _scale_to_height(self.door_opened_raw, max_door_h)
        if door_opened_img.get_width() > win_w - DOOR_MARGIN * 2:
            door_opened_img = _scale_to_width(door_opened_img, win_w - DOOR_MARGIN * 2)
        self.door_closed_img = door_closed_img
        self.door_opened_img = door_opened_img
        self.door_rect = self.door_closed_img.get_rect()
        self.door_rect.centerx = win_w // 2
        self.door_rect.centery = WALL_H // 2

        # Buttons
        self.red_btn_up   = _scale_to_height(self.red_btn_down_raw, BUTTON_TARGET_H)     # down/up scale same size
        self.red_btn_down = _scale_to_height(self.red_btn_down_raw, BUTTON_TARGET_H)
        self.green_btn_up   = _scale_to_height(self.green_btn_up_raw, BUTTON_TARGET_H)
        self.green_btn_down = _scale_to_height(self.green_btn_down_raw, BUTTON_TARGET_H)
        self.red_btn_img = self.red_btn_up
        self.green_btn_img = self.green_btn_up
        self.red_btn_rect = self.red_btn_img.get_rect()
        self.green_btn_rect = self.green_btn_img.get_rect()
        base_y = WALL_H + BUTTON_OFFSET_Y
        self.red_btn_rect.midtop = (self.door_rect.centerx - BUTTON_SPACING_X, base_y)
        self.green_btn_rect.midtop = (self.door_rect.centerx + BUTTON_SPACING_X, base_y)
        self.red_collide = self.red_btn_rect.inflate(6, 6)
        self.green_collide = self.green_btn_rect.inflate(6, 6)

        # Medkit
        self.medkit_img = _scale_to_height(self.medkit_raw, 28)
        self.medkit_rect = self.medkit_img.get_rect()
        self.medkit_visible = True

        # Player (Tony) – collision box only; sprite is drawn on top
        self.player = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.safe_bottom = self.win_h - 8

        # Sprite animator (4-dir), initially facing up
        self.walker = create_tony_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H)
        self._facing_dir = "up"   # 'up','down','left','right'
        self.facing_angle = -90.0 # for lighting cone
        self._moving = False

        # State flags
        self.door_open = False
        self.red_pressed = False
        self.green_pressed = False

        self.dark_enabled = DEFAULT_DARK_ENABLED

        # Cinematic event state
        self._event_name: Optional[str] = None
        self._event_phase: Optional[str] = None
        self._event_target = pygame.Vector2(0, 0)
        self._on_event_done: Optional[Callable[[str], None]] = None

        # Wander state
        self._wander_timer_ms: int = 0
        self._wander_dir: int = 1  # left/right
        self._wander_speed_scale: float = 0.75  # fraction of PLAYER_SPEED

        # Wait state (e.g., after red press)
        self._wait_timer_ms: int = 0

        self._place_default_layout()

    # ---------- Layout ----------
    def _place_default_layout(self):
        self.player.left = 12
        self.player.bottom = self.win_h - 12
        self.medkit_rect.midbottom = (self.win_w // 2, self.win_h - 16)

    def layout_for_dialogue(self, dialog_top: int):
        margin = 8
        self.safe_bottom = max(0, dialog_top - margin)
        self.player.left = 12
        self.player.bottom = self.safe_bottom
        self.medkit_rect.midbottom = (self.win_w // 2, self.safe_bottom - 2)
        self.medkit_visible = True

    # ---------- Scene<->Dialogue bridge ----------
    def start_event(self, event_name: str, on_done: Callable[[str], None]):
        """
        Supported events:
          - 'go_to_medkit'       : walk to medkit, hide on contact, finish
          - 'wander_then_medkit' : wander aimlessly ~3s, then go to medkit, finish
          - 'go_to_door'         : walk to center spot in front of both buttons
          - 'press_red_wait'     : walk to red, press, wait 1s, finish
          - 'press_green_open'   : walk to green, press, open door, finish
          - 'go_near_medkit_pause' : walk toward medkit but stop well before it, finish
        """
        self._event_name = event_name
        self._on_event_done = on_done

        if event_name == "go_to_medkit":
            self._event_phase = "move"
            self._event_target = pygame.Vector2(
                self.medkit_rect.centerx,
                min(self.medkit_rect.centery, self.safe_bottom - self.player.height // 2)
            )

        elif event_name == "wander_then_medkit":
            self._event_phase = "wander"
            self._wander_timer_ms = 3000
            self._wander_dir = 1 if random.random() < 0.5 else -1

        elif event_name == "go_to_door":
            cx = (self.red_btn_rect.centerx + self.green_btn_rect.centerx) // 2
            y_target = max(self.red_btn_rect.bottom, self.green_btn_rect.bottom) + self.player.height // 2 + 10
            y_target = min(y_target, self.safe_bottom - self.player.height // 2)
            self._event_target = pygame.Vector2(cx, y_target)
            self._event_phase = "move"

        elif event_name == "press_red_wait":
            self._event_phase = "move"
            self._event_target = pygame.Vector2(self.red_btn_rect.centerx, self.red_btn_rect.centery)

        elif event_name == "press_green_open":
            self._event_phase = "move"
            self._event_target = pygame.Vector2(self.green_btn_rect.centerx, self.green_btn_rect.centery)

        elif event_name == "go_near_medkit_pause":
            # Walk toward the medkit but stop WAY before reaching it.
            self._event_phase = "move"
            offset = 180  # stop this many pixels BEFORE the medkit (tweak to taste)
            target_x = self.medkit_rect.centerx - offset
            target_y = min(self.medkit_rect.centery, self.safe_bottom - self.player.height // 2)
            # keep within safe bounds
            left_bound  = 12 + self.player.width // 2
            right_bound = self.win_w - 12 - self.player.width // 2
            target_x = max(left_bound, min(right_bound, target_x))
            self._event_target = pygame.Vector2(target_x, target_y)

        else:
            self._finish_event_immediately()

    def _finish_event_immediately(self):
        if self._on_event_done and self._event_name:
            cb = self._on_event_done
            name = self._event_name
            self._event_name = None
            self._event_phase = None
            self._on_event_done = None
            cb(name)

    # ---------- Update/Draw ----------
    def handle_event(self, event: pygame.event.Event):
        return  # AI-only

    def update(self, dt_ms: int):
        # default: assume not moving this tick
        self._moving = False

        if not self._event_name:
            # idle update (no cinematics currently active)
            self.walker.update(self._facing_dir, self._moving, dt_ms)
            return

        if self._event_name == "wander_then_medkit":
            if self._event_phase == "wander":
                self._update_wander(dt_ms)
                self.walker.update(self._facing_dir, self._moving, dt_ms)
                return
            elif self._event_phase == "move_to_medkit":
                self._update_move_to_target(dt_ms, pygame.Vector2(self.medkit_rect.center))
                if self.medkit_visible and self.player.colliderect(self.medkit_rect):
                    self.medkit_visible = False
                    self._set_facing("up")
                    self._finish_event_immediately()
                self.walker.update(self._facing_dir, self._moving, dt_ms)
                return

        if self._event_phase == "wait":
            self._wait_timer_ms -= dt_ms
            if self._wait_timer_ms <= 0:
                self._finish_event_immediately()
            self.walker.update(self._facing_dir, False, dt_ms)
            return

        if self._event_phase == "move":
            self._update_move_to_target(dt_ms, self._event_target)

            if self._event_name == "go_to_medkit":
                if self.medkit_visible and self.player.colliderect(self.medkit_rect):
                    self.medkit_visible = False
                    self._set_facing("up")
                    self._finish_event_immediately()

            elif self._event_name == "go_to_door":
                if self._distance_to(self._event_target) < 2.0:
                    self._set_facing("up")
                    self._finish_event_immediately()

            elif self._event_name == "press_red_wait":
                if self.player.colliderect(self.red_collide) or self._distance_to(self._event_target) < 2.0:
                    self.red_pressed = True
                    self.red_btn_img = self.red_btn_down
                    self._set_facing("up")
                    self._event_phase = "wait"
                    self._wait_timer_ms = 1000

            elif self._event_name == "press_green_open":
                if self.player.colliderect(self.green_collide) or self._distance_to(self._event_target) < 2.0:
                    self.green_pressed = True
                    self.green_btn_img = self.green_btn_down
                    self.door_open = True
                    self._set_facing("up")
                    self._finish_event_immediately()

            elif self._event_name == "go_near_medkit_pause":
                if self._distance_to(self._event_target) < 2.0:
                    self._set_facing("up")
                    # Do NOT pick up the medkit; just stop and let dialogue play
                    self._finish_event_immediately()

        self.walker.update(self._facing_dir, self._moving, dt_ms)

    # ---- movement helpers ----
    def _distance_to(self, vec: pygame.Vector2) -> float:
        pos = pygame.Vector2(self.player.centerx, self.player.centery)
        return (vec - pos).length()

    def _set_facing(self, dir4: str):
        self._facing_dir = dir4
        # keep lighting consistent with the old angle convention
        if dir4 == "right":
            self.facing_angle = 0.0
        elif dir4 == "down":
            self.facing_angle = 90.0
        elif dir4 == "left":
            self.facing_angle = 180.0
        else:  # "up"
            self.facing_angle = -90.0

    def _update_move_to_target(self, dt_ms: int, target: pygame.Vector2):
        """
        Move using 4-directional steps ONLY (no diagonals):
         - Prioritize horizontal movement until aligned, then vertical.
        """
        pos_x, pos_y = self.player.centerx, self.player.centery
        dx = target.x - pos_x
        dy = target.y - pos_y
        step = PLAYER_SPEED * (dt_ms / 1000.0)

        # prefer horizontal until aligned
        if abs(dx) > 1:
            move = max(-step, min(step, dx))
            pos_x += move
            self._moving = True
            self._set_facing("right" if move > 0 else "left")
        elif abs(dy) > 1:
            move = max(-step, min(step, dy))
            pos_y += move
            self._moving = True
            self._set_facing("down" if move > 0 else "up")

        self.player.centerx = int(round(pos_x))
        self.player.centery = int(round(pos_y))

    def _update_wander(self, dt_ms: int):
        # Keep Tony near the bottom area, moving left/right aimlessly (4-dir already)
        speed = PLAYER_SPEED * self._wander_speed_scale
        dx = speed * (dt_ms / 1000.0) * self._wander_dir
        new_x = self.player.centerx + dx

        left_bound = 12 + self.player.width // 2
        right_bound = self.win_w - 12 - self.player.width // 2

        if new_x <= left_bound:
            new_x = left_bound
            self._wander_dir = 1
        elif new_x >= right_bound:
            new_x = right_bound
            self._wander_dir = -1

        self.player.centerx = int(round(new_x))
        self.player.centery = self.safe_bottom - self.player.height // 2

        self._moving = True
        self._set_facing("right" if self._wander_dir > 0 else "left")

        self._wander_timer_ms -= dt_ms
        if self._wander_timer_ms <= 0:
            # Go pick up medkit now
            self._event_phase = "move_to_medkit"

    def draw(self, screen: pygame.Surface):
        # Floor
        screen.fill((20, 24, 28))
        tile_w, tile_h = self.floor_tile.get_size()
        for y in range(0, self.win_h, tile_h):
            for x in range(0, self.win_w, tile_w):
                screen.blit(self.floor_tile, (x, y))

        # Wall + door
        screen.blit(self.wall_img, (0, 0))
        door_img = self.door_opened_img if self.door_open else self.door_closed_img
        screen.blit(door_img, (
            self.win_w // 2 - door_img.get_width() // 2,
            WALL_H // 2 - door_img.get_height() // 2
        ))

        # Buttons
        screen.blit(self.red_btn_img, self.red_btn_rect.topleft)
        screen.blit(self.green_btn_img, self.green_btn_rect.topleft)

        # Medkit
        if self.medkit_visible:
            screen.blit(self.medkit_img, self.medkit_rect.topleft)

        # Player (Tony) – draw sprite centered on the player's collision box bottom
        frame = self.walker.current_frame()
        img_rect = frame.get_rect(midbottom=self.player.midbottom)
        screen.blit(frame, img_rect.topleft)

        # Separator
        pygame.draw.line(screen, (0, 0, 0), (0, WALL_H), (self.win_w, WALL_H), 2)

        # Lighting (soft cone)
        if DEFAULT_DARK_ENABLED:
            origin = self.player.center
            cone_overlay = _make_darkness_cone(
                (self.win_w, self.win_h), DARK_ALPHA, origin,
                self.facing_angle, FOV_DEG, VISION_LENGTH,
                SOFT_EDGE, FEATHER_STEPS
            )
            screen.blit(cone_overlay, (0, 0))