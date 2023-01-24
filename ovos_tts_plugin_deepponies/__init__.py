import soundfile as sf
from ovos_plugin_manager.templates.tts import TTS

from ovos_tts_plugin_deepponies.deepponies import DeepPoniesEngine


class DeepPoniesTTSPlugin(TTS):
    def __init__(self, *args, **kwargs):
        # in here you should specify if your plugin return wav or mp3 files
        # you should also specify any valid ssml tags
        ssml_tags = []
        super().__init__(*args, **kwargs, audio_ext="wav", ssml_tags=ssml_tags)
        # read config settings for your plugin if any
        self.rate = self.config.get("rate", 1.0)
        self.voice = self.config.get("voice")
        if not self.voice or self.voice == "default":
            self.voice = "Heavy"
        self.engine = DeepPoniesEngine()
        from pprint import pprint
        pprint(self.engine.speaker2id.keys())

    def get_tts(self, sentence, wav_file, voice=None):
        voice = voice or self.voice
        audio = self.engine.synthesize(sentence,
                                       speaker_name=voice,
                                       duration_control=1 / self.rate)
        sf.write(wav_file, audio, 22050)
        return wav_file, None

    @property
    def available_languages(self):
        """Return languages supported by this TTS implementation in this state
        This property should be overridden by the derived class to advertise
        what languages that engine supports.
        Returns:
            set: supported languages
        """
        # TODO - what langs can this TTS handle?
        return {"en-us"}


# sample valid configurations per language
# "display_name" and "offline" provide metadata for UI
# "priority" is used to calculate position in selection dropdown
#       0 - top, 100-bottom
# all other keys represent an example valid config for the plugin
DeepPoniesTTSPluginConfig = {
    "en": [{"lang": "en",
            "display_name": f"{voice} (DeepPonies)",
            "voice": voice,
            "priority": 50,
            "offline": True}]
    for voice in ['Barack Obama', 'Billie Eilish',
                  'Donald Trump', 'Joe Biden',
                  'Joe Rogan', 'Kanye West',
                  'Kim Kardashian', 'Kratos',
                  'Nameless Hero', 'Franklin',
                  'Michael', 'Trevor', 'Apple Bloom',
                  'Applejack', 'Celestia', 'Cozy Glow',
                  'Discord', 'Fluttershy', 'Granny Smith',
                  'Luna', 'Pinkie Pie', 'Rainbow Dash',
                  'Rarity', 'Scootaloo', 'Spike',
                  'Starlight', 'Sunset Shimmer',
                  'Sweetie Belle', 'Trixie',
                  'Twilight Sparkle', 'Adachi Tohru',
                  'Chie Satonaka', 'Kanji Tatsumi',
                  'Nanako Dojima', 'Naoto Shirogane',
                  'Rise Kujikawa', 'Ryotaro Dojima',
                  'Teddie', 'Yosuke Hanamura',
                  'Yukiko Amagi', 'GLaDOS', 'SpongeBob',
                  'Demoman', 'Engineer', 'Heavy',
                  'Medic', 'Scout', 'Sniper', 'Soldier',
                  'Spy', 'Bart Simpson', 'Homer Simpson']
}

if __name__ == "__main__":
    tts = DeepPoniesTTSPlugin()
    for voice in ['Barack Obama', 'Billie Eilish',
                  'Donald Trump', 'Joe Biden',
                  'Joe Rogan', 'Kanye West',
                  'Kim Kardashian', 'GLaDOS', 'SpongeBob',
                  'Demoman', 'Engineer', 'Heavy',
                  'Medic', 'Scout', 'Sniper', 'Soldier',
                  'Spy', 'Bart Simpson', 'Homer Simpson']:
        tts.get_tts("hello world", f"{voice}.wav", voice=voice)
