# src/core/scene_runner.py
from __future__ import annotations
import pygame
from typing import Callable, Dict, Any
from dialogue_engine import DialogueRunner, GameVars
from dialog_ui import DialogueBox
from core.config import GENERAL_ASSET_DIR, RIGHT_MARGIN, BUSTSHOT_SCALE

def draw_inline_choices(screen: pygame.Surface, dialog: DialogueBox, options, selected_index: int):
    font = dialog.font

    # Zone utile "intérieure" à la box
    inner_left  = dialog.box_rect.left + dialog.padding_left
    inner_right = dialog.box_rect.right - dialog.padding_right
    inner_w     = max(1, inner_right - inner_left)

    # Helpers ---------------------------------------------------------
    def _truncate_to_fit(text: str) -> str:
        """Raccourcit avec ‘…’ si la ligne dépasse inner_w."""
        if font.size(text)[0] <= inner_w:
            return text
        ell = "…"
        # on garde le plus possible de caractères avant d'ajouter …
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi) // 2
            if font.size(text[:mid] + ell)[0] <= inner_w:
                lo = mid + 1
            else:
                hi = mid
        return (text[:max(0, lo - 1)] + ell) if lo > 0 else ell

    # Prépare chaque surface (avec le ‘> ’ pour l’option sélectionnée)
    rendered = []
    for i, raw_label in enumerate(options):
        label = _truncate_to_fit(raw_label)
        prefix = "> " if i == selected_index else "  "
        color  = (255, 255, 255) if i == selected_index else (190, 190, 190)
        surf   = font.render(prefix + label, True, color)
        rendered.append(surf)

    # Placement : on empile en LIGNES au bas de la boîte, en revenant à la ligne si besoin
    gap_x = 20
    line_h = font.get_height()
    x = inner_left
    y = dialog.box_rect.bottom - dialog.padding_bottom - line_h

    for surf in rendered:
        w, h = surf.get_size()
        if x + w > inner_right:
            # retour à la ligne
            y -= (line_h + 6)
            x = inner_left
        screen.blit(surf, (x, y))
        x += w + gap_x

def run_scene(
    screen: pygame.Surface,
    dialog: DialogueBox,
    scene_def: Dict[str, Any],
    room_factory: Callable[[int, int, GameVars], Any],
    gvars: GameVars,
    fps: int = 60,
    rng_seed: int | None = 42,
) -> None:
    clock = pygame.time.Clock()
    win_w, win_h = screen.get_size()

    runner = DialogueRunner(scene_def, gvars, rng_seed=rng_seed)

    room = room_factory(win_w, win_h, gvars)
    room.layout_for_dialogue(dialog_top=dialog.box_rect.top)

    # -------- Bustshot setup (preload originals once) --------
# -------- Bustshot setup (preload originals once) --------
    def _load_bustshot(name: str, flip_x: bool = True):
        p = GENERAL_ASSET_DIR / name
        try:
            surf = pygame.image.load(str(p)).convert_alpha()
            if flip_x:
                surf = pygame.transform.flip(surf, True, False)
            return surf
        except Exception:
            return None

    bust_tony  = _load_bustshot("tony_bustshot.png", flip_x=True)
    bust_lucas = _load_bustshot("lucas_bustshot.png", flip_x=True)

    def draw_bustshot_if_needed(current_prompt):
        """
        Draws the speaker bustshot above the dialog box, right-aligned,
        with bottom touching the dialog box top and RIGHT_MARGIN from the screen edge.
        """
        if not current_prompt or current_prompt.get("type") != "lines":
            return

        speaker = (current_prompt.get("speaker") or "").strip().lower()
        shot = None
        if speaker == "tony":
            shot = bust_tony
        elif speaker in ("lucas", "lukas"):
            shot = bust_lucas

        if not shot:
            return

        # Target height cannot exceed the available space above the dialog box
        # (bottom of the image aligns with dialog top; 0px gap as requested).
        available_h = max(0, dialog.box_rect.top)
        if available_h <= 0:
            return

        ow, oh = shot.get_size()
        base_h = min(oh, available_h)    
        target_h = max(1, int(round(base_h * BUSTSHOT_SCALE))) 
        target_w = max(1, int(round(ow * (target_h / oh))))
        scaled = pygame.transform.smoothscale(shot, (target_w, target_h))

        r = scaled.get_rect()
        r.bottom = dialog.box_rect.top            # 0px above the dialog box
        r.right  = win_w - RIGHT_MARGIN           # 40px right margin
        screen.blit(scaled, r.topleft)
    # ---------------------------------------------------------

    def on_scene_event_done(evt_name: str):
        nonlocal started_evt
        started_evt = None
        runner.notify_event_done(evt_name)
        refresh_prompt()

    def maybe_start_scene_event():
        nonlocal started_evt
        if runner.is_waiting_for_event():
            evt = runner.waiting_event_name()
            if evt and evt != started_evt:
                started_evt = evt
                room.start_event(evt, on_done=on_scene_event_done)

    show_room = False
    current = runner.get_prompt()
    if current and current["type"] == "lines":
        dialog.set_text(f'{current["speaker"]}: {current["text"]}')

    choice_index = 0
    started_evt: str | None = None  

    def refresh_prompt():
        nonlocal current, show_room, choice_index
        current = runner.get_prompt()
        if current and current["type"] == "lines":
            # same reveal rule you used: show the room once Lukas starts talking
            if not show_room and current.get("speaker") in ("Martha", "Tony"):
                show_room = True
            dialog.set_text(f'{current["speaker"]}: {current["text"]}')
        elif current and current["type"] == "choice":
            choice_index = 0
        maybe_start_scene_event()

    maybe_start_scene_event()

    running = True
    while running:
        dt_ms = clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.event.post(pygame.event.Event(pygame.QUIT))  # propagate to campaign
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return

            if runner.is_waiting_for_event():
                continue

            if current and current["type"] == "lines":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    runner.submit_continue()
                    refresh_prompt()

            elif current and current["type"] == "choice":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        choice_index = max(0, choice_index - 1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        choice_index = min(len(current["options"]) - 1, choice_index + 1)
                    elif event.key == pygame.K_RETURN:
                        runner.submit_choice(choice_index)
                        choice_index = 0
                        refresh_prompt()
        # Si on attend un event, on affiche forcément la room (sinon on verrait un écran noir)
        if runner.is_waiting_for_event():
            show_room = True
            maybe_start_scene_event()  # au cas où on est entré dans wait_scene sans refresh_prompt

        room.update(dt_ms)

        if show_room:
            room.draw(screen)
        else:
            screen.fill((10, 10, 12))

        # Draw bustshot AFTER the room (so lighting doesn't darken it) and BEFORE the dialog box.
        draw_bustshot_if_needed(current)

        if current and current["type"] == "lines":
            dialog.draw(screen, color=(255, 255, 255))
        elif current and current["type"] == "choice":
            dialog.set_text(current["prompt"])
            dialog.draw(screen, color=(255, 255, 255))
            draw_inline_choices(screen, dialog, current["options"], choice_index)

        pygame.display.flip()

        if runner.is_finished():
            return