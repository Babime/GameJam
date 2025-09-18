from __future__ import annotations
import pygame
from typing import Callable, Dict, Any
from dialogue_engine import DialogueRunner, GameVars
from dialog_ui import DialogueBox
from core.config import GENERAL_ASSET_DIR, RIGHT_MARGIN, BUSTSHOT_SCALE, FONT_PATH

# ---------- Choice rendering ----------
def draw_inline_choices(screen: pygame.Surface, dialog: DialogueBox, options, selected_index: int):
    font = dialog.font

    # Inner text area
    inner_left  = dialog.box_rect.left + dialog.padding_left
    inner_right = dialog.box_rect.right - dialog.padding_right
    inner_w     = max(1, inner_right - inner_left)

    # Helper: truncate if needed (adds …)
    def _truncate_to_fit(text: str) -> str:
        if font.size(text)[0] <= inner_w:
            return text
        ell = "…"
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi) // 2
            if font.size(text[:mid] + ell)[0] <= inner_w:
                lo = mid + 1
            else:
                hi = mid
        return (text[:max(0, lo - 1)] + ell) if lo > 0 else ell

    # Render each option surface with the selection marker
    rendered = []
    for i, raw_label in enumerate(options):
        label = _truncate_to_fit(raw_label)
        prefix = "> " if i == selected_index else "  "
        color  = (255, 255, 255) if i == selected_index else (190, 190, 190)
        surf   = font.render(prefix + label, True, color)
        rendered.append(surf)

    # Pack into rows (left→right), wrapping when exceeding inner width
    gap_x = 20
    row_gap = 6
    line_h = font.get_height()

    lines: list[list[pygame.Surface]] = [[]]
    cur_w = 0
    for surf in rendered:
        w, _ = surf.get_size()
        if cur_w == 0:
            lines[-1].append(surf)
            cur_w = w
        else:
            if cur_w + gap_x + w > inner_w:
                # new row
                lines.append([surf])
                cur_w = w
            else:
                lines[-1].append(surf)
                cur_w += gap_x + w

    # Compute top y so the whole block stays bottom-aligned in the box
    total_h = len(lines) * line_h + (len(lines) - 1) * row_gap
    y = dialog.box_rect.bottom - dialog.padding_bottom - total_h

    # Draw TOP → BOTTOM so visual order matches reading order
    for line in lines:
        x = inner_left
        for surf in line:
            screen.blit(surf, (x, y))
            x += surf.get_width() + gap_x
        y += line_h + row_gap

# ---------- Central HUD (Trust / PoliceGap) ----------
_HUD_FONT: pygame.font.Font | None = None

def _get_hud_font() -> pygame.font.Font:
    global _HUD_FONT
    if _HUD_FONT is None:
        try:
            _HUD_FONT = pygame.font.Font(str(FONT_PATH), 22)
        except Exception:
            _HUD_FONT = pygame.font.SysFont("monospace", 18)
    return _HUD_FONT

def draw_hud_overlay(screen: pygame.Surface, gvars: GameVars):
    font = _get_hud_font()

    def color_trust(v):
        # Trust : <=40 rouge ; 40<=v<50 orange ; >=50 vert
        if v <= 40:
            return (200, 0, 0)      # rouge
        elif v <= 50:
            return (230, 160, 0)    # orange
        else:
            return (0, 200, 0)      # vert

    def color_police_gap(v):
        # PoliceGap : <=3 rouge ; 3<v<5 orange ; >5 vert
        if v <= 3:
            return (200, 0, 0)      # rouge
        elif v <= 5:
            return (230, 160, 0)    # orange
        else:
            return (0, 200, 0)      # vert

    trust_text  = font.render(f"Trust: {gvars.trust}", True, color_trust(gvars.trust))
    police_text = font.render(f"PoliceGap: {gvars.police_gap}", True, color_police_gap(gvars.police_gap))

    screen.blit(trust_text, (12, 8))
    screen.blit(police_text, (300, 8))  # position demandée


# ---------- Scene runner ----------
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
    def _load_bustshot(name: str, flip_x: bool = True):
        p = GENERAL_ASSET_DIR / name
        try:
            surf = pygame.image.load(str(p)).convert_alpha()
            if flip_x:
                surf = pygame.transform.flip(surf, True, False)
            return surf
        except Exception:
            return None

    bust_tony   = _load_bustshot("tony_bustshot.png",   flip_x=True)
    bust_lucas  = _load_bustshot("lucas_bustshot.png",  flip_x=True)
    bust_martha = _load_bustshot("granny_bustshot.png", flip_x=True)
    bust_stranger = _load_bustshot("stranger_bustshot.png", flip_x=True)

    def draw_bustshot_if_needed(current_prompt):
        if not current_prompt or current_prompt.get("type") != "lines":
            return
        speaker = (current_prompt.get("speaker") or "").strip().lower()
        shot = None
        if speaker == "tony":
            shot = bust_tony
        elif speaker in ("lucas", "lukas"):
            shot = bust_lucas
        elif speaker == "martha":
            shot = bust_martha
        elif speaker == "john":
            shot = bust_stranger
        if not shot:
            return
        available_h = max(0, dialog.box_rect.top)
        if available_h <= 0:
            return
        ow, oh = shot.get_size()
        base_h = min(oh, available_h)
        target_h = max(1, int(round(base_h * BUSTSHOT_SCALE)))
        target_w = max(1, int(round(ow * (target_h / oh))))
        scaled = pygame.transform.smoothscale(shot, (target_w, target_h))
        r = scaled.get_rect()
        r.bottom = dialog.box_rect.top
        r.right  = win_w - RIGHT_MARGIN
        screen.blit(scaled, r.topleft)
    # ---------------------------------------------------------

    # --- Detect if our choice list will be one-per-line (stacked vertically) ---
    def _choices_render_one_per_line(options) -> bool:
        """
        Mirrors draw_inline_choices packing to see if we'll wrap every option to its own line.
        We treat it as 'one-per-line' if the computed number of rows == number of options.
        """
        font = dialog.font
        inner_left  = dialog.box_rect.left + dialog.padding_left
        inner_right = dialog.box_rect.right - dialog.padding_right
        inner_w     = max(1, inner_right - inner_left)
        gap_x = 20

        rows = 1
        line_w = 0
        for raw_label in options:
            # include the "> " prefix width (worst-case) to be safe
            w = font.size("> " + raw_label)[0]
            if line_w == 0:
                line_w = w
            else:
                if line_w + gap_x + w > inner_w:
                    rows += 1
                    line_w = w
                else:
                    line_w += gap_x + w
        return rows == len(options)

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
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return

            if runner.is_waiting_for_event():
                continue

            if current and current["type"] == "lines":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    # First paginate the current long text inside the same bubble
                    done_page = dialog.advance()
                    if done_page:
                        # No more pages for this line -> advance the dialogue graph
                        runner.submit_continue()
                        refresh_prompt()

            elif current and current["type"] == "choice":
                if event.type == pygame.KEYDOWN:
                    options = current["options"]
                    vertical = _choices_render_one_per_line(options)

                    if vertical:
                        # one option per line → use UP/DOWN (W/S also works)
                        if event.key in (pygame.K_UP, pygame.K_w):
                            choice_index = max(0, choice_index - 1)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            choice_index = min(len(options) - 1, choice_index + 1)
                    else:
                        # compact inline menu → use LEFT/RIGHT (A/D also works)
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            choice_index = max(0, choice_index - 1)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            choice_index = min(len(options) - 1, choice_index + 1)

                    if event.key == pygame.K_RETURN:
                        runner.submit_choice(choice_index)
                        choice_index = 0
                        refresh_prompt()

        if runner.is_waiting_for_event():
            show_room = True
            maybe_start_scene_event()

        room.update(dt_ms)

        if show_room:
            room.draw(screen)
        else:
            screen.fill((10, 10, 12))

        draw_bustshot_if_needed(current)

        if current and current["type"] == "lines":
            dialog.draw(screen, color=(255, 255, 255))
        elif current and current["type"] == "choice":
            dialog.set_text(current["prompt"])
            dialog.draw(screen, color=(255, 255, 255))
            draw_inline_choices(screen, dialog, current["options"], choice_index)

        # Always draw the HUD last so it's visible in every scene
        draw_hud_overlay(screen, gvars)

        pygame.display.flip()

        if runner.is_finished():
            return