# Using classes for namespacing so they can be easily changed here and accessed from other files.

class ScreenSettings:
    """Class to hold all the settings related to the screen."""
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH,HEIGHT)
    CENTER = (WIDTH / 2, HEIGHT / 2)
    FPS = 120

class GridSettings:
    # The actual size of the image files
    RAW_TILE_SIZE = 32 
    # The multiplier for how big they will appear in-game
    SCALE_FACTOR = 2 
    # This is what the rest the code will use for grid snapping
    TILE_SIZE = RAW_TILE_SIZE * SCALE_FACTOR 

class PlayerSettings:
    pass

class FontSettings:
    FONT = 'font/Pixeled.ttf'
    SMALL = 10
    MEDIUM = 20
    LARGE = 30
    COLOR = 'white'

class UISettings:
    pass

class AudioSettings:
    pass

class AssetPaths:
    GRAPHICS_DIR = 'graphics/'

    PLAYER = 'human_male.png'

    # Door
    CLOSED_DOOR = 'closed_door.png'
    OPEN_DOOR = 'open_door.png'

    # Floor Tiles
    DIRT_TILE = 'dirt_0_new.png'
    WALL_TILE = 'brick_brown_0.png'