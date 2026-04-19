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
    # 1-tile padding from the very edge of the window
    WINDOW_PADDING = GridSettings.TILE_SIZE
    
    # Action Window Starting Points (Top-Left)
    ACTION_WINDOW_X = WINDOW_PADDING
    ACTION_WINDOW_Y = WINDOW_PADDING

    # UI Element Sizes
    SIDEBAR_WIDTH = 200 
    BOTTOM_LOG_HEIGHT = 150
    
    # The actual playable area dimensions (Screen - UI - Padding)
    # This tells the drawing loop where to STOP
    ACTION_WINDOW_WIDTH = ScreenSettings.WIDTH - SIDEBAR_WIDTH - (WINDOW_PADDING * 2)
    ACTION_WINDOW_HEIGHT = ScreenSettings.HEIGHT - BOTTOM_LOG_HEIGHT - (WINDOW_PADDING * 2)

    # This ensures we only draw WHOLE tiles for the dungeon area
    COLS = ACTION_WINDOW_WIDTH // GridSettings.TILE_SIZE
    ROWS = ACTION_WINDOW_HEIGHT // GridSettings.TILE_SIZE

class PlayerSettings:
    MOVEMENT_COOLDOWN = 500 # Time in milliseconds between allowed movements to prevent spamming

class FontSettings:
    FONT = 'font/Pixeled.ttf'
    SMALL = 10
    MEDIUM = 20
    LARGE = 30
    COLOR = 'white'

class AudioSettings:
    pass

class AssetPaths:
    # Images
    GRAPHICS_DIR = 'graphics/'
    PLAYER = os.path.join(GRAPHICS_DIR, 'human_male.png')

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