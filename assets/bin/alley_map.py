import pygame
import sys

# --- CONFIG ---
TILE_SIZE = 32
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

# Map simple : -1 = vide, sinon index du tile dans la liste
# Ici j'ai inventé une petite map avec une bifurcation en V
# Tu devras ajuster les index en fonction de ton tileset
game_map = [
    [-1, -1,  1,  1,  1, -1, -1],
    [-1,  0,  0,  0,  0,  2, -1],
    [ 3,  0,  7,  8,  9,  0,  4],
    [-1,  5,  0,  6,  0,  5, -1],
    [-1, -1,  0,  0,  0, -1, -1],
]

# --- INIT ---
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("back_alley_scene")

# Charger tileset (assure-toi de renommer le fichier correctement)
tileset = pygame.image.load("assets/bin/tileset.png").convert_alpha()

# Extraire tiles
tiles = []
tileset_width = tileset.get_width() // TILE_SIZE
tileset_height = tileset.get_height() // TILE_SIZE

for y in range(tileset_height):
    for x in range(tileset_width):
        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        image.blit(tileset, (0, 0), rect)
        tiles.append(image)

# --- Player ---
player = pygame.Rect(100, 100, TILE_SIZE, TILE_SIZE)
player_color = (255, 200, 0)
speed = 3

# --- Functions ---
def draw_map():
    for y, row in enumerate(game_map):
        for x, tile_index in enumerate(row):
            if tile_index != -1:
                screen.blit(tiles[tile_index], (x * TILE_SIZE, y * TILE_SIZE))

def draw_player():
    pygame.draw.rect(screen, player_color, player)

# --- Main Loop ---
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Touches
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        player.y -= speed
    if keys[pygame.K_DOWN]:
        player.y += speed
    if keys[pygame.K_LEFT]:
        player.x -= speed
    if keys[pygame.K_RIGHT]:
        player.x += speed

    # Affichage
    screen.fill((30, 30, 30))
    draw_map()
    draw_player()
    pygame.display.flip()
    clock.tick(60)
