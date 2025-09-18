from __future__ import annotations
from pathlib import Path
import pygame

def _load(path: Path) -> pygame.Surface:
    return pygame.image.load(str(path)).convert_alpha()

def _scale_to_height(img: pygame.Surface, target_h: int) -> pygame.Surface:
    w, h = img.get_size()
    if h == 0:
        return img
    new_w = max(1, int(round(w * (target_h / h))))
    return pygame.transform.scale(img, (new_w, target_h))

class FourDirWalker:
    """
    Minimal 4-direction (up/down/left/right) 2-frame walk animator.
    - frames: dict[str, list[Surface]] with keys: 'up','down','left','right'
              each list should contain 1–2 frames; if only 1, it will be used as idle and walk.
    - frame_ms: how long each walking frame is shown
    """
    def __init__(self, frames: dict[str, list[pygame.Surface]], frame_ms: int = 140):
        self.frames = frames
        self.frame_ms = frame_ms
        self.timer = 0
        self.index = 0
        self.facing = "down"
        self.moving = False

        # Guarantee at least 1 frame per direction
        for k in ("up", "down", "left", "right"):
            if k not in self.frames or not self.frames[k]:
                raise ValueError(f"Missing animation frames for direction '{k}'")
            if len(self.frames[k]) == 1:
                # duplicate idle as walk
                self.frames[k] = [self.frames[k][0], self.frames[k][0]]

    def update(self, facing: str, moving: bool, dt_ms: int):
        if facing:
            self.facing = facing
        self.moving = moving

        if not self.moving:
            self.index = 0
            self.timer = 0
            return

        self.timer += dt_ms
        while self.timer >= self.frame_ms:
            self.timer -= self.frame_ms
            self.index = (self.index + 1) % len(self.frames[self.facing])

    def current_frame(self) -> pygame.Surface:
        return self.frames[self.facing][self.index]

def create_tony_animator(general_asset_dir: Path, target_height: int = 56) -> FourDirWalker:
    """
    Build Tony's 4-dir walk from your PNGs in assets/general:
      - up    : walk_facing_back_{1,2}.png
      - down  : walk_upfront_{1,2}.png
      - right : walk_to_his_right_{1,2}.png
      - left  : use horizontally flipped 'right' frames
    We scale all frames to the same *height* so mismatched source sizes "just work".
    """
    up1    = _scale_to_height(_load(general_asset_dir / "walk_facing_back_1.png"), target_height)
    up2    = _scale_to_height(_load(general_asset_dir / "walk_facing_back_2.png"), target_height)
    down1  = _scale_to_height(_load(general_asset_dir / "walk_upfront_1.png"),    target_height)
    down2  = _scale_to_height(_load(general_asset_dir / "walk_upfront_2.png"),    target_height)
    right1 = _scale_to_height(_load(general_asset_dir / "walk_to_his_right_1.png"), target_height)
    right2 = _scale_to_height(_load(general_asset_dir / "walk_to_his_right_2.png"), target_height)
    left1  = pygame.transform.flip(right1, True, False)
    left2  = pygame.transform.flip(right2, True, False)

    frames = {
        "up":    [up1, up2],
        "down":  [down1, down2],
        "right": [right1, right2],
        "left":  [left1, left2],
    }
    return FourDirWalker(frames, frame_ms=140)

# --- Grand-mère & Voiture de police (mêmes conventions que Tony) ---

def create_grandma_animator(general_asset_dir: Path, target_height: int = 54) -> FourDirWalker:
    """
    Grand-mère 4 directions, 2 frames/direction.
    Fichiers:
      - up    : granny_walk_facing_back_1.png,  granny_walk_facing_back_2.png
      - down  : granny_walk_upfront_1.png,      granny_walk_upfront_2.png
      - right : granny_walk_to_his_right_1.png, granny_walk_to_his_right_2.png
      - left  : flip horizontal des frames right (comme Tony)
    """
    up1    = _scale_to_height(_load(general_asset_dir / "granny_walk_facing_back_1.png"), target_height)
    up2    = _scale_to_height(_load(general_asset_dir / "granny_walk_facing_back_2.png"), target_height)
    down1  = _scale_to_height(_load(general_asset_dir / "granny_walk_upfront_1.png"),    target_height)
    down2  = _scale_to_height(_load(general_asset_dir / "granny_walk_upfront_2.png"),    target_height)
    right1 = _scale_to_height(_load(general_asset_dir / "granny_walk_to_his_right_1.png"), target_height)
    right2 = _scale_to_height(_load(general_asset_dir / "granny_walk_to_his_right_2.png"), target_height)
    left1  = pygame.transform.flip(right1, True, False)
    left2  = pygame.transform.flip(right2, True, False)

    frames = {"up":[up1,up2], "down":[down1,down2], "right":[right1,right2], "left":[left1,left2]}
    return FourDirWalker(frames, frame_ms=140)  # cadence identique à Tony


def create_police_animator(general_asset_dir: Path, target_height: int = 56) -> FourDirWalker:
    """
    Voiture de police (gauche/droite pour l’instant).
    - right : police_side.png (dupliquée pour 2 frames)
    - left  : flip de right
    - up/down : placeholders = right (jamais utilisés si L/R seulement)
    """
    side = _scale_to_height(_load(general_asset_dir / "police_side.png"), target_height)
    right1 = side
    right2 = side
    left1  = pygame.transform.flip(right1, True, False)
    left2  = pygame.transform.flip(right2, True, False)
    frames = {
        "up":[right1,right2], "down":[right1,right2],
        "right":[right1,right2], "left":[left1,left2]
    }
    return FourDirWalker(frames, frame_ms=140)

def create_car_animator(general_asset_dir: Path, target_height: int = 56) -> FourDirWalker:
    """
    Car (proper orientation):
      - down : car_front.png     (car coming toward screen/bottom)
      - up   : car_back.png      (car going upward/away)
      - left : car_side.png      (asset faces left)
      - right: flipped(car_side) (so it faces right)
    """
    # Down uses FRONT
    down1 = _scale_to_height(_load(general_asset_dir / "car_front.png"), target_height)
    down2 = down1  # duplicate for simple 2-frame loop

    # Up uses BACK
    up1 = _scale_to_height(_load(general_asset_dir / "car_back.png"), target_height)
    up2 = up1

    # Side asset faces LEFT by default
    left1 = _scale_to_height(_load(general_asset_dir / "car_side.png"), target_height)
    left2 = left1

    # RIGHT is a flipped LEFT
    right1 = pygame.transform.flip(left1, True, False)
    right2 = pygame.transform.flip(left2, True, False)

    frames = {
        "up":    [up1, up2],
        "down":  [down1, down2],
        "left":  [left1, left2],
        "right": [right1, right2],
    }
    return FourDirWalker(frames, frame_ms=140)