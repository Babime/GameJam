# src/scenes/scene4_airport.py
import pygame
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import WIDTH, HEIGHT, FPS

PLAYER_SPEED = 150
PLANE_BOARD_TIME = 2.0
GREEN_BAR = (80, 220, 100)

class Entity:
    def __init__(self, x, y, surf):
        self.x, self.y, self.surf = x, y, surf
        self.w, self.h = surf.get_width(), surf.get_height()

    def draw(self, screen):
        screen.blit(self.surf, (self.x, self.y))

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


class Player(Entity):
    def __init__(self, x, y, surf):
        super().__init__(x, y, surf)
        self.speed = PLAYER_SPEED

    def update(self, dt):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if dx and dy:
            dx, dy = dx * 0.7071, dy * 0.7071
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
        self.x = max(0, min(self.x, WIDTH - self.w))
        self.y = max(0, min(self.y, HEIGHT - self.h))


class AirportRoomScene:
    def __init__(self, win_w, win_h, gvars, hud_font_path=None):
        self.win_w, self.win_h = win_w, win_h
        self.gvars = gvars
        self.frozen = False
        self.done = False
        self.board_progress = 0
        self.game_state = "playing"
        self.hud_font = pygame.font.Font(hud_font_path, 24) if hud_font_path else None
        self.caught = False
        self.player_visible = True

        base_path = os.path.dirname(__file__)
        plane_path = os.path.join(base_path, "..", "..", "assets", "general", "avion.png")
        self.plane_image = pygame.image.load(plane_path).convert_alpha()
        self.plane_image = pygame.transform.scale(self.plane_image, (win_w // 4, win_h // 3))
        self.plane_rect = self.plane_image.get_rect(midbottom=(win_w - 200, win_h - 100))

        self.plane_takeoff = False
        self.plane_speed_x = -200   # vers la gauche
        self.plane_speed_y = -150

        player_path = os.path.join(base_path, "..", "..", "assets", "general", "walk_to_his_right_1.png")
        self.player_image = pygame.image.load(player_path).convert_alpha()
        self.player_image = pygame.transform.scale(self.player_image, (32, 48))
        self.player = Player(100, win_h - 100, self.player_image)

        # Police conditionnelle
        self.police_active = (self.gvars.trust < 30) or (self.gvars.police_gap < 70)
        if self.police_active:
            police_path = os.path.join(base_path, "..", "..", "assets", "general", "police_side.png")
            self.police_image = pygame.image.load(police_path).convert_alpha()
            self.police_image = pygame.transform.scale(self.police_image, (64, 32))
            self.police_rect = self.police_image.get_rect(midbottom=(200, win_h - 100))
            self.frozen = False
        else:
            self.police_image = None
            self.police_rect = None

        self.police_speed = 100

    def update(self, dt_ms):
        dt = dt_ms / 1000.0
        if self.done:
            return

        # Déplacement joueur si pas gelé
        if not self.frozen and self.player_visible:
            self.player.update(dt)

        # Détecte si Tony est proche de l'avion
        if not self.police_active and self.player.rect().colliderect(self.plane_rect):
            keys = pygame.key.get_pressed()
            if keys[pygame.K_e]:
                self.board_progress += dt
            else:
                self.board_progress += dt * 0.4

            if self.board_progress >= PLANE_BOARD_TIME:
                self.game_state = "escape"
                self.plane_takeoff = True
                self.frozen = True
                self.player_visible = False  # Tony disparaît
                # Optionnel: placer Tony sur l'avion
                self.player_visible = False
                self.player.x = self.plane_rect.centerx - self.player.w // 2
                self.player.y = self.plane_rect.bottom - self.player.h
        else:
            self.board_progress = max(0, self.board_progress - dt * 1.5)

        # Animation avion
        if self.plane_takeoff:
            self.plane_rect.x += self.plane_speed_x * dt
            self.plane_rect.y += self.plane_speed_y * dt
            if self.plane_rect.bottom < 0 or self.plane_rect.right < 0:
                self.done = True

        # Police qui approche
        if self.police_active and self.police_rect:
            dx = self.player.x - self.police_rect.x
            dy = self.player.y - self.police_rect.y
            dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
            self.police_rect.x += (dx / dist) * self.police_speed * dt
            self.police_rect.y += (dy / dist) * self.police_speed * dt

            if self.police_rect.colliderect(self.player.rect()):
                self.frozen = True
                self.caught = True

    def draw(self, screen):
        # décor
        for y in range(0, HEIGHT, 8):
            shade = 20 + (y // 8) * 2
            pygame.draw.rect(screen, (15, 15, 40 + shade), (0, y, WIDTH, 8))

        random.seed(1)
        for bx in range(0, WIDTH, 120):
            bw = 80
            bh = random.randint(120, 220)
            bx_pos = bx + 20
            by_pos = 380 - bh
            pygame.draw.rect(screen, (30, 30, 50), (bx_pos, by_pos, bw, bh))
            for wx in range(bx_pos + 5, bx_pos + bw - 5, 12):
                for wy in range(by_pos + 5, by_pos + bh - 5, 14):
                    if random.random() < 0.4:
                        pygame.draw.rect(screen, (255, 240, 150), (wx, wy, 6, 8))

        pygame.draw.polygon(screen, (40, 20, 60),
                            [(0, 380), (150, 300), (300, 380), (450, 280),
                             (650, 360), (800, 300), (960, 370),
                             (960, HEIGHT), (0, HEIGHT)])
        pygame.draw.rect(screen, (30, 80, 40), (0, HEIGHT - 200, WIDTH, 200))
        pygame.draw.rect(screen, (60, 60, 60), (0, HEIGHT - 120, WIDTH, 120))
        for x in range(0, WIDTH, 80):
            pygame.draw.rect(screen, (200, 200, 200), (x + 20, HEIGHT - 80, 40, 6))
        for x in [120, 300, 500, 720, 880]:
            pygame.draw.rect(screen, (100, 60, 30), (x, HEIGHT - 200, 16, 40))
            pygame.draw.circle(screen, (20, 100, 40), (x + 8, HEIGHT - 210), 30)

        # entités
        screen.blit(self.plane_image, self.plane_rect)
        if self.player_visible:
            self.player.draw(screen)
        if self.police_image and self.police_rect:
            screen.blit(self.police_image, self.police_rect)

        # HUD
        if self.hud_font:
            hud = self.hud_font.render(f"Board: {int(self.board_progress*100/PLANE_BOARD_TIME)}%", True, (255, 255, 255))
            screen.blit(hud, (10, 10))
        pygame.draw.rect(screen, (50, 50, 50), (8, HEIGHT - 36, 200, 24))
        pygame.draw.rect(screen, GREEN_BAR,
                         (8, HEIGHT - 36, int(200 * (self.board_progress / PLANE_BOARD_TIME)), 24))

        # messages fin
        font = pygame.font.Font(None, 64)
        if getattr(self, "caught", False):
            text = font.render("He did not escape", True, (255, 0, 0))
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))
        elif self.plane_takeoff and not self.player_visible:
            text = font.render("He did escape", True, (0, 255, 0))
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2))


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Test Airport Scene")

    # gvars test pour permettre l'évasion
    class DummyGVars:
        trust = 100
        police_gap = 1000

    gvars = DummyGVars()
    scene = AirportRoomScene(WIDTH, HEIGHT, gvars)

    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        scene.update(dt)
        screen.fill((0, 0, 0))
        scene.draw(screen)
        pygame.display.flip()
