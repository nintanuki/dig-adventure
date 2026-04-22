# Using classes for namespacing so they can be easily changed here and accessed from other files.
import os

class ScreenSettings:
    """Class to hold all the settings related to the screen."""
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH,HEIGHT)
    FPS = 60
    CRT_ALPHA_RANGE = (75, 90)
    CRT_SCANLINE_HEIGHT = 3

class GridSettings:
    RAW_TILE_SIZE = 16 # The actual size of the image files (in pixels)
    SCALE_FACTOR = 2 # The multiplier for how big they will appear in-game
    TILE_SIZE = RAW_TILE_SIZE * SCALE_FACTOR # What rest the code will use for grid snapping

class UISettings:
    LEFT_MARGIN = 64
    TOP_MARGIN = 56
    GAP = GridSettings.TILE_SIZE

    BORDER_COLOR = 'white'
    BORDER_RADIUS = 5
    DOOR_UNLOCK_BORDER_FLASH_MS = 2500

    SIDEBAR_WIDTH = 200
    BOTTOM_LOG_HEIGHT = 150

    COLS = 14
    ROWS = 10
    ACTION_WINDOW_WIDTH = COLS * GridSettings.TILE_SIZE
    ACTION_WINDOW_HEIGHT = ROWS * GridSettings.TILE_SIZE

    ACTION_WINDOW_X = LEFT_MARGIN
    ACTION_WINDOW_Y = TOP_MARGIN

    SIDEBAR_X = ACTION_WINDOW_X + ACTION_WINDOW_WIDTH + GAP
    SIDEBAR_Y = TOP_MARGIN
    SIDEBAR_HEIGHT = ACTION_WINDOW_HEIGHT

    LOG_X = LEFT_MARGIN
    LOG_Y = ACTION_WINDOW_Y + ACTION_WINDOW_HEIGHT + GAP
    LOG_WIDTH = ACTION_WINDOW_WIDTH
    LOG_HEIGHT = BOTTOM_LOG_HEIGHT

    MAP_X = SIDEBAR_X
    MAP_Y = LOG_Y
    MAP_WIDTH = SIDEBAR_WIDTH
    MAP_HEIGHT = BOTTOM_LOG_HEIGHT
    MINIMAP_PADDING = 10

    SCORE_X = 72
    SCORE_Y = 20
    CURRENT_SCORE_X = SIDEBAR_X + 16
    CURRENT_SCORE_Y = SCORE_Y
    LEVEL_X = LEFT_MARGIN
    LEVEL_Y = ScreenSettings.HEIGHT - 34
    DUNGEON_NAME_Y = LEVEL_Y + 15

class GameSettings:
    LEVEL_TRANSITION_MS = 2000
    HIGH_SCORE_FILE = 'high_score.txt'

class WindowSettings:
    MAX_MESSAGES = 5
    LINE_HEIGHT = 22
    TEXT_PADDING = 16
    WELCOME_MESSAGE = [
        "B - LIGHT A TORCH OR LANTERN",
        "A - DIG AND UNLOCK DOORS",
        "X - USE KEY DETECTOR",
        "Y - USE MONSTER REPELLENT",
        "LB / C - USE INVISIBILITY CLOAK"]
    TYPING_SPEED = 0.25 # Characters per frame for the typewriter effect

class PlayerSettings:
    ANIMATION_SPEED = 1 # Pixels per frame for smooth movement

class MonsterSettings:
    COUNT = 2
    CHASE_RADIUS = 3  # Manhattan distance
    IDLE_CHANCE = 0.3 
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
    INVISIBILITY_CLOAK_DURATION = 5
    LEVEL_SCOPED_ITEMS = {"KEY", "MAP", "MAGIC MAP", "KEY DETECTOR"}

    TREASURE_SCORE_VALUES = {
        'GOLD COINS': 1,
        'RUBY': 50,
        'SAPPHIRE': 100,
        'EMERALD': 200,
        'DIAMOND': 500
    }

    SHOP PRICES = {
        'MATCH': 50,
        'TORCH': 250,
        'MONSTER REPELLENT': 500,
        'LANTERN': 1000,
        'INVISIBILITY CLOAK': 5000,
    }

    # Digging probabilities (must be between 0.0 and 1.0)
    # The higher the number, the more common it is.
    SPAWN_CHANCE = {
        'MONSTER REPELLENT': 0.10,
        'MATCH': 0.25,
        'TORCH': 0.15,
        'LANTERN': 0.05,
        'KEY DETECTOR': 0.05,
        'INVISIBILITY CLOAK': 0.05,
        'MAGIC MAP': 0.01,
        'GOLD COINS': 0.25,
        'RUBY': 0.10,
        'SAPPHIRE': 0.05,
        'EMERALD': 0.025,
        'DIAMOND': 0.01
    }

    SPAWN_QUANTITIES = {
        'GOLD COINS': (1, 200),
        'RUBY': (1, 10),
        'SAPPHIRE': (1, 5),
        'EMERALD': (1, 3),
        'MATCH': (1, 10),
        'TORCH': (1, 5),
        'MONSTER REPELLENT': (1, 5)
        # Anything not here will default to 1
    }

    INITIAL_INVENTORY = {
        'MATCH': 1,
        #  Uncomment below for testing
        # 'KEY': 1,
        # 'INVISIBILITY CLOAK': 100,
        # 'MAP': 1,
        # 'MAGIC MAP': 1,
        # 'TORCH': 999,
        # 'LANTERN': 999,
        # 'MONSTER REPELLENT': 999,
        # 'KEY DETECTOR': 1,
        # 'GOLD COINS': 0,
        # 'RUBY': 0,
        # 'SAPPHIRE': 0,
        # 'EMERALD': 0,
        # 'DIAMOND': 0,
        }

class FontSettings:
    FONT = 'font/Pixeled.ttf'
    MESSAGE_SIZE = 8
    SCORE_SIZE = 12
    HUD_SIZE = 10
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
    MUTE_MUSIC = False  # Mute music but keep SFX
    MUSIC_VOLUME = 0.2  # Hardcoded volume (0.0 to 1.0)

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
    MONSTER_CHASE_SOUND = os.path.join(SOUND_DIR, 'sfx_sound_nagger1.wav')
    COIN_SOUND = os.path.join(SOUND_DIR, 'sfx_coin_cluster3.wav')
    LIGHT_SOUND = os.path.join(SOUND_DIR, 'Torch Whoosh Sound Effect.mp3')
    MATCH_LIGHT_SOUND = os.path.join(SOUND_DIR, 'Lighting A Match Sound Effect.mp3')
    VANISH_SOUND = os.path.join(SOUND_DIR, 'Vanish Sound Effect.mp3')
    SHORT_SPRAY_SOUND = os.path.join(SOUND_DIR, 'short_spray.mp3')
    LONG_SPRAY_SOUND = os.path.join(SOUND_DIR, 'long_spray.mp3')
    FOUND_DETECTOR_SOUND = os.path.join(SOUND_DIR, 'sfx_alarm_loop3.wav')
    HOT_DETECTOR_SOUND = os.path.join(SOUND_DIR, 'sfx_alarm_loop7.wav')
    WARM_DETECTOR_SOUND = os.path.join(SOUND_DIR, 'sfx_alarm_loop6.wav')

    # Music
    MUSIC_DIR = 'music/'
    MUSIC_TRACKS = [
        os.path.join(MUSIC_DIR, 'Goof Troop SNES - Illusion.mp3'),
        os.path.join(MUSIC_DIR, 'Goof Troop SNES - Lose My Way.mp3'),
    ]

class DebugSettings:
    """Settings related to debugging features."""
    GRID = True # Toggle grey outlines for debugging
    MUTE = False # Set to True to mute all sounds during testing, False to enable sounds
    NO_FOG = False # Set to True to disable fog of war
    SPAWN_LOG = True # Print spawn/item placement summary at dungeon setup