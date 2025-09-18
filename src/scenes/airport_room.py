import pygame

class AirportRoomScene:
    def __init__(self, win_w, win_h, hud_font_path, game_vars):
        self.win_w = win_w
        self.win_h = win_h
        self.gvars = game_vars
        self.hud_font = pygame.font.Font(hud_font_path, 24)
        self.freeze = True  # on commence en pause tant que le dialogue n’est pas fini
        self.done = False
        self.always_show = True


    def layout_for_dialogue(self, dialog_top):
        self.dialog_top = dialog_top

    def start_event(self, evt_name, on_done=None):
        if evt_name == "end_dialogue":
            self.freeze = False
            if on_done:
                on_done(evt_name)

    def update(self, dt_ms):
        if self.freeze:
            return
        # Ici tu peux animer une voiture de police ou un avion
        # pour simuler la course-poursuite / évasion

    def draw(self, screen):
        screen.fill((20, 20, 40))
        hud = self.hud_font.render(
            f"Trust: {self.gvars.trust} | Police gap: {self.gvars.police_gap}",
            True,
            (255, 255, 255)
        )
        screen.blit(hud, (20, 20))

        if self.done:
            # gros message de fin
            font_big = pygame.font.Font(None, 64)
            if self.gvars.trust < 40 or self.gvars.police_gap < 0:
                text = "HE DID NOT ESCAPE"
                color = (200, 50, 50)
            else:
                text = "HE DID ESCAPE"
                color = (50, 200, 50)
            surf = font_big.render(text, True, color)
            rect = surf.get_rect(center=(self.win_w//2, self.win_h//2))
            screen.blit(surf, rect)
