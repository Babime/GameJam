# src/scenes/airport_room.py
import os
import random
import pygame
from core.config import WIDTH, HEIGHT

# =========================
# Tunables
# =========================
# Car horizontal
CAR_START_X: float | None = None   # None -> auto off-screen left (−car.w − 20)
CAR_STOP_X:  float | None = None   # None -> spawn_x + 40 (where it brakes in intro)

# Car vertical
CAR_BOTTOM_Y: float | None = None
CAR_Y  = 600

# Plane placement
PLANE_START_X = 980
PLANE_START_Y = 550
ALIGN_PLANE_TO_CAR_BASELINE = False

# Tony spawn relative to the car
TONY_SPAWN_RIGHT_OF_CAR = True
TONY_SPAWN_OFFSET_X = 60

# Tony “board/disappear” point
TONY_BOARD_X: float | None = None
TONY_BOARD_Y: float | None = None

# Plane climb behavior
PLANE_CLIMB_TRIGGER_FRACTION = 0.50  # starts climbing when plane center crosses this screen fraction
PLANE_CLIMB_SPEED = 140.0            # px/s upward while climbing

# Ground line control
GROUND_Y_FROM_BOTTOM = 100

# --- Police cars (spawn when the plane starts climbing) ---
POLICE_IMG_PATH = ("assets/general/police_side.png")  # faces LEFT
POLICE_SCALE_FACTOR = 1.0 / 2.5                        # match the hero car scale

# Left-side police (moves LEFT)
POLICE1_START_X: float | None = None  # None => just off left edge (-w - 20)
POLICE1_Y = 650
POLICE1_END_X = 400                  # where it stops
POLICE1_SPEED = 460.0                 # px/s

# Right-side police #2 (moves RIGHT)
POLICE2_START_X: float | None = None  # None => just off right edge (win_w + 20)
POLICE2_Y = 650
POLICE2_END_X = WIDTH - 400
POLICE2_SPEED = 460.0

# Right-side police #3 (moves RIGHT)
POLICE3_START_X: float | None = None
POLICE3_Y = 600
POLICE3_END_X = WIDTH - 450
POLICE3_SPEED = 520.0

# ------------ Tiny helpers ------------
def _load(path):
    return pygame.image.load(path).convert_alpha()

class Entity:
    def __init__(self, x, y, surf: pygame.Surface):
        self.x, self.y = float(x), float(y)
        self.surf = surf

    @property
    def w(self): return self.surf.get_width()
    @property
    def h(self): return self.surf.get_height()

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, screen):
        screen.blit(self.surf, (int(self.x), int(self.y)))

class PoliceCar(Entity):
    """One-direction straight-line mover until reaching end_x."""
    def __init__(self, x, y, surf, speed, going_right: bool, end_x: float):
        super().__init__(x, y, surf)
        self.speed = float(speed)
        self.going_right = bool(going_right)
        self.end_x = float(end_x)
        self.active = True

    def update(self, dt: float):
        if not self.active:
            return
        dx = self.speed * dt * (1.0 if self.going_right else -1.0)
        self.x += dx
        # stop at end_x
        if self.going_right and self.x >= self.end_x:
            self.x = self.end_x
            self.active = False
        elif (not self.going_right) and self.x <= self.end_x:
            self.x = self.end_x
            self.active = False

# ------------ Airport room (cinematic-only) ------------
class AirportRoomScene:
    """
    Car drives in → Tony appears → Tony runs to plane → disappears
    → plane taxis left, accelerates, then climbs; exactly when climb starts,
      3 police cars arrive (1 from left going left, 2 from right going right).

    Alt (caught) variant:
      - police spawn ~1s earlier than the climb trigger
      - plane does NOT climb; it stops exactly at the trigger point
    """
    def __init__(self, win_w, win_h, gvars, hud_font_path=None):
        self.win_w, self.win_h = win_w, win_h
        self.gvars = gvars

        # --- Art assets ---
        base = os.path.dirname(__file__)

        # Plane
        plane_path_1 = os.path.join(base, "..", "..", "assets", "general", "avion.png")
        plane_path_2 = os.path.join(base, "..", "..", "assets", "general", "plane.png")
        plane_path = plane_path_1 if os.path.exists(plane_path_1) else plane_path_2
        plane = _load(plane_path)
        plane = pygame.transform.scale(plane, (win_w // 4, win_h // 3))
        self.plane = Entity(0, 0, plane)

        # Default plane anchor before overrides
        plane_rect = plane.get_rect(midbottom=(win_w - 200, win_h - 100))
        self.plane.x, self.plane.y = float(plane_rect.x), float(plane_rect.y)

        # Car
        car_path = os.path.join(base, "..", "..", "assets", "airport", "car_side.png")
        car_img = _load(car_path)
        car_img = pygame.transform.flip(car_img, True, False)
        car_img = pygame.transform.smoothscale(
            car_img,
            (max(1, int(car_img.get_width() * POLICE_SCALE_FACTOR)),
             max(1, int(car_img.get_height() * POLICE_SCALE_FACTOR)))
        )
        self.car = Entity(-car_img.get_width(), 0, car_img)

        # Tony sprites
        gen = os.path.join(base, "..", "..", "assets", "general")
        self.tony_front    = _load(os.path.join(gen, "walk_upfront_1.png"))
        self.tony_walk_r_1 = _load(os.path.join(gen, "walk_to_his_right_1.png"))
        self.tony_walk_r_2 = _load(os.path.join(gen, "walk_to_his_right_2.png"))

        def _scale_h(img, h=48):
            w0, h0 = img.get_size()
            if h0 == 0: return img
            w = max(1, int(round(w0 * (h / h0))))
            return pygame.transform.scale(img, (w, h))

        self.tony_front     = _scale_h(self.tony_front,   48)
        self.tony_walk_r_1  = _scale_h(self.tony_walk_r_1,48)
        self.tony_walk_r_2  = _scale_h(self.tony_walk_r_2,48)

        self.tony = Entity(0, 0, self.tony_front)
        self.tony_visible = False

        # Police art (base faces LEFT; flip for right-going)
        police_raw = _load(POLICE_IMG_PATH)
        police_raw = pygame.transform.smoothscale(
            police_raw,
            (max(1, int(police_raw.get_width() * POLICE_SCALE_FACTOR)),
             max(1, int(police_raw.get_height() * POLICE_SCALE_FACTOR)))
        )
        self._police_left_img = police_raw
        self._police_right_img = pygame.transform.flip(police_raw, True, False)

        # Active police cars list (spawned at climb/alt trigger)
        self.police: list[PoliceCar] = []
        self._spawned_police = False

        # Ground / spawn anchors
        self.spawn_x = 100
        self.spawn_y = win_h - GROUND_Y_FROM_BOTTOM
        self._place_initial()

        # Cinematic state
        self._evt = None
        self._evt_cb = None
        self._phase = None
        self._timer = 0.0

        self.done = True
        self.frozen = False

        # Simple 2-frame animation timers
        self._anim_timer = 0.0
        self._anim_index = 0

        # Plane taxi
        self._plane_taxi_speed = 50.0
        self._plane_taxi_accel = 35.0
        self._plane_taxi_speed_max = 420.0
        self._plane_climb_speed = float(PLANE_CLIMB_SPEED)
        self._plane_started_climb = False

        # --- Caught-variant switches/state ---
        self._caught_variant = False   # set by event "airport_run_caught"
        self._plane_brake = False      # braking active
        self._plane_stop_cx = None     # screen-center X where the plane must stop (caught route)

    # ----------------- Dialogue bridge -----------------
    def layout_for_dialogue(self, dialog_top: int):
        pass

    def start_event(self, evt_name, on_done=None):
        self._evt = evt_name
        self._evt_cb = on_done
        self._timer = 0.0

        if evt_name == "airport_intro":
            self._phase = "car_drive_in"
            self.tony_visible = False

            target_x_default = float(self.spawn_x + 40)
            self._car_target_x = float(CAR_STOP_X if CAR_STOP_X is not None else target_x_default)
            self.car.x = float(CAR_START_X if CAR_START_X is not None else (-self.car.w - 20))
            self._car_speed = 320.0

        elif evt_name in ("airport_run", "airport_run_caught"):
            # reset route-specific flags
            self._caught_variant = (evt_name == "airport_run_caught")
            self._plane_brake = False
            self._plane_stop_cx = self.win_w * PLANE_CLIMB_TRIGGER_FRACTION  # stop exactly at old climb trigger

            self._phase = "walk_right_normal"
            self.done = False

            if not self.tony_visible:
                self.tony_visible = True
                side_dir = 1 if TONY_SPAWN_RIGHT_OF_CAR else -1
                if side_dir > 0:
                    self.tony.x = self.car.x + self.car.w + TONY_SPAWN_OFFSET_X
                else:
                    self.tony.x = self.car.x - TONY_SPAWN_OFFSET_X - self.tony.w
                self.tony.y = float(self.spawn_y - self.tony.h)
                self.tony.x = max(0.0, min(self.win_w - self.tony.w, self.tony.x))

            self._board_x = float(
                TONY_BOARD_X if TONY_BOARD_X is not None else (self.plane.x + self.plane.w * 0.5)
            )
            self._board_y = float(
                TONY_BOARD_Y if TONY_BOARD_Y is not None else (self.plane.y + 16)
            )

            start_x = self.tony.x
            dist = max(1.0, (self._board_x - start_x))
            self._x_norm_end = start_x + dist * 0.30
            self._x_slow_end = start_x + dist * 0.50

            self._spd_norm = 280.0
            self._spd_slow = 120.0
            self._spd_run  = 640.0

        else:
            self._finish_evt()

    def _finish_evt(self):
        if self._evt_cb and self._evt:
            cb = self._evt_cb
            ev = self._evt
            self._evt = None
            self._evt_cb = None
            cb(ev)

    # ----------------- Placement helpers -----------------
    def _place_initial(self):
        default_car_bottom = self.spawn_y + 8
        if CAR_BOTTOM_Y is not None:
            car_bottom = float(CAR_BOTTOM_Y)
            self.car.y = car_bottom - self.car.h
        elif CAR_Y is not None:
            self.car.y = float(CAR_Y)
            car_bottom = self.car.y + self.car.h
        else:
            car_bottom = default_car_bottom
            self.car.y = car_bottom - self.car.h

        if PLANE_START_X is not None:
            self.plane.x = float(PLANE_START_X)

        if PLANE_START_Y is not None:
            self.plane.y = float(PLANE_START_Y)
        elif ALIGN_PLANE_TO_CAR_BASELINE:
            self.plane.y = (car_bottom - self.plane.h)

        self.tony.x = float(self.spawn_x)
        self.tony.y = float(self.spawn_y - self.tony.h)
        self.tony_visible = False

    # ----------------- Police spawn -----------------
    def _spawn_police_if_needed(self):
        if self._spawned_police:
            return
        self._spawned_police = True

        # --- Police 1: comes from left → goes right ---
        img_right = self._police_right_img  # flipped, since base faces LEFT
        start_x_1 = POLICE1_START_X if POLICE1_START_X is not None else (-img_right.get_width() - 20)
        p1 = PoliceCar(
            x=float(start_x_1),
            y=float(POLICE1_Y),
            surf=img_right,
            speed=POLICE1_SPEED,
            going_right=True,                # moves right
            end_x=float(POLICE1_END_X),
        )

        # --- Police 2: comes from right → goes left ---
        img_left = self._police_left_img    # base sprite already faces LEFT
        default_right_x = self.win_w + 20
        start_x_2 = POLICE2_START_X if POLICE2_START_X is not None else default_right_x
        p2 = PoliceCar(
            x=float(start_x_2),
            y=float(POLICE2_Y),
            surf=img_left,
            speed=POLICE2_SPEED,
            going_right=False,               # moves left
            end_x=float(POLICE2_END_X),
        )

        # --- Police 3: comes from right → goes left ---
        start_x_3 = POLICE3_START_X if POLICE3_START_X is not None else default_right_x
        p3 = PoliceCar(
            x=float(start_x_3),
            y=float(POLICE3_Y),
            surf=img_left,
            speed=POLICE3_SPEED,
            going_right=False,               # moves left
            end_x=float(POLICE3_END_X),
        )

        # Draw order fix: police3 BEHIND police2
        self.police = [p1, p3, p2]

    # ----------------- Update/Draw -----------------
    def _advance_anim(self, dt):
        self._anim_timer += dt
        if self._anim_timer >= 0.14:
            self._anim_timer -= 0.14
            self._anim_index = 1 - self._anim_index

    def update(self, dt_ms: int):
        dt = dt_ms / 1000.0
        self._advance_anim(dt)

        if self._evt == "airport_intro":
            if self._phase == "car_drive_in":
                if self.car.x < self._car_target_x:
                    self.car.x = min(self._car_target_x, self.car.x + self._car_speed * dt)
                else:
                    self._phase = "car_stop_pause"
                    self._timer = 1.0
            elif self._phase == "car_stop_pause":
                self._timer -= dt
                if self._timer <= 0.0:
                    self.tony_visible = True
                    self.tony.surf = self.tony_front
                    side_dir = 1 if TONY_SPAWN_RIGHT_OF_CAR else -1
                    if side_dir > 0:
                        self.tony.x = self.car.x + self.car.w + TONY_SPAWN_OFFSET_X
                    else:
                        self.tony.x = self.car.x - TONY_SPAWN_OFFSET_X - self.tony.w
                    self.tony.y = float(self.spawn_y - self.tony.h)
                    self.tony.x = max(0.0, min(self.win_w - self.tony.w, self.tony.x))
                    self._finish_evt()

        elif self._evt in ("airport_run", "airport_run_caught"):
            if self._phase in ("walk_right_normal", "walk_right_slow", "walk_right_run"):
                if self._phase == "walk_right_normal":
                    spd = self._spd_norm
                    end_x = self._x_norm_end
                    next_phase = "walk_right_slow"
                elif self._phase == "walk_right_slow":
                    spd = self._spd_slow
                    end_x = self._x_slow_end
                    next_phase = "walk_right_run"
                else:
                    spd = self._spd_run
                    end_x = self._board_x
                    next_phase = "plane_taxi"  # vanish & start taxi when reached

                self.tony.surf = self.tony_walk_r_1 if self._anim_index == 0 else self.tony_walk_r_2

                dir_sign = 1.0 if end_x >= self.tony.x else -1.0
                self.tony.x += dir_sign * spd * dt
                if (dir_sign > 0 and self.tony.x >= end_x) or (dir_sign < 0 and self.tony.x <= end_x):
                    self.tony.x = end_x
                    if next_phase == "plane_taxi":
                        self.tony_visible = False
                        self._plane_started_climb = False
                        self._plane_taxi_speed = max(50.0, self._plane_taxi_speed)
                    self._phase = next_phase

            elif self._phase == "plane_taxi":
                # accelerate forward (left) while taxiing
                self._plane_taxi_speed = min(
                    self._plane_taxi_speed_max,
                    self._plane_taxi_speed + self._plane_taxi_accel * dt
                )

                # We'll handle movement separately per route so we can clamp at the stop point.
                current_cx = self.plane.x + self.plane.w * 0.5
                trigger_cx = self._plane_stop_cx if self._plane_stop_cx is not None else (self.win_w * PLANE_CLIMB_TRIGGER_FRACTION)
                stop_left_x = trigger_cx - self.plane.w * 0.5

                if not self._caught_variant:
                    # --- ORIGINAL ROUTE ---
                    # Move first
                    self.plane.x -= self._plane_taxi_speed * dt

                    # Trigger climb + spawn police at trigger
                    if not self._plane_started_climb and (self.plane.x + self.plane.w * 0.5) <= trigger_cx:
                        self._plane_started_climb = True
                        self._spawn_police_if_needed()

                    if self._plane_started_climb:
                        self.plane.y -= self._plane_climb_speed * dt

                else:
                    # --- CAUGHT VARIANT ---
                    # Spawn police when we're ~1s (at current speed) from the stop point
                    dist_to_stop = max(0.0, current_cx - trigger_cx)
                    if (not self._spawned_police) and dist_to_stop <= (self._plane_taxi_speed * 1.0):
                        self._spawn_police_if_needed()

                    # If we haven't begun braking, compute the next position and clamp to stop
                    next_x = self.plane.x - self._plane_taxi_speed * dt
                    next_cx = next_x + self.plane.w * 0.5

                    if not self._plane_brake and next_cx <= trigger_cx:
                        # Snap exactly to the stop point (no overshoot), set speed to 0
                        self.plane.x = stop_left_x
                        self._plane_taxi_speed = 0.0
                        self._plane_brake = True
                    elif not self._plane_brake:
                        # Still before the stop point → advance normally
                        self.plane.x = next_x
                    else:
                        # Already braking (we might have arrived already). Keep x clamped and speed at 0.
                        self.plane.x = stop_left_x
                        self._plane_taxi_speed = 0.0

                # update police movement every frame
                for p in self.police:
                    p.update(dt)

                # End conditions:
                if not self._caught_variant:
                    # original: plane leaves screen (x or y)
                    if self.plane.x + self.plane.w < -20 or self.plane.y + self.plane.h < -20:
                        self._phase = "done"
                        self.done = True
                        self._finish_evt()
                else:
                    # caught: plane fully stopped AND police have reached their stops
                    if self._plane_brake and self._plane_taxi_speed <= 0.01:
                        all_stopped = all(not p.active for p in self.police) if self.police else False
                        if all_stopped:
                            self._phase = "done"
                            self.done = True
                            self._finish_evt()

        # keep police moving when not inside the taxi update block (defensive)
        if self.police and self._evt not in ("airport_run", "airport_run_caught"):
            for p in self.police:
                p.update(dt)

    def draw(self, screen):
        # Background
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

        # Draw order: plane (back), car, Tony, then police
        screen.blit(self.plane.surf, (int(self.plane.x), int(self.plane.y)))
        self.car.draw(screen)
        if self.tony_visible:
            self.tony.draw(screen)
        for p in self.police:
            p.draw(screen)