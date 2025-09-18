# src/scenes/scene4_airport.py
import pygame
import math
import os
import random
from src.core.config import WIDTH, HEIGHT, FPS

# --- CONFIG ---
PLAYER_SPEED = 150
POLICE_SPEED = 80
CHASE_SPEED = 140
POLICE_DETECT_RADIUS = 140
PLANE_BOARD_TIME = 2.0

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 40, 40)
POLICE_BLUE = (20, 50, 120)
GREEN_BAR = (80, 220, 100)


# --- ENTITIES ---
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


# --- ROOM CLASS ---
class AirportRoomScene:

    
    def __init__(self, win_w, win_h, gvars):
        self.win_w, self.win_h = win_w, win_h
        self.gvars = gvars
        self.frozen = True

        # Charger images
        base_path = os.path.dirname(__file__)

        plane_path = os.path.join(base_path, "..", "..", "assets", "general", "avion.png")
        self.plane_image = pygame.image.load(plane_path).convert_alpha()
        self.plane_image = pygame.transform.scale(self.plane_image, (win_w // 4, win_h // 3))
        self.plane_rect = self.plane_image.get_rect(midbottom=(win_w - 200, win_h - 100))

        player_path = os.path.join(base_path, "..", "..", "assets", "general", "walk_to_his_right_1.png")
        self.player_image = pygame.image.load(player_path).convert_alpha()
        self.player_image = pygame.transform.scale(self.player_image, (32, 48))
        self.player = Player(100, win_h - 100, self.player_image)

        #  Voiture de police
        police_path = os.path.join(base_path, "..", "..", "assets", "general", "police_side.png")
        self.police_image = pygame.image.load(police_path).convert_alpha()
        self.police_image = pygame.transform.scale(self.police_image, (64, 32))
        self.police_rect = self.police_image.get_rect(midbottom=(200, win_h - 100))
        self.board_progress = 0
        self.game_state = "playing"

    def layout_for_dialogue(self, dialog_top: int):
         """
        Appelé par scene_runner pour placer ton décor / caméra
        en fonction de la boîte de dialogue. Ici on ne fait rien
        de spécial mais on garde la signature pour compatibilité.
        """
         self.dialog_top = dialog_top

    def update(self, dt_ms):
        dt = dt_ms / 1000.0
        
        if self.frozen: 
           return
        if self.game_state == "playing":
            self.player.update(dt)
            if self.player.rect().colliderect(self.plane_rect):
                keys = pygame.key.get_pressed()
                if keys[pygame.K_e]:
                    self.board_progress += dt
                else:
                    self.board_progress += dt * 0.4
                if self.board_progress >= PLANE_BOARD_TIME:
                    self.game_state = "escape"
            else:
                self.board_progress = max(0, self.board_progress - dt * 1.5)

    def draw(self, screen):
        # --- décor ---
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

        # avion
        screen.blit(self.plane_image, self.plane_rect)

        # joueur
        self.player.draw(screen)

        # voiture de police
        screen.blit(self.police_image, self.police_rect)


        # HUD
        pygame.draw.rect(screen, (50, 50, 50), (8, HEIGHT - 36, 200, 24))
        pygame.draw.rect(screen, GREEN_BAR,
                         (8, HEIGHT - 36, int(200 * (self.board_progress / PLANE_BOARD_TIME)), 24))
        
# --- Dialogue scenes for the airport ---

SCENE_AIRPORT_CAUGHT = {
    "id": "airport_caught",
    "start": "intro",
    "nodes": {
        "intro": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony arrive à l’aéroport, haletant, fatigué, blessé…",
            "next": "caught_police"
        },
        "caught_police": {
            "type": "line",
            "speaker": "Police",
            "text": "Arrête-toi Tony ! Tu es en état d’arrestation !",
            "next": "end"
        },
        "end": { "type": "end" }
    }
}

SCENE_AIRPORT_ESCAPED = {
    "id": "airport_escaped",
    "start": "intro",
    "nodes": {
        "intro": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony parvient à atteindre l’avion et monte à bord, échappant de justesse à la police.",
            "next": "end"
        },
        "end": { "type": "end" }
    }
}

        
__all__ = ["AirportRoomScene", "SCENE_AIRPORT_CAUGHT", "SCENE_AIRPORT_ESCAPED"]


"""test """
if __name__ == "__main__":
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # objet gvars factice pour tester
    class DummyGVars: pass
    gvars = DummyGVars()

    room = AirportRoomScene(WIDTH, HEIGHT, gvars)
    room.frozen = False  # pour activer update()

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        room.update(dt)
        room.draw(screen)
        pygame.display.flip()

    pygame.quit()
