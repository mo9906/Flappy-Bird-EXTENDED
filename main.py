import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QInputDialog, QLineEdit
from PyQt5.QtGui import QColor, QPainter, QPixmap, QFont, QPen, QTransform, QIcon
from PyQt5.QtCore import Qt, QTimer, QRect, QPointF
import random
from enum import Enum, auto
import json
import os
import pygame.mixer
import time
import math

# --- Global Game Configuration ---
WINDOW_WIDTH = 288
WINDOW_HEIGHT = 512
GROUND_HEIGHT = 112
PIPE_WIDTH = 52
BIRD_ASSET_SIZE = (34, 24)
PIPE_SPEED = 2.0
GRAVITY = 0.5
MOON_GRAVITY = 0.07  # Adjusted: Lower value for a more pronounced "moon" feel
LIFT = -8.0
MOON_LIFT = -3.0  # Adjusted: Lower value for slower, weaker jumps
DEBUG_MODE = True
DECORATION_PIPE_Y = 300
BIRD_PIPE_CONTROL_SPEED = 1.0  # Adjusted for slower, more controllable movement
GRAVITY_BIRD_CONTROL_ACCELERATION = 0.2
LEADERBOARD_FILE = "data/leaderboard.json"
BACKGROUND_SCROLL_SPEED = 0.5  # New value for parallax background scrolling
SPECIAL_PIPE_CHANCE = 0.2  # 20% chance to spawn a special pipe
MOVING_PIPE_CHANCE = 0.5  # 5% chance to spawn a moving pipe
DOUBLE_MOVING_PIPE_CHANCE = 0.5  # 50% chance to spawn a second moving pipe
MOVING_PIPE_GAP = 150  # Wider gap for moving pipes
BIRD_ROTATION_EASING = 0.02  # Adjusted: Easing factor for Moon Gravity random rotation
GROUND_DARKENING_OPACITY = 0.35  # New: Opacity for the semi-transparent dark rectangle over the ground

# --- File Paths ---
ASSETS_PATH = "assets"
AUDIO_PATH = os.path.join(ASSETS_PATH, "audio")
SPRITES_PATH = os.path.join(ASSETS_PATH, "sprites")

# Audio
AUDIO_DIE = os.path.join(AUDIO_PATH, "die.ogg")
AUDIO_HIT = os.path.join(AUDIO_PATH, "hit.ogg")
AUDIO_POINT = os.path.join(AUDIO_PATH, "point.ogg")
AUDIO_SWOOSH = os.path.join(AUDIO_PATH, "swoosh.ogg")
AUDIO_WING = os.path.join(AUDIO_PATH, "wing.ogg")

# Sprites
BACKGROUND_DAY = os.path.join(SPRITES_PATH, "background-day.png")
BACKGROUND_NIGHT = os.path.join(SPRITES_PATH, "background-night.png")
GROUND_PATH = os.path.join(SPRITES_PATH, "base.png")
GAME_OVER_PATH = os.path.join(SPRITES_PATH, "gameover.png")
MESSAGE_PATH = os.path.join(SPRITES_PATH, "message.png")
PIPE_GREEN = os.path.join(SPRITES_PATH, "pipe-green.png")
PIPE_RED = os.path.join(SPRITES_PATH, "pipe-red.png")
CLOUDS_BG_PATH = os.path.join(SPRITES_PATH, "cloud_bg.png")
CLOUDS_FG_PATH = os.path.join(SPRITES_PATH, "cloud_fg.png")


# --- Game States ---
class GameState(Enum):
    MAIN_MENU = auto()
    ADVENTURE_MODE = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    PIPE_CONTROL_MODE = auto()


# --- Bird Class (Modified for Animation and Rotation) ---
class Bird:
    def __init__(self, x, y, color="red"):
        self.x = x
        self.y = y
        self.width, self.height = BIRD_ASSET_SIZE
        self.velocity = 0
        self.gravity = GRAVITY
        self.lift = LIFT
        self.rotation = 0
        self.target_rotation = 0  # New: For Moon Gravity random rotation
        self.frame = 0
        self.frame_timer = 0
        self.color = color
        self.sprite_frames = self.load_sprites()
        self.max_rotation_up = -25  # Max upward tilt
        self.max_rotation_down = 90  # Max downward tilt
        self.pipe_control_velocity = 0
        self.target_pipe_control_velocity = 0
        self.pipe_control_acceleration = 0.2  # Easing factor for smooth acceleration/deceleration
        self.direction_change_timer = 0
        # Increased interval to make the bird change direction less frequently
        self.direction_change_interval = random.randint(250, 350)
        self.moon_rotation_timer = 0  # New: Timer for Moon Gravity rotation change
        self.moon_rotation_interval = 60  # New: Interval for Moon Gravity rotation change

    def load_sprites(self):
        sprites = []
        for flap in ["down", "mid", "up"]:
            path = os.path.join(SPRITES_PATH, f"{self.color}bird-{flap}flap.png")
            sprite = QPixmap(path).scaled(*BIRD_ASSET_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if sprite.isNull():
                print(f"Error: Bird texture '{path}' could not be loaded!")
                return [QPixmap(), QPixmap(), QPixmap()]
            sprites.append(sprite)
        return sprites

    def flap(self):
        # Flap logic remains the same
        self.velocity = self.lift
        self.rotation = self.max_rotation_up
        pygame.mixer.Sound(AUDIO_WING).play()

    def update(self, game_state):
        if game_state == GameState.ADVENTURE_MODE:
            self.velocity += self.gravity
            self.y += self.velocity

            # Standard rotation logic
            if self.gravity == MOON_GRAVITY:
                self.moon_rotation_timer += 1
                if self.moon_rotation_timer >= self.moon_rotation_interval:
                    self.target_rotation = random.uniform(-45, 45)  # Random rotation between -45 and 45 degrees
                    self.moon_rotation_timer = 0
                    self.moon_rotation_interval = random.randint(30, 90)

                # Smoothly transition to the target rotation (easing)
                self.rotation += (self.target_rotation - self.rotation) * BIRD_ROTATION_EASING
            else:
                if self.velocity > 0:
                    self.rotation = min(self.max_rotation_down, self.rotation + 4)
                else:
                    self.rotation = self.max_rotation_up

        elif game_state == GameState.PIPE_CONTROL_MODE:
            self.direction_change_timer += 1
            if self.direction_change_timer >= self.direction_change_interval:
                self.target_pipe_control_velocity = random.choice([BIRD_PIPE_CONTROL_SPEED, -BIRD_PIPE_CONTROL_SPEED])
                self.direction_change_timer = 0
                self.direction_change_interval = random.randint(250, 350)

            self.pipe_control_velocity += (
                                                  self.target_pipe_control_velocity - self.pipe_control_velocity) * self.pipe_control_acceleration
            self.y += self.pipe_control_velocity

            if self.y < 0:
                self.y = 0
                self.target_pipe_control_velocity = BIRD_PIPE_CONTROL_SPEED
            elif self.y + self.height > WINDOW_HEIGHT - GROUND_HEIGHT:
                self.y = WINDOW_HEIGHT - GROUND_HEIGHT - self.height
                self.target_pipe_control_velocity = -BIRD_PIPE_CONTROL_SPEED

        self.frame_timer += 1
        if self.frame_timer > 5:
            self.frame_timer = 0
            self.frame = (self.frame + 1) % len(self.sprite_frames)

    def bounce_update(self):
        self.y = 200 + 5 * (self.frame % 2)
        self.frame_timer += 1
        if self.frame_timer > 10:
            self.frame_timer = 0
            self.frame = (self.frame + 1) % len(self.sprite_frames)

    def get_hitbox(self):
        hitbox_margin_x = 5
        hitbox_margin_y = 5
        return QRect(
            int(self.x) + hitbox_margin_x,
            int(self.y) + hitbox_margin_y,
            self.width - 2 * hitbox_margin_x,
            self.height - 2 * hitbox_margin_y
        )

    def draw(self, painter, debug_mode=False):
        current_sprite = self.sprite_frames[self.frame]
        painter.save()
        painter.translate(self.x + self.width / 2, self.y + self.height / 2)
        painter.rotate(self.rotation)
        painter.drawPixmap(int(-self.width / 2), int(-self.height / 2), current_sprite)
        painter.restore()

        if debug_mode:
            painter.setPen(QColor(255, 0, 0))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.get_hitbox())


# --- Pipe Classes ---
class Pipe:
    def __init__(self, x, gap_y, gap_height, is_pipe_control_mode=False, is_special=False):
        self.x = x
        self.gap_y = gap_y
        self.width = PIPE_WIDTH
        self.gap_height = gap_height
        self.passed = False
        self.is_pipe_control_mode = is_pipe_control_mode
        self.is_special = is_special
        self.is_moving = False

        pipe_texture_path = PIPE_RED if is_special else PIPE_GREEN
        self.pipe_top_texture = QPixmap(pipe_texture_path).scaledToWidth(self.width)
        self.pipe_bottom_texture = QPixmap(pipe_texture_path).scaledToWidth(self.width).transformed(
            QTransform().rotate(180)
        )
        if self.pipe_top_texture.isNull() or self.pipe_bottom_texture.isNull():
            print("Error: Pipe textures could not be loaded!")

    def update(self):
        self.x -= PIPE_SPEED

    def get_top_hitbox(self):
        return QRect(int(self.x), 0, self.width, int(self.gap_y))

    def get_bottom_hitbox(self, window_height):
        return QRect(int(self.x), int(self.gap_y + self.gap_height), self.width, window_height)

    def draw(self, painter, window_height, debug_mode=False):
        painter.drawPixmap(int(self.x), int(self.gap_y - self.pipe_top_texture.height()), self.pipe_top_texture)
        painter.drawPixmap(int(self.x), int(self.gap_y + self.gap_height), self.pipe_bottom_texture)

        if debug_mode:
            painter.setPen(QColor(0, 255, 255))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.get_top_hitbox())
            painter.drawRect(self.get_bottom_hitbox(window_height))


class MovingPipe(Pipe):
    def __init__(self, x, gap_y, gap_height):
        super().__init__(x, gap_y, gap_height)
        self.is_moving = True
        self.y_offset = gap_y
        self.move_amplitude = 80
        self.move_frequency = 0.006
        self.time_offset = random.uniform(0, 2 * math.pi)

    def update(self):
        super().update()
        vertical_move = math.sin(self.move_frequency * (self.x + self.time_offset)) * self.move_amplitude
        self.gap_y = self.y_offset + vertical_move


# --- Ground Class ---
class Ground:
    def __init__(self):
        self.height = GROUND_HEIGHT
        self.texture = QPixmap(GROUND_PATH).scaled(WINDOW_WIDTH + 10, self.height, Qt.IgnoreAspectRatio,
                                                   Qt.SmoothTransformation)
        if self.texture.isNull():
            print("Error: Ground texture could not be loaded!")

        self.x1 = 0
        self.x2 = WINDOW_WIDTH

    def update(self):
        self.x1 -= PIPE_SPEED
        self.x2 -= PIPE_SPEED
        if self.x1 <= -WINDOW_WIDTH:
            self.x1 = WINDOW_WIDTH
        if self.x2 <= -WINDOW_WIDTH:
            self.x2 = WINDOW_WIDTH

    def get_hitbox(self):
        return QRect(0, WINDOW_HEIGHT - self.height, WINDOW_WIDTH, self.height)

    def draw(self, painter, debug_mode=False):
        painter.drawPixmap(int(self.x1), WINDOW_HEIGHT - self.height, self.texture)
        painter.drawPixmap(int(self.x2), WINDOW_HEIGHT - self.height, self.texture)

        if debug_mode:
            painter.setPen(QColor(0, 0, 255))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.get_hitbox())


# --- Cloud Class for the "Cloudy Sky" event ---
class Cloud:
    def __init__(self, x, y, speed, opacity, size_factor, sprite_path="clouds.png", animation_type=None):
        self.x = x
        self.y = y
        self.speed = speed
        self.initial_opacity = opacity
        self.opacity = 0.0 if animation_type == "alpha_ease" else opacity
        self.size_factor = size_factor
        self.width = 0
        self.height = 0

        cloud_sprite_path = sprite_path

        base_sprite = QPixmap(cloud_sprite_path)
        if base_sprite.isNull():
            print(f"Error: Cloud texture '{cloud_sprite_path}' could not be loaded!")
            self.sprite = QPixmap()
        else:
            self.sprite = base_sprite.scaled(int(base_sprite.width() * size_factor),
                                             int(base_sprite.height() * size_factor))
            self.width = self.sprite.width()
            self.height = self.sprite.height()

        # New animation attributes
        self.animation_type = animation_type
        self.animation_start_time = time.time()
        self.animation_duration = random.uniform(1.5, 3.0)  # Random duration for each cloud
        self.is_animating = True

        if self.animation_type == "y_ease":
            self.start_y = WINDOW_HEIGHT
            self.y = self.start_y
            self.target_y = y
        else:  # For "alpha_ease" and no animation
            self.start_y = y
            self.target_y = y

    def update(self):
        if self.is_animating:
            elapsed = time.time() - self.animation_start_time
            progress = min(1.0, elapsed / self.animation_duration)

            # Simple easing function (quadratic ease-out)
            eased_progress = 1 - (1 - progress) ** 2

            if self.animation_type == "y_ease":
                self.y = self.start_y + (self.target_y - self.start_y) * eased_progress
                if progress >= 1.0:
                    self.is_animating = False
            elif self.animation_type == "alpha_ease":
                self.opacity = self.initial_opacity * eased_progress
                if progress >= 1.0:
                    self.is_animating = False
        else:
            self.x -= self.speed

    def draw(self, painter):
        painter.save()
        painter.setOpacity(self.opacity)
        painter.drawPixmap(int(self.x), int(self.y), self.sprite)
        painter.restore()


# --- Main Game Window ---
class GameWindow(QMainWindow):
    # --- UI and Game-Specific Hardcoded Values ---
    GAME_OVER_TEXT_Y = 100
    MESSAGE_IMAGE_Y = 50
    DEBUG_TEXT_X_OFFSET = 150
    DEBUG_TEXT_WIDTH = 140
    BOTTOM_TEXT_Y = WINDOW_HEIGHT - 35
    HIGH_SCORE_TEXT_WIDTH = int(WINDOW_WIDTH / 2)
    EVENT_TEXT_Y = WINDOW_HEIGHT - 55
    EVENT_TEXT_WIDTH = WINDOW_WIDTH - 40
    PAUSED_TEXT = "PAUSED"
    LEADERBOARD_INFO_Y = 360
    LEADERBOARD_Y_OFFSET = 20
    PIPE_SPAWN_INTERVAL = 1500  # ms
    BIRD_START_X = 50
    BIRD_START_Y = 200
    BIRD_BOUNCE_Y_OFFSET = 5
    BIRD_BOUNCE_TIMER_THRESHOLD = 10
    BIRD_FRAME_TIMER_THRESHOLD = 5
    BIRD_TILT_RATE = 4
    HITBOX_MARGIN = 5
    PIPE_GAP_MIN_Y = 60

    # New: Event-specific Pipe Gap Height for Moon Gravity
    MOON_GRAVITY_PIPE_GAP_HEIGHT = 120

    # --- Random Event Configuration ---
    EVENT_DURATION_MIN = 5.0  # seconds
    EVENT_DURATION_MAX = 10.0  # seconds
    EVENT_INTERVAL_MIN = 3.0  # seconds
    EVENT_INTERVAL_MAX = 8.0  # seconds

    # --- Day/Night Cycle Configuration ---
    BACKGROUND_CYCLE_SECONDS = 12  # 12 seconds per cycle
    FADE_DURATION = 12.0  # Duration of the fade animation in seconds

    GRAVITY_TRANSITION_SPEED = 0.005  # How fast gravity inverts

    # New: "Cloudy Sky" event specific variables
    CLOUDY_SKY_OVERLAY_OPACITY = 0.5
    CLOUD_SPAWN_INTERVAL_MIN = 300  # milliseconds
    CLOUD_SPAWN_INTERVAL_MAX = 600

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flappy Bird")

        # New: Set the window icon
        icon_path = os.path.join(SPRITES_PATH, 'yellowbird-midflap.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file not found at '{icon_path}'")

        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        pygame.mixer.init()

        self.original_bird_size = BIRD_ASSET_SIZE
        self.original_lift = LIFT
        self.original_gravity = GRAVITY
        self.PIPE_GAP_HEIGHT = 100
        self.original_pipe_gap_height = self.PIPE_GAP_HEIGHT

        self.gravity_target = GRAVITY

        self.background_day_texture = QPixmap(BACKGROUND_DAY).scaled(WINDOW_WIDTH + 1, WINDOW_HEIGHT + 1,
                                                                     Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.background_night_texture = QPixmap(BACKGROUND_NIGHT).scaled(WINDOW_WIDTH + 1, WINDOW_HEIGHT + 1,
                                                                         Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        self.current_background_texture = self.background_day_texture
        self.previous_background_texture = self.background_night_texture
        self.background_scroll_x = 0
        self.background_last_switch_time = time.time()

        self.game_over_image = QPixmap(GAME_OVER_PATH).scaledToWidth(int(WINDOW_WIDTH * 0.8))
        self.message_image = QPixmap(MESSAGE_PATH).scaledToWidth(int(WINDOW_WIDTH * 0.8))
        self.number_sprites = [QPixmap(os.path.join(SPRITES_PATH, f"{i}.png")) for i in range(10)]

        self.game_state = GameState.MAIN_MENU
        self.bird = Bird(self.BIRD_START_X, self.BIRD_START_Y, "red")
        self.pipes = []
        self.score = 0
        self.debug_mode = DEBUG_MODE
        self.debug_toggle_timer = QTimer(self)
        self.debug_toggle_timer.setSingleShot(True)
        self.debug_toggle_timer.timeout.connect(self._toggle_debug_mode)

        self.events_enabled = True

        self.ground = Ground()

        self.pipe_spawn_timer = QTimer(self)
        self.pipe_spawn_timer.timeout.connect(self.spawn_pipe)

        self.main_game_timer = QTimer(self)
        self.main_game_timer.timeout.connect(self.update_game)
        self.main_game_timer.start(16)

        # Removed inverse_gravity flag
        self.size_changer = False

        self.is_cloudy_sky_event = False
        self.background_clouds = []
        self.foreground_clouds = []
        self.cloud_spawn_timer = QTimer(self)
        self.cloud_spawn_timer.timeout.connect(self.spawn_cloud)

        self.pipe_control_pipes = []

        self.skins = ["red", "blue", "yellow"]
        self.current_skin_index = 0

        self.current_menu_mode = GameState.ADVENTURE_MODE

        self.leaderboard = self.load_leaderboard()
        self.score_multiplier = 1

        self.random_event_end_time = 0
        self.current_event = None
        self.next_event_time = time.time() + random.uniform(self.EVENT_INTERVAL_MIN, self.EVENT_INTERVAL_MAX)
        self.event_timer_active = False
        self.last_event_end_time = time.time()

        self.game_over_timer = QTimer(self)
        self.game_over_timer.setSingleShot(True)
        self.game_over_timer.timeout.connect(self.show_name_input_dialog)

        self.cloud_configs = [
            {"z_index": 0, "speed_factor": 0.5, "size_factor": 0.8, "opacity": 0.6},
            {"z_index": 0, "speed_factor": 0.7, "size_factor": 1.0, "opacity": 0.7},
            {"z_index": 0, "speed_factor": 0.9, "size_factor": 1.2, "opacity": 0.8},
            {"z_index": 1, "speed_factor": 0.3, "size_factor": 1.5, "opacity": 0.9}
        ]

        # Ensure the 'data' directory exists for the leaderboard file
        os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)

    def load_leaderboard(self):
        try:
            if os.path.exists(LEADERBOARD_FILE):
                with open(LEADERBOARD_FILE, 'r') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading leaderboard: {e}")
        return []

    def save_score(self, player_name, score):
        try:
            self.leaderboard.append({"name": player_name, "score": score})
            self.leaderboard.sort(key=lambda x: x["score"], reverse=True)
            self.leaderboard = self.leaderboard[:5]
            with open(LEADERBOARD_FILE, 'w') as f:
                json.dump(self.leaderboard, f, indent=4)
        except IOError as e:
            print(f"Error saving leaderboard: {e}")

    def show_name_input_dialog(self):
        is_top_score = False
        if len(self.leaderboard) < 3:
            is_top_score = True
        elif self.score > (self.leaderboard[2]['score'] if len(self.leaderboard) > 2 else -1):
            is_top_score = True

        if is_top_score:
            text, ok = QInputDialog.getText(self, "Game Over",
                                            f"Your score: {self.score}\n Enter your name:",
                                            echo=QLineEdit.Normal)

            if ok and text:
                self.save_score(text, self.score)

        self.restart_game()

    def start_game(self, game_mode):
        self.game_state = game_mode
        self.score = 0
        self.bird = Bird(self.BIRD_START_X, self.BIRD_START_Y, self.skins[self.current_skin_index])
        self.pipes = []
        self.pipe_spawn_timer.start(self.PIPE_SPAWN_INTERVAL)
        self.next_event_time = time.time() + random.uniform(self.EVENT_INTERVAL_MIN, self.EVENT_INTERVAL_MAX)
        self.last_event_end_time = time.time()

    def spawn_pipe(self):
        if self.game_state in [GameState.ADVENTURE_MODE, GameState.PIPE_CONTROL_MODE]:
            # New: Check for a moving pipe spawn chance
            if random.random() < MOVING_PIPE_CHANCE:
                gap_y = random.randint(self.PIPE_GAP_MIN_Y,
                                       WINDOW_HEIGHT - GROUND_HEIGHT - MOVING_PIPE_GAP - self.PIPE_GAP_MIN_Y)
                new_pipe = MovingPipe(WINDOW_WIDTH, gap_y, MOVING_PIPE_GAP)
                self.pipes.append(new_pipe)

                # New: Check for a second moving pipe
                if random.random() < DOUBLE_MOVING_PIPE_CHANCE:
                    gap_y_2 = random.randint(self.PIPE_GAP_MIN_Y,
                                             WINDOW_HEIGHT - GROUND_HEIGHT - MOVING_PIPE_GAP - self.PIPE_GAP_MIN_Y)
                    new_pipe_2 = MovingPipe(WINDOW_WIDTH + PIPE_WIDTH + 100, gap_y_2, MOVING_PIPE_GAP)
                    self.pipes.append(new_pipe_2)
            else:
                # Original pipe spawning logic
                min_gap_y = self.PIPE_GAP_MIN_Y
                max_gap_y = WINDOW_HEIGHT - GROUND_HEIGHT - self.PIPE_GAP_HEIGHT - self.PIPE_GAP_MIN_Y
                gap_y = random.randint(min_gap_y, max_gap_y)

                is_special = random.random() < SPECIAL_PIPE_CHANCE

                new_pipe = Pipe(WINDOW_WIDTH, gap_y, self.PIPE_GAP_HEIGHT,
                                is_pipe_control_mode=(self.game_state == GameState.PIPE_CONTROL_MODE),
                                is_special=is_special)
                self.pipes.append(new_pipe)

    def spawn_cloud(self):
        if self.is_cloudy_sky_event:
            config = random.choice(self.cloud_configs)
            y = random.randint(0, WINDOW_HEIGHT // 2)

            # Select animation type based on z_index
            animation_type = "y_ease" if config["z_index"] == 0 else "alpha_ease"

            sprite_path = CLOUDS_BG_PATH if config["z_index"] == 0 else CLOUDS_FG_PATH

            new_cloud = Cloud(
                WINDOW_WIDTH, y,
                config["speed_factor"] * PIPE_SPEED,
                config["opacity"],
                config["size_factor"],
                sprite_path,
                animation_type
            )

            if config["z_index"] == 0:
                self.background_clouds.append(new_cloud)
            else:
                self.foreground_clouds.append(new_cloud)

    def _toggle_debug_mode(self):
        self.debug_mode = not self.debug_mode
        self.update()

    def keyPressEvent(self, event):
        if self.game_state in [GameState.ADVENTURE_MODE, GameState.PIPE_CONTROL_MODE]:
            if event.key() == Qt.Key_Space:
                self.bird.flap()

        if self.debug_mode:
            if event.key() == Qt.Key_1:
                # Changed from Inverse Gravity to Moon Gravity
                self.trigger_event("Moon Gravity")
            elif event.key() == Qt.Key_2:
                self.trigger_event("Size Changer")
            elif event.key() == Qt.Key_3:
                self.trigger_event("Double Score")
            elif event.key() == Qt.Key_4:
                self.trigger_event("Cloudy Sky")

        if event.key() == Qt.Key_P:
            if self.game_state in [GameState.ADVENTURE_MODE, GameState.PIPE_CONTROL_MODE]:
                self.game_state = GameState.PAUSED
                self.pipe_spawn_timer.stop()
                self.cloud_spawn_timer.stop()
            elif self.game_state == GameState.PAUSED:
                if not self.pipes and self.current_menu_mode == GameState.PIPE_CONTROL_MODE:
                    self.game_state = GameState.PIPE_CONTROL_MODE
                else:
                    self.game_state = GameState.ADVENTURE_MODE
                self.pipe_spawn_timer.start(self.PIPE_SPAWN_INTERVAL)
                if self.is_cloudy_sky_event:
                    self.cloud_spawn_timer.start(
                        random.randint(self.CLOUD_SPAWN_INTERVAL_MIN, self.CLOUD_SPAWN_INTERVAL_MAX))
        elif event.key() == Qt.Key_B:
            if not self.debug_toggle_timer.isActive():
                self.debug_toggle_timer.start(500)
        elif event.key() == Qt.Key_E:
            self.events_enabled = not self.events_enabled
            if not self.events_enabled and self.current_event:
                self.end_random_event()
            self.update()
        elif event.key() == Qt.Key_R and self.game_state == GameState.GAME_OVER:
            self.restart_game()
        elif event.key() == Qt.Key_S and self.game_state == GameState.MAIN_MENU:
            self.current_skin_index = (self.current_skin_index + 1) % len(self.skins)
            self.bird = Bird(self.BIRD_START_X, self.BIRD_START_Y, self.skins[self.current_skin_index])
        elif event.key() == Qt.Key_C and self.game_state == GameState.MAIN_MENU:
            if self.current_menu_mode == GameState.ADVENTURE_MODE:
                self.current_menu_mode = GameState.PIPE_CONTROL_MODE
            else:
                self.current_menu_mode = GameState.ADVENTURE_MODE
            self.update()

    def mouseMoveEvent(self, event):
        if self.game_state == GameState.PIPE_CONTROL_MODE and self.pipes:
            mouse_y = event.y()
            closest_pipe = self.pipes[0]
            if closest_pipe.x < self.bird.x:
                if len(self.pipes) > 1:
                    closest_pipe = self.pipes[1]
                else:
                    return

            min_gap_y = self.PIPE_GAP_MIN_Y
            max_gap_y = WINDOW_HEIGHT - GROUND_HEIGHT - self.PIPE_GAP_HEIGHT - self.PIPE_GAP_MIN_Y

            closest_pipe.gap_y = max(min_gap_y, min(max_gap_y, mouse_y - self.PIPE_GAP_HEIGHT / 2))

    def mousePressEvent(self, event):
        if self.game_state == GameState.MAIN_MENU:
            pygame.mixer.Sound(AUDIO_SWOOSH).play()
            self.start_game(self.current_menu_mode)
        elif self.game_state == GameState.ADVENTURE_MODE:
            self.bird.flap()
        self.update()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_B:
            if self.debug_toggle_timer.isActive():
                self.debug_toggle_timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        time_since_switch = time.time() - self.background_last_switch_time

        painter.save()

        if self.current_background_texture == self.background_day_texture:
            fading_in_texture = self.background_day_texture
            fading_out_texture = self.background_night_texture
        else:
            fading_in_texture = self.background_night_texture
            fading_out_texture = self.background_day_texture

        fade_factor = min(1.0, time_since_switch / self.FADE_DURATION)

        painter.setOpacity(1.0 - fade_factor)
        painter.drawPixmap(int(self.background_scroll_x), 0, fading_out_texture)
        painter.drawPixmap(int(self.background_scroll_x + WINDOW_WIDTH), 0, fading_out_texture)

        painter.setOpacity(fade_factor)
        painter.drawPixmap(int(self.background_scroll_x), 0, fading_in_texture)
        painter.drawPixmap(int(self.background_scroll_x + WINDOW_WIDTH), 0, fading_in_texture)

        painter.restore()

        for cloud in self.background_clouds:
            cloud.draw(painter)

        for pipe in self.pipes:
            pipe.draw(painter, WINDOW_HEIGHT, self.debug_mode)

        self.ground.draw(painter, self.debug_mode)

        # New: Darkening the ground during the Cloudy Sky event
        if self.is_cloudy_sky_event:
            painter.setOpacity(GROUND_DARKENING_OPACITY)
            painter.setBrush(QColor(0, 0, 0))
            painter.drawRect(0, WINDOW_HEIGHT - GROUND_HEIGHT, WINDOW_WIDTH, GROUND_HEIGHT)
            painter.setOpacity(1.0)  # Reset opacity after drawing the rect

        self.bird.draw(painter, self.debug_mode)

        for cloud in self.foreground_clouds:
            cloud.draw(painter)

        self.draw_score_with_numbers(painter)

        if self.game_state == GameState.MAIN_MENU:
            painter.drawPixmap(int((WINDOW_WIDTH - self.message_image.width()) / 2), self.MESSAGE_IMAGE_Y,
                               self.message_image)
            self.draw_main_menu_info(painter)
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(20, 400, "Toggles: E - Events, B - Debug")

        elif self.game_state == GameState.GAME_OVER:
            self.draw_leaderboard(painter)

        if self.game_state == GameState.PAUSED:
            painter.setPen(QColor(0, 0, 0))
            font = QFont("Arial", 36)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, self.PAUSED_TEXT)

        if self.game_state in [GameState.ADVENTURE_MODE, GameState.PIPE_CONTROL_MODE]:
            self.draw_event_bar(painter)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 12))

        high_score_text = f"High Score: {self.leaderboard[0]['score']}" if self.leaderboard else "High Score: 0"
        high_score_rect = QRect(20, self.BOTTOM_TEXT_Y, self.HIGH_SCORE_TEXT_WIDTH, 30)
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(high_score_rect, Qt.AlignLeft | Qt.AlignVCenter, high_score_text)

        debug_rect = QRect(WINDOW_WIDTH - self.DEBUG_TEXT_X_OFFSET, self.BOTTOM_TEXT_Y, self.DEBUG_TEXT_WIDTH, 30)
        painter.setFont(QFont("Arial", 12))
        painter.drawText(debug_rect, Qt.AlignRight | Qt.AlignVCenter, f"DEBUG: {'ON' if self.debug_mode else 'OFF'}")

        event_rect = QRect(20, self.EVENT_TEXT_Y, self.EVENT_TEXT_WIDTH, 20)
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        if self.current_event:
            painter.setPen(QColor(0, 0, 0, 150))
            painter.drawText(event_rect, Qt.AlignCenter, f"Event: {self.current_event}")
        else:
            painter.drawText(event_rect, Qt.AlignCenter, "")

        if self.debug_mode:
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 10))
            debug_legend_y = WINDOW_HEIGHT - 75
            painter.drawText(20, debug_legend_y, "Debug Keys:")
            # Updated debug key text
            painter.drawText(20, debug_legend_y + 12, "1: Moon Gravity")
            painter.drawText(20, debug_legend_y + 24, "2: Size Changer")
            painter.drawText(110, debug_legend_y + 12, "3: Double Score")
            painter.drawText(110, debug_legend_y + 24, "4: Cloudy Sky")

    def draw_event_bar(self, painter):
        max_bar_width = WINDOW_WIDTH - 40
        bar_height = 10
        x_pos = 20
        y_pos = 10

        if self.current_event:
            elapsed = time.time() - self.random_event_start_time
            total_duration = self.random_event_end_time - self.random_event_start_time
            progress = (elapsed / total_duration)

            bar_width = int(max_bar_width * progress)
            painter.setBrush(QColor(255, 215, 0))
            painter.drawRect(x_pos, y_pos, bar_width, bar_height)
        else:
            time_until_event = self.next_event_time - time.time()
            total_interval = self.next_event_time - self.last_event_end_time
            if time_until_event > 0 and total_interval > 0:
                progress = 1 - (time_until_event / total_interval)
                progress = max(0, progress)
                bar_width = int(max_bar_width * progress)
                painter.setBrush(QColor(135, 206, 235))
                painter.drawRect(x_pos, y_pos, bar_width, bar_height)
            else:
                painter.setBrush(QColor(135, 206, 235))
                painter.drawRect(x_pos, y_pos, 0, bar_height)

        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(x_pos, y_pos, max_bar_width, bar_height)

    def draw_score_with_numbers(self, painter):
        score_str = str(self.score)
        total_width = sum(self.number_sprites[int(digit)].width() for digit in score_str)
        x_start = (WINDOW_WIDTH - total_width) / 2

        for digit in score_str:
            sprite = self.number_sprites[int(digit)]
            painter.drawPixmap(int(x_start), 50, sprite)
            x_start += sprite.width()

    def draw_main_menu_info(self, painter):
        painter.setPen(QColor(0, 0, 0))
        font = QFont("Arial", 16)
        font.setBold(True)
        painter.setFont(font)

        mode_text = "Current Mode: " + (
            "Adventure" if self.current_menu_mode == GameState.ADVENTURE_MODE else "Pipe Control")
        painter.drawText(20, 300, mode_text)
        painter.drawText(20, 320, "Press 'C' to Change Mode")

        painter.drawText(20, 350, f"Current Skin: {self.bird.color.capitalize()}")
        painter.drawText(20, 370, "Press 'S' to Change Skin")

    def draw_leaderboard(self, painter):
        if self.leaderboard:
            painter.setPen(QColor(0, 0, 0))

            font_title = QFont("Arial", 16)
            font_title.setBold(True)
            painter.setFont(font_title)

            title_text = "Leaderboard"
            title_width = painter.fontMetrics().boundingRect(title_text).width()
            title_x = int((WINDOW_WIDTH - title_width) / 2)

            num_entries = len(self.leaderboard)
            entry_height = painter.fontMetrics().height() + 5
            total_height = num_entries * entry_height

            leaderboard_start_y = int((WINDOW_HEIGHT - total_height) / 2)

            painter.drawText(title_x, leaderboard_start_y - 20, title_text)

            painter.setFont(QFont("Arial", 12))

            for i, entry in enumerate(self.leaderboard):
                text = f"{i + 1}. {entry['name']}: {entry['score']}"
                text_width = painter.fontMetrics().boundingRect(text).width()
                text_x = int((WINDOW_WIDTH - text_width) / 2)
                painter.drawText(text_x, leaderboard_start_y + i * entry_height, text)

    def update_game(self):
        if time.time() - self.background_last_switch_time > self.BACKGROUND_CYCLE_SECONDS:
            self.previous_background_texture = self.current_background_texture
            if self.current_background_texture == self.background_day_texture:
                self.current_background_texture = self.background_night_texture
            else:
                self.current_background_texture = self.background_day_texture
            self.background_last_switch_time = time.time()

        if self.game_state == GameState.MAIN_MENU:
            self.bird.bounce_update()
            self.ground.update()
            self.background_scroll_x -= BACKGROUND_SCROLL_SPEED
            if self.background_scroll_x <= -WINDOW_WIDTH:
                self.background_scroll_x = 0
        elif self.game_state in [GameState.ADVENTURE_MODE, GameState.PIPE_CONTROL_MODE]:
            if self.bird.gravity != self.gravity_target:
                diff = self.gravity_target - self.bird.gravity
                if abs(diff) > self.GRAVITY_TRANSITION_SPEED:
                    self.bird.gravity += diff * self.GRAVITY_TRANSITION_SPEED
                    # Also smoothly transition lift to keep jump feel consistent with new gravity
                    target_lift = LIFT if self.gravity_target == GRAVITY else MOON_LIFT
                    lift_diff = target_lift - self.bird.lift
                    self.bird.lift += lift_diff * self.GRAVITY_TRANSITION_SPEED
                else:
                    self.bird.gravity = self.gravity_target
                    self.bird.lift = LIFT if self.gravity_target == GRAVITY else MOON_LIFT

            self.bird.update(self.game_state)
            self.ground.update()
            self.update_pipes()
            self.check_collisions()
            self.update_events()

            self.background_scroll_x -= BACKGROUND_SCROLL_SPEED
            if self.background_scroll_x <= -WINDOW_WIDTH:
                self.background_scroll_x = 0

            if self.is_cloudy_sky_event:
                self.background_clouds = [cloud for cloud in self.background_clouds if cloud.x + cloud.width > 0]
                self.foreground_clouds = [cloud for cloud in self.foreground_clouds if cloud.x + cloud.width > 0]
                for cloud in self.background_clouds + self.foreground_clouds:
                    cloud.update()

        self.update()

    def update_events(self):
        if not self.events_enabled:
            return

        current_time = time.time()
        if self.current_event is None and current_time >= self.next_event_time:
            # Replaced "Inverse Gravity" with "Moon Gravity" in random choice
            self.trigger_event(random.choice(["Moon Gravity", "Size Changer", "Double Score", "Cloudy Sky"]))
        elif self.current_event is not None and current_time >= self.random_event_end_time:
            self.end_random_event()

    def trigger_event(self, event_name=None):
        pygame.mixer.Sound(AUDIO_SWOOSH).play()

        if event_name is None:
            # Updated random choice
            event_name = random.choice(["Moon Gravity", "Size Changer", "Double Score", "Cloudy Sky"])

        self.current_event = event_name
        self.random_event_start_time = time.time()
        self.random_event_end_time = time.time() + random.uniform(self.EVENT_DURATION_MIN, self.EVENT_DURATION_MAX)

        if event_name != "Cloudy Sky":
            self.pipes.clear()

        # New: Moon Gravity Event Logic
        if event_name == "Moon Gravity":
            self.gravity_target = MOON_GRAVITY
            self.bird.target_rotation = random.uniform(-45, 45)  # Set initial target for rotation
            self.PIPE_GAP_HEIGHT = self.MOON_GRAVITY_PIPE_GAP_HEIGHT

        elif event_name == "Size Changer":
            size_factor = 1.5
            new_width = self.original_bird_size[0] * size_factor
            new_height = self.original_bird_size[1] * size_factor
            self.bird.width = int(new_width)
            self.bird.height = int(new_height)
            self.bird.sprite_frames = [
                QPixmap(os.path.join(SPRITES_PATH, f"{self.bird.color}bird-upflap.png")).scaled(int(new_width),
                                                                                                int(new_height),
                                                                                                Qt.KeepAspectRatio,
                                                                                                Qt.SmoothTransformation),
                QPixmap(os.path.join(SPRITES_PATH, f"{self.bird.color}bird-midflap.png")).scaled(int(new_width),
                                                                                                 int(new_height),
                                                                                                 Qt.KeepAspectRatio,
                                                                                                 Qt.SmoothTransformation),
                QPixmap(os.path.join(SPRITES_PATH, f"{self.bird.color}bird-downflap.png")).scaled(int(new_width),
                                                                                                  int(new_height),
                                                                                                  Qt.KeepAspectRatio,
                                                                                                  Qt.SmoothTransformation)
            ]
            self.pipes.clear()
            self.bird.lift = self.original_lift * 1.1
            self.bird.gravity = self.original_gravity * 0.9
            self.PIPE_GAP_HEIGHT = int(self.original_pipe_gap_height * 1.5)

        elif event_name == "Double Score":
            self.score_multiplier = 2

        elif event_name == "Cloudy Sky":
            self.is_cloudy_sky_event = True
            self.cloud_spawn_timer.start(random.randint(self.CLOUD_SPAWN_INTERVAL_MIN, self.CLOUD_SPAWN_INTERVAL_MAX))
            self.background_clouds = []
            self.foreground_clouds = []

    def end_random_event(self):
        pygame.mixer.Sound(AUDIO_SWOOSH).play()

        # New: Moon Gravity Event Reset Logic
        if self.current_event == "Moon Gravity":
            self.gravity_target = GRAVITY
            self.bird.target_rotation = self.bird.max_rotation_up  # Reset rotation target
            self.PIPE_GAP_HEIGHT = self.original_pipe_gap_height

        elif self.current_event == "Size Changer":
            self.bird.width, self.bird.height = self.original_bird_size
            self.bird.sprite_frames = [
                QPixmap(os.path.join(SPRITES_PATH, f"{self.bird.color}bird-upflap.png")).scaled(*BIRD_ASSET_SIZE,
                                                                                                Qt.KeepAspectRatio,
                                                                                                Qt.SmoothTransformation),
                QPixmap(os.path.join(SPRITES_PATH, f"{self.bird.color}bird-midflap.png")).scaled(*BIRD_ASSET_SIZE,
                                                                                                 Qt.KeepAspectRatio,
                                                                                                 Qt.SmoothTransformation),
                QPixmap(os.path.join(SPRITES_PATH, f"{self.bird.color}bird-downflap.png")).scaled(*BIRD_ASSET_SIZE,
                                                                                                  Qt.KeepAspectRatio,
                                                                                                  Qt.SmoothTransformation)
            ]
            self.bird.lift = self.original_lift
            self.bird.gravity = self.original_gravity
            self.PIPE_GAP_HEIGHT = self.original_pipe_gap_height

        elif self.current_event == "Double Score":
            self.score_multiplier = 1

        elif self.current_event == "Cloudy Sky":
            self.is_cloudy_sky_event = False
            self.cloud_spawn_timer.stop()
            self.background_clouds = []
            self.foreground_clouds = []

        self.current_event = None
        self.last_event_end_time = time.time()
        self.next_event_time = time.time() + random.uniform(self.EVENT_INTERVAL_MIN, self.EVENT_INTERVAL_MAX)

    def update_pipes(self):
        pipes_to_remove = []
        for pipe in self.pipes:
            pipe.update()
            if pipe.x + pipe.width < 0:
                pipes_to_remove.append(pipe)

            if not pipe.passed and pipe.x < self.bird.x:
                pipe.passed = True
                if pipe.is_special:
                    self.score += 5 * self.score_multiplier
                else:
                    self.score += 1 * self.score_multiplier
                pygame.mixer.Sound(AUDIO_POINT).play()

        for pipe in pipes_to_remove:
            self.pipes.remove(pipe)

    def check_collisions(self):
        if self.bird.get_hitbox().intersects(self.ground.get_hitbox()):
            self.game_over(hit=True)
            return

        # Check for top collision only if not in Moon Gravity (to prevent false positive with extreme random rotation)
        # In Moon Gravity, we rely on the ground check since the bird's movement is slow.
        if self.bird.y <= 0 and self.bird.gravity == GRAVITY:
            self.game_over(hit=False)
            return

        for pipe in self.pipes:
            if self.bird.get_hitbox().intersects(pipe.get_top_hitbox()) or \
                    self.bird.get_hitbox().intersects(pipe.get_bottom_hitbox(WINDOW_HEIGHT)):
                self.game_over(hit=True)
                return

    def game_over(self, hit=False):
        if hit:
            pygame.mixer.Sound(AUDIO_HIT).play()
        pygame.mixer.Sound(AUDIO_DIE).play()
        self.game_state = GameState.GAME_OVER
        self.pipe_spawn_timer.stop()
        self.cloud_spawn_timer.stop()
        self.update()
        self.end_random_event()
        self.game_over_timer.start(2000)

    def restart_game(self):
        self.game_state = GameState.MAIN_MENU
        self.score = 0
        self.bird = Bird(self.BIRD_START_X, self.BIRD_START_Y, self.skins[self.current_skin_index])
        self.pipes = []
        self.pipe_spawn_timer.stop()
        self.cloud_spawn_timer.stop()
        self.background_clouds = []
        self.foreground_clouds = []
        self.is_cloudy_sky_event = False
        self.bird.gravity = self.original_gravity
        self.bird.lift = self.original_lift
        self.PIPE_GAP_HEIGHT = self.original_pipe_gap_height
        self.score_multiplier = 1
        self.gravity_target = GRAVITY
        self.message_image = QPixmap(MESSAGE_PATH).scaledToWidth(int(WINDOW_WIDTH * 0.8))
        self.event_timer_active = False


def main():
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()