import numpy as np
import sounddevice as sd

if __name__ == "__main__":
    fs = 48000      # sampling rate, Hz, must be integer
    duration = 5.0  # in seconds, may be float
    f1 = 1000.0     # sine frequency, Hz, may be float
    f2 = 10000.0

    myarray = np.arange(fs * duration)
    myarray = np.sin(2 * np.pi * f1 / fs * myarray) / 2 + np.sin(2 * np.pi * f2 / fs * myarray) / 2

    sd.play(myarray, fs)
    status = sd.wait()
    sd.stop()
