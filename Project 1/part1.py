import numpy as np
import soundfile as sf
import sounddevice as sd


def ck1():
    duration = 10.0
    fs = 48000
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
    status = sd.wait()

    sd.play(recording)
    status = sd.wait()
    sd.stop()


def ck2():
    duration = 10.0
    sound_file = "play.wav"

    sound_data, fs = sf.read(sound_file, dtype='float32')
    recording = sd.playrec(sound_data, fs, channels=2)
    status = sd.wait()

    sd.play(recording)
    status = sd.wait()
    sd.stop()


if __name__ == "__main__":
    ck1()
    # ck2()