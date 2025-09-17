# src/core/scene_runner.py
from __future__ import annotations
import pygame
from typing import Callable, Dict, Any
from dialogue_engine import DialogueRunner, GameVars
from dialog_ui import DialogueBox

def draw_inline_choices(screen: pygame.Surface, dialog: DialogueBox, options, selected_index: int):
    font = dialog.font
    parts = []
    for i, label in enumerate(options):
        prefix = "> "
        color = (255, 255, 255) if i == selected_index else (190, 190, 190)
        parts.append(font.render(prefix + label, True, color))

    gap = 36
    total_w = sum(s.get_width() for s in parts) + gap * (len(parts) - 1)
    x = dialog.box_rect.centerx - total_w // 2
    # use dialog’s own padding_bottom so this draws correctly for all scenes
    y = dialog.box_rect.bottom - dialog.padding_bottom - font.get_height()

    for surf in parts:
        screen.blit(surf, (x, y))
        x += surf.get_width() + gap

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

    def on_scene_event_done(evt_name: str):
        runner.notify_event_done(evt_name)
        refresh_prompt()

    def maybe_start_scene_event():
        if runner.is_waiting_for_event():
            evt = runner.waiting_event_name()
            room.start_event(evt, on_done=on_scene_event_done)

    show_room = False
    current = runner.get_prompt()
    if current and current["type"] == "lines":
        dialog.set_text(f'{current["speaker"]}: {current["text"]}')

    choice_index = 0

    def refresh_prompt():
        nonlocal current, show_room, choice_index
        current = runner.get_prompt()
        if current and current["type"] == "lines":
            # same reveal rule you used: show the room once Lukas starts talking
            if not show_room and current.get("speaker") == "Lukas":
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

        room.update(dt_ms)

        if show_room:
            room.draw(screen)
        else:
            screen.fill((10, 10, 12))

        if current and current["type"] == "lines":
            dialog.draw(screen, color=(255, 255, 255))
        elif current and current["type"] == "choice":
            dialog.set_text(current["prompt"])
            dialog.draw(screen, color=(255, 255, 255))
            draw_inline_choices(screen, dialog, current["options"], choice_index)

        pygame.display.flip()

        if runner.is_finished():
            return