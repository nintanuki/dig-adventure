# Using classes for namespacing so they can be easily changed here and accessed from other files.
import os

class ScreenSettings:
    """Class to hold all the settings related to the screen."""
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH,HEIGHT)
    FPS = 60
    CRT_ALPHA_RANGE = (75, 90)

class GridSettings:
    RAW_TILE_SIZE = 16 # The actual size of the image files (in pixels)
    SCALE_FACTOR = 2 # The multiplier for how big they will appear in-game
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
    TEXT_PADDING = 16
    WELCOME_MESSAGE = [
        "YOU FIND YOURSELF IN PITCH BLACK DARKNESS...",
        "B - LIGHT A TORCH OR LANTERN",
        "A - DIG AND UNLOCK DOORS",
        "X - USE KEY DETECTOR",
        "Y - USE MONSTER REPELLENT"]
    TYPING_SPEED = 0.25 # Characters per frame for the typewriter effect

class PlayerSettings:
    MOVEMENT_COOLDOWN = 0 # Time in milliseconds between allowed movements to prevent spamming
    # ^ it doesn't seem like we need this? The game waits for the text to finish before letting you move
    ANIMATION_SPEED = 1 # Pixels per frame for smooth movement

class MonsterSettings:
    CHASE_RADIUS = 3  # Manhattan distance
    IDLE_CHANCE = 0.2 # 1 in 5 chance to stand still
    REPELLENT_DURATION = 5 # Number of turns the repellent effect lasts
    ANIMATION_SPEED = 1 # Pixels per frame for smooth movement

class LightSettings:
    DEFAULT_RADIUS = 0    # Game starts in total darkness
    BASE_RADIUS = 2
    BASE_DURATION = 3
    
    MATCH_RADIUS = BASE_RADIUS * 1
    MATCH_DURATION = BASE_DURATION * 1
    
    TORCH_RADIUS = BASE_RADIUS * 1.5
    TORCH_DURATION = BASE_DURATION * 1.5
    
    LANTERN_RADIUS = BASE_RADIUS * 3
    LANTERN_DURATION = BASE_DURATION * 3

class ItemSettings:
    # Point values for treasures, we will use this later when we make our score system
    TREASURE_SCORE_VALUES = {
        'GOLD COINS': 1,
        'RUBY': 50,
        'SAPPHIRE': 100,
        'EMERALD': 150,
        'DIAMOND': 500
    }

    # Digging probabilities (must be between 0.0 and 1.0)
    # The higher the number, the more common it is.
    SPAWN_CHANCE = {
        'MONSTER REPELLENT': 0.10,
        'MATCH': 0.20,
        'TORCH': 0.10,
        'LANTERN': 0.05,
        'GOLD COINS': 0.20,
        'RUBY': 0.10,
        'SAPPHIRE': 0.05,
        'EMERALD': 0.02,
        'DIAMOND': 0.01
    }

    SPAWN_QUANTITIES = {
        'GOLD COINS': (1, 100),
        'RUBY': (1, 3),
        'SAPPHIRE': (1, 2),
        'MATCH': (1, 5),
        'TORCH': (1, 3),
        'MONSTER REPELLENT': (1, 1)
        # Anything not here will default to 1
    }

    INITIAL_INVENTORY = {
        'MATCH': 1,
        'TORCH': 3,
        # 'LANTERN': 0,
        # 'MONSTER REPELLENT': 0,
        # 'GOLD COINS': 0,
        # 'RUBY': 0,
        # 'SAPPHIRE': 0,
        # 'EMERALD': 0,
        # 'DIAMOND': 0,
        # 'KEY DETECTOR': 0,
        # 'MAP': 1,
        # 'KEY': 0
        }

class FontSettings:
    FONT = 'font/Pixeled.ttf'
    MESSAGE_SIZE = 8
    ENDGAME_SIZE = 32
    DEFAULT_COLOR = 'white'
    LAST_MESSAGE_COLOR = 'yellow'

    WORD_COLORS = {
        "RUBY": "red",
        "SAPPHIRE": "blue",
        "EMERALD": "green",
        "KEY": "yellow",
        "MONSTER": "purple",
        "MONSTER REPELLENT": "purple"
    }

class AudioSettings:
    MUTE = False

class AssetPaths:
    # Images
    GRAPHICS_DIR = 'graphics/'

    # Sprites
    PLAYER = os.path.join(GRAPHICS_DIR, 'tile_0097.png')
    MONSTER = os.path.join(GRAPHICS_DIR, 'tile_0121.png')

    # Door
    CLOSED_DOOR = os.path.join(GRAPHICS_DIR, 'tile_0045.png')
    OPEN_DOOR = os.path.join(GRAPHICS_DIR, 'tile_0021.png')

    # Floor Tiles (this no longer needs to be a list, unless we want to add variety later.)
    DIRT_TILES = [
        os.path.join(GRAPHICS_DIR, 'tile_0000.png'),
    ]

    DUG_TILE = os.path.join(GRAPHICS_DIR, 'tile_0012.png')
    WALL_TILE = os.path.join(GRAPHICS_DIR, 'tile_0014.png')

    # CRT Effect
    TV = os.path.join(GRAPHICS_DIR, 'tv.png')

    # Audio
    SOUND_DIR = 'sound/'
    MOVE_SOUND = os.path.join(SOUND_DIR, 'sfx_movement_footstepsloop4_slow.wav')
    DIG_SOUND = os.path.join(SOUND_DIR, 'minecraft_digging_dirt_sound_effect.mp3')
    BOUNDARY_SOUND = os.path.join(SOUND_DIR, 'pokemon_wall_bump_sound_effect.mp3')
    KEY_SOUND = os.path.join(SOUND_DIR, 'sfx_coin_single1.wav')
    SCREAM_SOUND = os.path.join(SOUND_DIR, 'wilhelm_scream.wav')

class DebugSettings:
    """Settings related to debugging features."""
    GRID = True # Toggle grey outlines for debugging
    MUTE = False # Set to True to mute all sounds during testing, False to enable sounds
    NO_FOG = True # Set to True to disable fog of war