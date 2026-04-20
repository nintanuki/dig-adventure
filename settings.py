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
    BASE_RADIUS = 0.5
    BASE_DURATION = 1
    
    # Match: 0.5 radius for 1 turn (doesn't really have room to shrink)
    MATCH_RADIUS = BASE_DURATION * 1
    MATCH_DURATION = BASE_RADIUS * 1
    
    # Torch: Starts at 2.0, shrinks over 4 turns
    TORCH_RADIUS = BASE_RADIUS * 4
    TORCH_DURATION = BASE_RADIUS * 4
    
    # Lantern: Starts at 5.0, shrinks over 10 turns
    LANTERN_RADIUS = BASE_RADIUS * 10
    LANTERN_DURATION = BASE_RADIUS * 10

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
        'GOLD COINS': 0.25,
        'MONSTER REPELLENT': 0.10,
        'MATCH': 0.25,
        'TORCH': 0.15,
        'LANTERN': 0.05,
        'RUBY': 0.10,
        'SAPPHIRE': 0.05,
        'EMERALD': 0.025,
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

    # UI Sort Order (The requested layout)
    INITIAL_INVENTORY = {
        'MATCH': 1, 'TORCH': 0, 'LANTERN': 0,
        'MONSTER REPELLENT': 0,
        'GOLD COINS': 0, 'RUBY': 0, 'SAPPHIRE': 0, 'EMERALD': 0, 'DIAMOND': 0, 
        'KEY DETECTOR': 0, 'MAP': 0, 'KEY': 0
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
    DIRT_GRAPHICS_DIR = os.path.join(GRAPHICS_DIR, 'dirt/')

    # Sprites
    PLAYER = os.path.join(GRAPHICS_DIR, 'human_male.png')
    CHAINMAIL = os.path.join(GRAPHICS_DIR, 'chainmail_3.png')
    ARAGORN_SHIRT = os.path.join(GRAPHICS_DIR, 'aragorn.png')
    LEG_ARMOR1 = os.path.join(GRAPHICS_DIR, 'leg_armor_1.png')
    LEG_ARMOR4 = os.path.join(GRAPHICS_DIR, 'leg_armor_4.png')
    BLUE_GOLD_BOOTS = os.path.join(GRAPHICS_DIR, 'blue_gold.png')
    MIDDLE_BROWN_BOOTS = os.path.join(GRAPHICS_DIR, 'middle_ybrown.png')
    BROWN_WIZARD_HAT = os.path.join(GRAPHICS_DIR, 'wizard_brown.png')

    MONSTER = os.path.join(GRAPHICS_DIR, 'dragon.png')

    # Door
    CLOSED_DOOR = os.path.join(GRAPHICS_DIR, 'closed_door.png')
    OPEN_DOOR = os.path.join(GRAPHICS_DIR, 'open_door.png')

    # Floor Tiles
    DIRT_TILES = [
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_0_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_0_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_1_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_1_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_2_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_2_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_east_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_east_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_full_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_full_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_north_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_north_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_northeast_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_northeast_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_northwest_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_northwest_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_south_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_south_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_southeast_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_southeast_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_southwest_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_southwest_old.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_west_new.png'),
        os.path.join(DIRT_GRAPHICS_DIR, 'dirt_west_old.png')
    ]

    DUG_TILE = os.path.join(GRAPHICS_DIR, 'cobble_blood6.png')
    WALL_TILE = os.path.join(GRAPHICS_DIR, 'brick_brown_0.png')

    # Audio
    SOUND_DIR = 'sound/'
    MOVE_SOUND = os.path.join(SOUND_DIR, 'sfx_movement_footstepsloop4_slow.wav')
    BOUNDARY_SOUND = os.path.join(SOUND_DIR, 'pokemon_wall_bump_sound_effect.mp3')
    KEY_SOUND = os.path.join(SOUND_DIR, 'sfx_coin_single1.wav')

class DebugSettings:
    """Settings related to debugging features."""
    GRID = False # Toggle grey outlines for debugging
    MUTE = False # Set to True to mute all sounds during testing, False to enable sounds
    NO_FOG = True # Set to True to disable fog of war