#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages(ps: [ps.numpy ps.librosa])"

import numpy as np
import librosa
import math

from autocut.melt import read_fps

def listen_for_start_and_end(video,before_in=0.25,after_out=0.30):
    sr=48000
    audio, _ = librosa.load(video,sr=sr)

    # remove the first and last pieces to avoid button click sounds
    quiet_zone = math.floor(sr / 5)
    audio = audio[quiet_zone:-quiet_zone]
    
    hop_length = 1024
    audio_mfcc = librosa.feature.melspectrogram(y=audio, sr=sr, hop_length=hop_length)

    fs = librosa.core.mel_frequencies()

    buckets = np.sum( audio_mfcc, axis=1 )
    fundamental_frequency = fs[np.argmax(buckets)]

    weights = [1 if f > fundamental_frequency * 0.5 and f < 1.5 * fundamental_frequency else 0 for f in fs]
    weights[np.argmax(buckets)] = 2

    s = np.tensordot(audio_mfcc,fs,axes=([0],[0]))

    cutoff = np.quantile(s, 0.5)

    start = np.max( s[:math.floor(sr / 4 / hop_length)] )
    ending = np.max( s[-math.floor(sr / 4 / hop_length):] )
    mid = np.mean( s[math.floor(len(s) / 3):math.ceil(2 * len(s) / 3)] )
    cutoff = (mid + start + ending) / 100

    s = [1 if x > cutoff else 0 for x in s]

    starting = float(np.nonzero(s)[0][0]) * hop_length / sr
    ending = float(np.nonzero(s)[0][-1]) * hop_length / sr
    
    starting = starting - before_in
    ending = ending + after_out

    if starting < 0:
        starting = 0

    if ending > float(len(audio)) / sr:
        ending = float(len(audio)) / sr
    
    return starting + (float(quiet_zone)/sr), ending + (float(quiet_zone)/sr)

