import pygame
from settings import *

class AudioManager:
    def __init__(self):
        """
        Initialize the audio manager and load all necessary sound effects.
        Uses fixed channels for important sounds to prevent them from being cut off by other effects.
        """

        # Load the movement sound effect and set up a channel for it
        self.move_sound = pygame.mixer.Sound(AssetPaths.MOVE_SOUND)
        self.movement_channel = pygame.mixer.Channel(0)

        self.boundary_sound = pygame.mixer.Sound(AssetPaths.BOUNDARY_SOUND)
        self.boundary_channel = pygame.mixer.Channel(1)

        self.key_sound = pygame.mixer.Sound(AssetPaths.KEY_SOUND)
        self.key_channel = pygame.mixer.Channel(2)

        self.scream_sound = pygame.mixer.Sound(AssetPaths.SCREAM_SOUND)
        self.scream_channel = pygame.mixer.Channel(3)

        self.dig_sound = pygame.mixer.Sound(AssetPaths.DIG_SOUND)
        self.dig_channel = pygame.mixer.Channel(4)

        self.monster_chase_sound = pygame.mixer.Sound(AssetPaths.MONSTER_CHASE_SOUND)
        self.monster_chase_channel = pygame.mixer.Channel(5)

        self.coin_sound = pygame.mixer.Sound(AssetPaths.COIN_SOUND)
        self.coin_channel = pygame.mixer.Channel(6)

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

    def play_scream_sound(self):
        """Play a scream sound effect for when the player dies."""
        if AudioSettings.MUTE or DebugSettings.MUTE: return
        self.scream_channel.play(self.scream_sound)

    def play_dig_sound(self):
        """Play a digging sound effect for when the player digs."""
        if AudioSettings.MUTE or DebugSettings.MUTE: return
        self.dig_channel.play(self.dig_sound)

    def play_monster_chase_sound(self):
        """Play a sound effect for when the monster is chasing the player."""
        if AudioSettings.MUTE or DebugSettings.MUTE: return
        self.monster_chase_channel.play(self.monster_chase_sound)

    def play_coin_sound(self):
        """Play a sound effect for when the player collects a coin."""
        if AudioSettings.MUTE or DebugSettings.MUTE: return
        self.coin_channel.play(self.coin_sound)

    def update(self):
        """Update method for the audio manager, used for volume control and looping music."""
        pass