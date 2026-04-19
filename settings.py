# Using classes for namespacing so they can be easily changed here and accessed from other files.
import os

class ScreenSettings:
    """Class to hold all the settings related to the screen."""
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH,HEIGHT)
    FPS = 60

class GridSettings:
    RAW_TILE_SIZE = 32 # The actual size of the image files (in pixels)
    SCALE_FACTOR = 1 # The multiplier for how big they will appear in-game
    TILE_SIZE = RAW_TILE_SIZE * SCALE_FACTOR # What rest the code will use for grid snapping

class UISettings:
    WINDOW_PADDING = GridSettings.TILE_SIZE
    BORDER_COLOR = 'white'
    BORDER_RADIUS = 5
    
    # SIDEBAR & LOG FIXED SIZES
    SIDEBAR_WIDTH = 200 
    BOTTOM_LOG_HEIGHT = 150

    # ACTION WINDOW (The Dungeon)
    ACTION_WINDOW_X = WINDOW_PADDING
    ACTION_WINDOW_Y = WINDOW_PADDING
    # Forcing it to a specific number of columns and rows.
    COLS = 14 
    ROWS = 10
    ACTION_WINDOW_WIDTH = COLS * GridSettings.TILE_SIZE
    ACTION_WINDOW_HEIGHT = ROWS * GridSettings.TILE_SIZE

    # SIDEBAR (Right)
    SIDEBAR_X = ACTION_WINDOW_X + ACTION_WINDOW_WIDTH + WINDOW_PADDING
    SIDEBAR_Y = WINDOW_PADDING
    SIDEBAR_HEIGHT = ACTION_WINDOW_HEIGHT

    # MESSAGE LOG (Bottom Left)
    LOG_X = WINDOW_PADDING
    LOG_Y = ACTION_WINDOW_Y + ACTION_WINDOW_HEIGHT + WINDOW_PADDING
    LOG_WIDTH = ACTION_WINDOW_WIDTH
    LOG_HEIGHT = BOTTOM_LOG_HEIGHT

    # MAP WINDOW (Bottom Right)
    MAP_X = SIDEBAR_X
    MAP_Y = LOG_Y
    MAP_WIDTH = SIDEBAR_WIDTH
    MAP_HEIGHT = BOTTOM_LOG_HEIGHT

class WindowSettings:
    MAX_MESSAGES = 5
    LINE_HEIGHT = 22
    TEXT_PADDING = 10
    WELCOME_MESSAGE = ["Welcome to the Dungeon!", "Use arrows to move."]
    TYPING_SPEED = 0.25 # Characters per frame for the typewriter effect

class PlayerSettings:
    MOVEMENT_COOLDOWN = 2000 # Time in milliseconds between allowed movements to prevent spamming
    ANIMATION_SPEED = 1 # Pixels per frame for smooth movement

class MonsterSettings:
    CHASE_RADIUS = 3  # Manhattan distance
    IDLE_CHANCE = 0.2 # 1 in 5 chance to stand still
    REPELLENT_DURATION = 5 # Number of turns the repellent effect lasts
    ANIMATION_SPEED = 1 # Pixels per frame for smooth movement

class LightSettings:
    DEFAULT_RADIUS = 1
    TORCH_RADIUS = 2
    TORCH_DURATION = 5
    LANTERN_RADIUS = 5
    LANTERN_DURATION = 10

class ItemSettings:
    # Point values for treasures
    TREASURE_SCORE_VALUES = {
        'Gold': 10,
        'Ruby': 50,
        'Sapphire': 100,
        'Emerald': 150,
        'Diamond': 500
    }

    # Digging probabilities (must be between 0.0 and 1.0)
    # The higher the number, the more common it is.
    SPAWN_CHANCE = {
        'Gold': 0.25,
        'Monster Repellent': 0.20,
        'Torch': 0.25,
        'Lantern': 0.10,
        'Ruby': 0.10,
        'Sapphire': 0.05,
        'Emerald': 0.025,
        'Diamond': 0.01
    }

    # UI Sort Order (The requested layout)
    INITIAL_INVENTORY = {
        'Candle': 1, 'Shovel': 1, 'Map': 1,
        'Torch': 3, 'Lantern': 0, 'Monster Repellent': 2,
        'Gold': 0, 'Ruby': 0, 'Diamond': 0, 'Emerald': 0,
        'Key': 0
        }

class FontSettings:
    FONT = 'font/Pixeled.ttf'
    MESSAGE_SIZE = 20
    ENDGAME_SIZE = 80
    DEFAULT_COLOR = 'white'
    LAST_MESSAGE_COLOR = 'yellow'

class AudioSettings:
    pass

class AssetPaths:
    # Images
    GRAPHICS_DIR = 'graphics/'

    # Sprites
    PLAYER = os.path.join(GRAPHICS_DIR, 'human_male.png')
    MONSTER = os.path.join(GRAPHICS_DIR, 'dragon.png')

    # Door
    CLOSED_DOOR = os.path.join(GRAPHICS_DIR, 'closed_door.png')
    OPEN_DOOR = os.path.join(GRAPHICS_DIR, 'open_door.png')

    # Floor Tiles
    DIRT_TILE = os.path.join(GRAPHICS_DIR, 'dirt_0_new.png')
    DUG_TILE = os.path.join(GRAPHICS_DIR, 'cobble_blood6.png')
    WALL_TILE = os.path.join(GRAPHICS_DIR, 'brick_brown_0.png')

    # Audio
    SOUND_DIR = 'sound/'
    MOVE_SOUND = os.path.join(SOUND_DIR, 'sfx_movement_footstepsloop4_slow.wav')
    BOUNDARY_SOUND = os.path.join(SOUND_DIR, 'pokemon_wall_bump_sound_effect.mp3')
    KEY_SOUND = os.path.join(SOUND_DIR, 'sfx_coin_single1.wav')