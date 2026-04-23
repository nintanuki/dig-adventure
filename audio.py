import pygame
import random
from settings import *

class AudioManager:
    """Load, route, and play game music and sound effects across fixed channels."""

    CHANNEL_IDS = {
        'movement': 0,
        'boundary': 1,
        'key': 2,
        'scream': 3,
        'dig': 4,
        'monster_chase': 5,
        'coin': 6,
        'spray': 7,
        'found_detector': 8,
        'detector': 9,
        'light': 10,
        'vanish': 11,
    }

    def __init__(self):
        """
        Initialize the audio manager and load all necessary sound effects.
        Uses fixed channels for important sounds to prevent them from being cut off by other effects.
        """
        pygame.mixer.set_num_channels(len(self.CHANNEL_IDS))

        # Initialize Music
        self.play_random_bgm()

        self.move_sound = self._load_sound(AssetPaths.MOVE_SOUND)
        self.boundary_sound = self._load_sound(AssetPaths.BOUNDARY_SOUND)
        self.key_sound = self._load_sound(AssetPaths.KEY_SOUND)
        self.scream_sound = self._load_sound(AssetPaths.SCREAM_SOUND)
        self.dig_sound = self._load_sound(AssetPaths.DIG_SOUND)
        self.monster_chase_sound = self._load_sound(AssetPaths.MONSTER_CHASE_SOUND)
        self.coin_sound = self._load_sound(AssetPaths.COIN_SOUND)
        self.coin_sound.set_volume(0.5)
        self.light_sound = self._load_sound(AssetPaths.LIGHT_SOUND)
        self.match_light_sound = self._load_sound(AssetPaths.MATCH_LIGHT_SOUND)
        self.vanish_sound = self._load_sound(AssetPaths.VANISH_SOUND)
        self.short_spray_sound = self._load_sound(AssetPaths.SHORT_SPRAY_SOUND)
        self.long_spray_sound = self._load_sound(AssetPaths.LONG_SPRAY_SOUND)
        self.found_detector_sound = self._load_sound(AssetPaths.FOUND_DETECTOR_SOUND)
        self.hot_detector_sound = self._load_sound(AssetPaths.HOT_DETECTOR_SOUND)
        self.warm_detector_sound = self._load_sound(AssetPaths.WARM_DETECTOR_SOUND)

        self.channels = {
            name: pygame.mixer.Channel(channel_id)
            for name, channel_id in self.CHANNEL_IDS.items()
        }

    def _load_sound(self, path: str) -> pygame.mixer.Sound:
        """Load one sound effect from disk.

        Args:
            path (str): File path to the sound asset.

        Returns:
            pygame.mixer.Sound: Loaded sound object.
        """
        return pygame.mixer.Sound(path)

    def _play_on_channel(self, channel_name: str, sound: pygame.mixer.Sound) -> None:
        """Play a sound effect on its reserved channel.

        Args:
            channel_name (str): Logical channel key.
            sound (pygame.mixer.Sound): Sound to play.
        """
        if AudioSettings.MUTE or DebugSettings.MUTE:
            return
        self.channels[channel_name].play(sound)

    def play_random_bgm(self):
        """Selects a random track and starts looping it."""
        if AudioSettings.MUTE or AudioSettings.MUTE_MUSIC:
            return

        if not AssetPaths.MUSIC_TRACKS:
            print("Warning: No music tracks found in AssetPaths.MUSIC_TRACKS")
            return

        # Select one track for continuous playback.
        track = random.choice(AssetPaths.MUSIC_TRACKS)
        
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(AudioSettings.MUSIC_VOLUME)
            # Use loops=-1 for indefinite looping.
            pygame.mixer.music.play(loops=-1)
        except pygame.error as e:
            # Gracefully handle unsupported or missing audio assets.
            print(f"Could not load music track {track}: {e}")

    def stop_music(self) -> None:
        """Stop the currently playing background track."""
        pygame.mixer.music.stop()

    def toggle_mute(self, resume_music: bool = True) -> bool:
        """Toggle global mute and return the new mute state."""
        AudioSettings.MUTE = not AudioSettings.MUTE

        if AudioSettings.MUTE:
            # Stop all currently playing SFX/music immediately.
            pygame.mixer.stop()
            pygame.mixer.music.stop()
            return True

        if resume_music and not AudioSettings.MUTE_MUSIC:
            self.play_random_bgm()

        return False

    def play_move_sound(self):
        """Play the movement sound effect."""
        self._play_on_channel('movement', self.move_sound)

    def play_boundary_sound(self):
        """Play the boundary collision sound effect."""
        self._play_on_channel('boundary', self.boundary_sound)

    def play_key_sound(self):
        """Play a sound effect for when the key is discovered."""
        self._play_on_channel('key', self.key_sound)

    def play_scream_sound(self):
        """Play a scream sound effect for when the player dies."""
        self._play_on_channel('scream', self.scream_sound)

    def play_dig_sound(self):
        """Play a digging sound effect for when the player digs."""
        self._play_on_channel('dig', self.dig_sound)

    def play_monster_chase_sound(self):
        """Play a sound effect for when the monster is chasing the player."""
        self._play_on_channel('monster_chase', self.monster_chase_sound)

    def play_coin_sound(self):
        """Play a sound effect for when the player collects a coin."""
        self._play_on_channel('coin', self.coin_sound)

    def play_light_sound(self):
        """Play a sound effect for when the player lights a light source."""
        self._play_on_channel('light', self.light_sound)

    def play_match_light_sound(self):
        """Play a sound effect for when the player lights a match."""
        self._play_on_channel('light', self.match_light_sound)

    def play_vanish_sound(self):
        """Play a sound effect for when the player activates invisibility."""
        self._play_on_channel('vanish', self.vanish_sound)

    def play_short_spray_sound(self):
        """Play the normal effect for when the player uses the monster repellent spray."""
        self._play_on_channel('spray', self.short_spray_sound)

    def play_long_spray_sound(self):
        """Play a funnier sound effect for when the player uses the monster repellent spray."""
        self._play_on_channel('spray', self.long_spray_sound)

    def play_repellent_sound(self, cans_left: int):
        """Play repellent spray sound based on remaining can count.

        Args:
            cans_left (int): Remaining repellent cans after use.
        """
        if cans_left == 0:
            self.play_long_spray_sound()
        else:
            self.play_short_spray_sound()

    def play_found_detector_sound(self):
        """Play a sound effect for when the player finds the key detector."""
        self._play_on_channel('found_detector', self.found_detector_sound)

    def play_hot_detector_sound(self):
        """Play the stronger detector sound for nearby key feedback."""
        self._play_on_channel('detector', self.hot_detector_sound)

    def play_warm_detector_sound(self):
        """Play the weaker detector sound for distant key feedback."""
        self._play_on_channel('detector', self.warm_detector_sound)
