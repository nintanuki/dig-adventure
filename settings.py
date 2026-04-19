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
    MAX_MESSAGES = 6
    LINE_HEIGHT = 22
    TEXT_PADDING = 10
    WELCOME_MESSAGE = ["Welcome to the Dungeon!", "Use arrows to move."]

class PlayerSettings:
    MOVEMENT_COOLDOWN = 500 # Time in milliseconds between allowed movements to prevent spamming

class FontSettings:
    FONT = 'font/Pixeled.ttf'
    SIZE = 20
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
    WALL_TILE = os.path.join(GRAPHICS_DIR, 'brick_brown_0.png')

    # Audio
    SOUND_DIR = 'sound/'
    MOVE_SOUND = os.path.join(SOUND_DIR, 'sfx_movement_footstepsloop4_slow.wav')
    BOUNDARY_SOUND = os.path.join(SOUND_DIR, 'pokemon_wall_bump_sound_effect.mp3')