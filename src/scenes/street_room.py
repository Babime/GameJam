# src/scenes/street_room.py
from __future__ import annotations
from pathlib import Path
import math
import random
import pygame
from typing import Optional, Callable
from core.config import GENERAL_ASSET_DIR
from core.actor_sprite import create_tony_animator

# ----------------- Room Config -----------------
BUILDING_H = 120
ROAD_WIDTH = 200
SIDEWALK_WIDTH = 40
PLAYER_SIZE = 32           # collision box
PLAYER_SPEED = 200         # cinematic speed
SPRITE_DRAW_H = 56         # visual sprite height
CAR_TARGET_W = 80
CAR_TARGET_H = 40
STRANGER_TARGET_H = 50

# Street layout
STREET_SPLIT_Y = 300       # where the street splits into two paths
LEFT_PATH_ANGLE = 45       # degrees for left path (towards police)
RIGHT_PATH_ANGLE = -30     # degrees for right path (towards garage)

# Lighting
DEFAULT_DARK_ENABLED = True
DARK_ALPHA = 180
VISION_LENGTH = 200
FOV_DEG = 60
SOFT_EDGE = True
FEATHER_STEPS = 6

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

# ----------------- Scene -----------------
class StreetRoomScene:
    """
    Street scene with a crossroads: left path leads to police, right path leads to garage with car.
    Tony is AI-driven based on dialogue choices and trust level.
    """
    def __init__(self, win_w: int, win_h: int, street_asset_dir: Path, hud_font_path: Optional[Path], game_vars):
        self.win_w = win_w
        self.win_h = win_h
        self.street_asset_dir = street_asset_dir
        self.gvars = game_vars

        # ----- Load assets -----
        # Street/building textures
        self.asphalt_raw = _load_image(street_asset_dir / "asphalt_tile.png")
        self.sidewalk_raw = _load_image(street_asset_dir / "sidewalk_tile.png")
        self.building_raw = _load_image(street_asset_dir / "building_wall.png")
        
        # Car and stranger
        self.car_raw = _load_image(street_asset_dir / "car_front.png")
        self.stranger_raw = _load_image(street_asset_dir / "stanger_walk_upfront_1.png")
        
        # Scale textures
        self.asphalt_tile = pygame.transform.scale(self.asphalt_raw, (64, 64))
        self.sidewalk_tile = pygame.transform.scale(self.sidewalk_raw, (64, 32))
        self.building_wall = pygame.transform.scale(self.building_raw, (win_w, BUILDING_H))
        
        # Scale objects
        self.car_img = _scale_to_width(self.car_raw, CAR_TARGET_W)
        self.stranger_img = _scale_to_height(self.stranger_raw, STRANGER_TARGET_H)
        
        # Positioning
        self.car_rect = self.car_img.get_rect()
        self.stranger_rect = self.stranger_img.get_rect()
        self.stranger_visible = True
        
        # Set car and stranger positions (garage area - right side)
        garage_x = win_w - 120
        garage_y = win_h - 80
        self.car_rect.center = (garage_x, garage_y)
        self.stranger_rect.midbottom = (garage_x - 30, garage_y + 10)

        # Player (Tony) - collision box
        self.player = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.safe_bottom = self.win_h - 20

        # Sprite animator (4-dir), initially facing up (towards the split)
        self.walker = create_tony_animator(GENERAL_ASSET_DIR, target_height=SPRITE_DRAW_H)
        self._facing_dir = "up"   # 'up','down','left','right'
        self.facing_angle = -90.0 # for lighting cone
        self._moving = False

        # Cinematic event state
        self._event_name: Optional[str] = None
        self._event_phase: Optional[str] = None
        self._event_target = pygame.Vector2(0, 0)
        self._on_event_done: Optional[Callable[[str], None]] = None
        self._event_speed_multiplier = 1.0

        # Wander state
        self._wander_timer_ms: int = 0
        self._wander_dir: int = 1  
        self._wander_speed_scale: float = 0.6  

        # Wait state
        self._wait_timer_ms: int = 0

        # HUD font
        if hud_font_path and Path(hud_font_path).exists():
            self.hud_font = pygame.font.Font(str(hud_font_path), 22)
        else:
            self.hud_font = pygame.font.SysFont("monospace", 18)

        self._place_default_layout()

    # ---------- Layout ----------
    def _place_default_layout(self):
        # Start Tony at bottom center of the street
        self.player.centerx = int(round(pos_x))
        self.player.centery = int(round(pos_y))

    def _update_wander(self, dt_ms: int):
        # Wander around the starting area before going to garage
        speed = PLAYER_SPEED * self._wander_speed_scale
        dx = speed * (dt_ms / 1000.0) * self._wander_dir
        new_x = self.player.centerx + dx

        left_bound = 50
        right_bound = self.win_w - 50

        if new_x <= left_bound:
            new_x = left_bound
            self._wander_dir = 1
        elif new_x >= right_bound:
            new_x = right_bound
            self._wander_dir = -1

        self.player.centerx = int(round(new_x))
        # Keep near bottom during wander
        self.player.bottom = self.safe_bottom

        self._moving = True
        self._set_facing("right" if self._wander_dir > 0 else "left")

        self._wander_timer_ms -= dt_ms
        if self._wander_timer_ms <= 0:
            # Now go to garage
            self._event_phase = "move_to_garage"

    def draw(self, screen: pygame.Surface):
        # Background (night sky)
        screen.fill((15, 20, 35))

        # Draw buildings at top
        screen.blit(self.building_wall, (0, 0))

        # Draw street/road with tiles
        asphalt_w, asphalt_h = self.asphalt_tile.get_size()
        sidewalk_w, sidewalk_h = self.sidewalk_tile.get_size()
        
        # Road surface
        for y in range(BUILDING_H, self.win_h, asphalt_h):
            for x in range(0, self.win_w, asphalt_w):
                screen.blit(self.asphalt_tile, (x, y))

        # Sidewalks on sides
        for y in range(BUILDING_H, self.win_h, sidewalk_h):
            # Left sidewalk
            for x in range(0, SIDEWALK_WIDTH, sidewalk_w):
                screen.blit(self.sidewalk_tile, (x, y))
            # Right sidewalk  
            for x in range(self.win_w - SIDEWALK_WIDTH, self.win_w, sidewalk_w):
                screen.blit(self.sidewalk_tile, (x, y))

        # Draw street markings to show the split
        split_y = STREET_SPLIT_Y
        pygame.draw.line(screen, (200, 200, 100), 
                        (self.win_w // 2, split_y), 
                        (self.win_w // 2, split_y + 50), 3)
        
        # Left arrow (towards police - red)
        left_arrow_points = [
            (self.win_w // 2 - 40, split_y + 30),
            (self.win_w // 2 - 60, split_y + 40),
            (self.win_w // 2 - 40, split_y + 50)
        ]
        pygame.draw.polygon(screen, (200, 50, 50), left_arrow_points)
        
        # Right arrow (towards garage - green) 
        right_arrow_points = [
            (self.win_w // 2 + 40, split_y + 30),
            (self.win_w // 2 + 60, split_y + 40),
            (self.win_w // 2 + 40, split_y + 50)
        ]
        pygame.draw.polygon(screen, (50, 200, 50), right_arrow_points)

        # Draw car
        screen.blit(self.car_img, self.car_rect.topleft)

        # Draw stranger (if visible)
        if self.stranger_visible:
            screen.blit(self.stranger_img, self.stranger_rect.topleft)

        # Draw player (Tony) - only if on screen
        if self.player.centerx > 0 and self.player.centery > 0:
            frame = self.walker.current_frame()
            img_rect = frame.get_rect(midbottom=self.player.midbottom)
            screen.blit(frame, img_rect.topleft)

        # HUD
        hud = self.hud_font.render(
            f"Trust: {self.gvars.trust}   PoliceGap: {self.gvars.police_gap}",
            True, (230, 230, 230)
        )
        screen.blit(hud, (12, 8))

        # Street labels for clarity
        garage_label = self.hud_font.render("GARAGE", True, (100, 200, 100))
        screen.blit(garage_label, (self.win_w - 140, self.win_h - 120))
        
        police_label = self.hud_font.render("DANGER", True, (200, 100, 100))
        screen.blit(police_label, (20, self.win_h - 180))

    def layout_for_dialogue(self, dialog_top: int):
        margin = 8
        self.safe_bottom = max(0, dialog_top - margin)
        self.player.centerx = self.win_w // 2
        self.player.bottom = self.safe_bottom
        self.stranger_visible = True

    # ---------- Scene<->Dialogue bridge ----------
    def start_event(self, event_name: str, on_done: Callable[[str], None]):
        """
        Supported events:
          - 'go_to_garage'       : walk towards the garage (right path)
          - 'wander_then_garage' : wander briefly, then go to garage
          - 'go_to_police'       : walk towards police area (left path) 
          - 'escape_to_garage'   : quick escape run from police to garage
          - 'stealth_to_car'     : sneak carefully to the car
          - 'direct_to_car'      : walk directly to the car
          - 'drive_away'         : get in car and drive off screen
        """
        self._event_name = event_name
        self._on_event_done = on_done
        self._event_speed_multiplier = 1.0

        if event_name == "go_to_garage":
            # Move towards garage area (right side)
            self._event_phase = "move"
            self._event_target = pygame.Vector2(self.win_w - 100, self.win_h - 100)

        elif event_name == "wander_then_garage":
            self._event_phase = "wander"
            self._wander_timer_ms = 2000  # 2 seconds of wandering
            self._wander_dir = 1 if random.random() < 0.5 else -1

        elif event_name == "go_to_police":
            # Move towards left side (police area)
            self._event_phase = "move"
            self._event_target = pygame.Vector2(80, self.win_h - 150)

        elif event_name == "escape_to_garage":
            # Fast escape from police to garage
            self._event_phase = "move"
            self._event_target = pygame.Vector2(self.win_w - 100, self.win_h - 100)
            self._event_speed_multiplier = 1.8  # Faster movement

        elif event_name == "drive_away":
            # Get in car and drive off
            self._event_phase = "enter_car"
            self._event_target = pygame.Vector2(self.car_rect.centerx, self.car_rect.centery)

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
            # idle update
            self.walker.update(self._facing_dir, self._moving, dt_ms)
            return

        if self._event_name == "wander_then_garage":
            if self._event_phase == "wander":
                self._update_wander(dt_ms)
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

            if self._event_name in ["go_to_garage", "escape_to_garage"]:
                if self._distance_to(self._event_target) < 15.0:
                    self._set_facing("right")
                    self._finish_event_immediately()

            elif self._event_name == "go_to_police":
                if self._distance_to(self._event_target) < 15.0:
                    self._set_facing("left")
                    self._finish_event_immediately()

        self.walker.update(self._facing_dir, self._moving, dt_ms)

    # ---- movement helpers ----
    def _distance_to(self, vec: pygame.Vector2) -> float:
        pos = pygame.Vector2(self.player.centerx, self.player.centery)
        return (vec - pos).length()

    def _set_facing(self, dir4: str):
        self._facing_dir = dir4
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
        Move using 4-directional steps with speed multiplier for different movement types
        """
        pos_x, pos_y = self.player.centerx, self.player.centery
        dx = target.x - pos_x
        dy = target.y - pos_y
        base_step = PLAYER_SPEED * (dt_ms / 1000.0) * self._event_speed_multiplier

        # Prioritize horizontal movement first, then vertical
        if abs(dx) > 2:
            move = max(-base_step, min(base_step, dx))
            pos_x += move
            self._moving = True
            self._set_facing("right" if move > 0 else "left")
        elif abs(dy) > 2:
            move = max(-base_step, min(base_step, dy))
            pos_y += move
            self._moving = True
            self._set_facing("down" if move > 0 else "up")

        self.player.centerx