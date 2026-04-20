import pygame
from settings import *

class AudioManager:
    def __init__(self):
        """Initialize the audio manager and load all necessary sound effects."""

        # Load the movement sound effect and set up a channel for it
        self.move_sound = pygame.mixer.Sound(AssetPaths.MOVE_SOUND)
        self.movement_channel = pygame.mixer.Channel(0)

        self.boundary_sound = pygame.mixer.Sound(AssetPaths.BOUNDARY_SOUND)
        self.boundary_channel = pygame.mixer.Channel(1)

        self.key_sound = pygame.mixer.Sound(AssetPaths.KEY_SOUND)
        self.key_channel = pygame.mixer.Channel(2)

    def play_move_sound(self):
        """Play the movement sound effect."""
        if AudioSettings.MUTE or DebugSettings.MUTE: return
        # Using a specific channel prevents the sound from being 
        # cut off by other random sounds
        self.movement_channel.play(self.move_sound)

    def play_boundary_sound(self):
        """Play the boundary collision sound effect."""
        if AudioSettings.MUTE or DebugSettings.MUTE: return
        self.boundary_channel.play(self.boundary_sound)

    def play_key_sound(self):
        """Play a sound effect for when the key is discovered."""
        if AudioSettings.MUTE or DebugSettings.MUTE: return
        self.key_channel.play(self.key_sound)

    def update(self):
        """Update method for the audio manager, used for volume control and looping music."""
        pass