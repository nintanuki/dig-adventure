class ScreenSettings:
    """Class to hold all the settings related to the screen."""
    WIDTH = 800
    HEIGHT = 600
    RESOLUTION = (WIDTH,HEIGHT)
    CENTER = (WIDTH / 2, HEIGHT / 2)
    FPS = 120

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