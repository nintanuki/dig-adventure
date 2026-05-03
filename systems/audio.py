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
        'menu_move': 12,
        'menu_select': 13,
    }

    def __init__(self):
        """
        Initialize the audio manager and load all necessary sound effects.
        Uses fixed channels for important sounds to prevent them from being cut off by other effects.
        """
        pygame.mixer.set_num_channels(len(self.CHANNEL_IDS))

        # Track last played song to avoid back-to-back repeats.
        self._last_bgm_track = None
        self._music_mode = "normal"

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
        self.menu_move_sound = self._load_sound(AssetPaths.MENU_MOVE_SOUND)
        self.menu_select_sound = self._load_sound(AssetPaths.MENU_SELECT_SOUND)

        self.channels = {
            name: pygame.mixer.Channel(channel_id)
            for name, channel_id in self.CHANNEL_IDS.items()
        }

    def _load_sound(self, path: str) -> pygame.mixer.Sound:
        """Load one sound effect from disk.

        Args:
            path: File path to the sound asset.

        Returns:
            pygame.mixer.Sound: Loaded sound object.
        """
        return pygame.mixer.Sound(path)

    def play_random_bgm(self):
        """Selects a random track (avoiding the last played) and starts looping it."""
        if AudioSettings.MUTE or AudioSettings.MUTE_MUSIC:
            return

        if not AssetPaths.MUSIC_TRACKS:
            print("Warning: No music tracks found in AssetPaths.MUSIC_TRACKS")
            return

        # Exclude the last played track so the same song never repeats back-to-back.
        available = [t for t in AssetPaths.NORMAL_MUSIC_TRACKS if t != self._last_bgm_track]
        if not available:
            available = AssetPaths.MUSIC_TRACKS
        track = random.choice(available)
        self._last_bgm_track = track
        
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(AudioSettings.MUSIC_VOLUME)
            # Use loops=-1 for indefinite looping.
            pygame.mixer.music.play(loops=-1)
        except pygame.error as e:
            # Gracefully handle unsupported or missing audio assets.
            print(f"Could not load music track {track}: {e}")

    def play_chase_music(self) -> None:
        """Switch to battle music while a monster is chasing."""
        if AudioSettings.MUTE or AudioSettings.MUTE_MUSIC:
            return

        if self._music_mode == "chase":
            return

        self._music_mode = "chase"
        pygame.mixer.music.load(AssetPaths.CHASE_MUSIC)
        pygame.mixer.music.set_volume(AudioSettings.MUSIC_VOLUME)
        pygame.mixer.music.play(loops=-1)


    def play_normal_music(self) -> None:
        """Return to normal background music."""
        if AudioSettings.MUTE or AudioSettings.MUTE_MUSIC:
            return

        if self._music_mode == "normal":
            return

        self._music_mode = "normal"
        self.play_random_bgm()

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

    # Logical SFX name -> (channel, attribute holding the loaded Sound).
    SOUND_BINDINGS = {
        'move':           ('movement',       'move_sound'),
        'boundary':       ('boundary',       'boundary_sound'),
        'key':            ('key',            'key_sound'),
        'scream':         ('scream',         'scream_sound'),
        'dig':            ('dig',            'dig_sound'),
        'monster_chase':  ('monster_chase',  'monster_chase_sound'),
        'coin':           ('coin',           'coin_sound'),
        'light':          ('light',          'light_sound'),
        'match_light':    ('light',          'match_light_sound'),
        'vanish':         ('vanish',         'vanish_sound'),
        'short_spray':    ('spray',          'short_spray_sound'),
        'long_spray':     ('spray',          'long_spray_sound'),
        'detector_found': ('found_detector', 'found_detector_sound'),
        'detector_hot':   ('detector',       'hot_detector_sound'),
        'detector_warm':  ('detector',       'warm_detector_sound'),
        'menu_move':      ('menu_move',      'menu_move_sound'),
        'menu_select':    ('menu_select',    'menu_select_sound'),
    }

    def play(self, name: str) -> None:
        """Play one named sound effect on its reserved channel.

        Args:
            name: A key in SOUND_BINDINGS (e.g. 'dig', 'coin', 'menu_move').
        """
        if AudioSettings.MUTE or DebugSettings.MUTE:
            return
        channel_name, sound_attr = self.SOUND_BINDINGS[name]
        self.channels[channel_name].play(getattr(self, sound_attr))

    def play_repellent_sound(self, cans_left: int) -> None:
        """Play a longer can-empty spray when repellent runs out, otherwise the short variant.

        Args:
            cans_left: Repellent count remaining after the use.
        """
        self.play('long_spray' if cans_left == 0 else 'short_spray')
