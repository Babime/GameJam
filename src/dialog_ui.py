# dialog_ui.py
import os
from pathlib import Path
import pygame

TILE = 16

def _to_str(p) -> str:
    return str(p) if isinstance(p, (Path,)) else p

def load_image(path):
    path = _to_str(path)
    img = pygame.image.load(path).convert_alpha()
    return img

class TiledBoxRenderer:
    def __init__(self, corner_img_path, edge_img_path, tile_size: int = TILE):
        self.tile = tile_size
        corner_raw = load_image(corner_img_path)
        edge_raw   = load_image(edge_img_path)
        # scale both to tile size with nearest neighbor
        self.corner = pygame.transform.scale(corner_raw, (self.tile, self.tile))
        self.edge   = pygame.transform.scale(edge_raw,   (self.tile, self.tile))

        # Pre-rotations
        self.corner_bl = self.corner
        self.corner_br = pygame.transform.rotate(self.corner_bl, -90)
        self.corner_tr = pygame.transform.rotate(self.corner_bl, -180)
        self.corner_tl = pygame.transform.rotate(self.corner_bl, -270)

        self.edge_top    = self.edge
        self.edge_right  = pygame.transform.rotate(self.edge, -90)
        self.edge_bottom = pygame.transform.rotate(self.edge, -180)
        self.edge_left   = pygame.transform.rotate(self.edge, -270)

    def draw(self, surface: pygame.Surface, rect: pygame.Rect, fill_color=(34, 34, 34)):
        x, y, w, h = rect
        t = self.tile
        if w < t * 2 or h < t * 2:
            return

        # Fill interior (inside borders)
        inner = pygame.Rect(x + t, y + t, w - 2 * t, h - 2 * t)
        pygame.draw.rect(surface, fill_color, inner)

        # Corners
        surface.blit(self.corner_tl, (x, y))
        surface.blit(self.corner_tr, (x + w - t, y))
        surface.blit(self.corner_bl, (x, y + h - t))
        surface.blit(self.corner_br, (x + w - t, y + h - t))

        # Edges horizontal
        for ix in range(x + t, x + w - t, t):
            surface.blit(self.edge_top, (ix, y))
            surface.blit(self.edge_bottom, (ix, y + h - t))

        # Edges vertical
        for iy in range(y + t, y + h - t, t):
            surface.blit(self.edge_left, (x, iy))
            surface.blit(self.edge_right, (x + w - t, iy))

def wrap_text(text: str, font: pygame.font.Font, max_width: int):
    words = text.split()
    lines, line = [], ""
    for w in words:
        cand = w if not line else f"{line} {w}"
        if font.size(cand)[0] <= max_width:
            line = cand
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines

class DialogueBox:
    """
    Handles:
      - computing the box rect from font/line-height + paddings (3 lines/page)
      - wrapping & paginating text (3 lines/page)
      - drawing the tile-built box and current lines
    """
    def __init__(
        self,
        screen_w: int,
        screen_h: int,
        font_path,
        font_size: int,
        line_height_factor: float,
        padding_left: int,
        padding_right: int,
        padding_top: int,
        padding_bottom: int,
        corner_img_path,
        edge_img_path,
        tile: int = TILE,
        fill_color=(34, 34, 34)
    ):
        self.tile = tile
        self.fill_color = fill_color
        self.padding_left   = padding_left
        self.padding_right  = padding_right
        self.padding_top    = padding_top
        self.padding_bottom = padding_bottom

        font_path = _to_str(font_path)
        try:
            self.font = pygame.font.Font(font_path, font_size)
        except FileNotFoundError:
            # Fall back to a system font so the game runs even if the TTF is missing
            self.font = pygame.font.SysFont("monospace", font_size)

        self.font_h = self.font.get_height()
        self.line_gap = int(round(self.font_h * line_height_factor)) - self.font_h
        self.lines_per_page = 3

        self.renderer = TiledBoxRenderer(corner_img_path, edge_img_path, tile_size=self.tile)

        self._lines = []
        self.i_top = 0 

        self.box_rect = pygame.Rect(0, 0, 0, 0)
        self.text_left = 0
        self.text_right = 0
        self.text_top = 0
        self.text_width = 0

        self.layout(screen_w, screen_h)

    def layout(self, screen_w: int, screen_h: int):
        inner_text_h = self.lines_per_page * self.font_h + (self.lines_per_page - 1) * self.line_gap
        inner_total_h = self.padding_top + inner_text_h + self.padding_bottom

        # Total box height includes top+bottom borders; snap to TILE
        box_h = self.tile + inner_total_h + self.tile
        box_h = ((box_h + self.tile - 1) // self.tile) * self.tile

        box_w = (screen_w // self.tile) * self.tile
        box_x = (screen_w - box_w) // 2
        box_y = screen_h - box_h
        self.box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        # Text region (inside borders + paddings)
        self.text_left  = self.box_rect.left + self.tile + self.padding_left
        self.text_right = self.box_rect.right - self.tile - self.padding_right
        self.text_top   = self.box_rect.top + self.tile + self.padding_top
        self.text_width = max(0, self.text_right - self.text_left)

        # If we already had text, rewrap to the new width
        if self._lines:
            joined = " ".join(self._lines)
            self._lines = wrap_text(joined, self.font, self.text_width)
            self.i_top = 0

    def set_text(self, text: str):
        self._lines = wrap_text(text, self.font, self.text_width)
        self.i_top = 0

    def advance(self) -> bool:
        """Advance to next page (3 lines). Returns True if we reached the end and should close."""
        if (self.i_top + self.lines_per_page) >= len(self._lines):
            return True  # done
        self.i_top += self.lines_per_page
        return False

    def draw(self, surface: pygame.Surface, color=(255, 255, 255)):
        """Draw the box and up to 3 current lines."""
        self.renderer.draw(surface, self.box_rect, fill_color=self.fill_color)

        y = self.text_top
        for i in range(self.lines_per_page):
            idx = self.i_top + i
            if 0 <= idx < len(self._lines):
                surf = self.font.render(self._lines[idx], True, color)
                surface.blit(surf, (self.text_left, y))
                if i < self.lines_per_page - 1:
                    y += self.font_h + self.line_gap
            else:
                break