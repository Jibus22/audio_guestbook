import RPi.GPIO as GPIO
import time
from time import sleep
import os
import subprocess
import adafruit_matrixkeypad
import digitalio
import board
import random
import pygame.mixer as mixer
from itertools import chain

################################## BOARD INIT ##################################

PICKUP_BUTTON = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(PICKUP_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

cols = [digitalio.DigitalInOut(x) for x in (board.D16, board.D26, board.D6)]
rows = [digitalio.DigitalInOut(x) for x in (board.D5, board.D22, board.D27, board.D17)]
keys = ((1, 2, 3), (4, 5, 6), (7, 8, 9), ("*", 0, "#"))
flattened_keys = list(tuple(chain.from_iterable(keys)))
keypad = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keys)

############################## AUDIO MIXER INIT ################################

mixer.init(frequency=44100, channels=1, buffer=4096)
audio_channel = mixer.Channel(0)
audio_queue = []
record_process = None

RECORDDIRECTORY = "record"
TIMEMAXREC = 60  # maximum recording time (sec)
AUDIOFILES = {
    "accueil": "audio_files/accueil.wav",
    "menu": "audio_files/menu.wav",
    "beep": "audio_files/beep.wav",
    "prerandom": "audio_files/prerandom.wav",
    "audio3": "audio_files/audio3.wav",
    "audio31": "audio_files/audio31.wav",
}

################################# FUNCTIONS ####################################


def working():
    return GPIO.input(23) == 0


def sleeping():
    return GPIO.input(23) != 0


def clean_audio_queue():
    global audio_queue
    audio_queue = []


def stop_audio():
    if audio_channel.get_busy():
        audio_channel.stop()


def stop_record():
    global record_process
    if record_process is not None and record_process.poll() is None:
        record_process.terminate()

    record_process = None


def stop_all():
    stop_audio()
    clean_audio_queue()
    stop_record()


def get_random_audio():
    """
    Looks for ".wav" files in RECORDDIRECTORY and randomly return one or None
    """
    recordings = [
        os.path.join(RECORDDIRECTORY, file)
        for file in os.listdir(RECORDDIRECTORY)
        if file.endswith(".wav")
    ]
    if recordings and len(recordings) > 0:
        return random.choice(recordings)
    else:
        return None


def audio_queue_handler():
    """
    Queue any audio Sound waiting to be queued if the audio channel is free
    """
    if len(audio_queue) > 0 and audio_channel.get_queue() is None:
        audio_channel.queue(audio_queue.pop(0))


def audio_process_handler(key):
    """
    Stop any current record and clean queue if the user had pressed a registered key
    """
    if len(key) == 0:
        return
    if key[0] in flattened_keys:
        clean_audio_queue()
        stop_record()


def start_recording():
    """
    Launch the 'arecord' subprocess to record a 'timestampedfile.wav' at 44.1kHz,
    16 bits, for a maximum time of 60 seconds
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    record_filename = os.path.join(RECORDDIRECTORY, f"{timestamp}.wav")
    global record_process
    record_process = subprocess.Popen(
        [
            "arecord",
            "-f",
            "S16_LE",
            "-c1",
            "-r44100",
            "-d",
            f"{TIMEMAXREC}",
            record_filename,
        ]
    )


def play_audio(*audio):
    """
    Plays - and queue if necessary - audio files to be played

    Args:
        audio: tuple. AUDIOFILES keywords and/or full audiofile path as argument
    """
    if audio is None:
        return

    audiofiles = [
        AUDIOFILES[key] if key in AUDIOFILES else key
        for key in audio
        if key is not None
    ]

    audio_nb = len(audiofiles)

    match audio_nb:
        case 0:
            return
        case 1:
            audio_channel.play(mixer.Sound(audiofiles[0]))
        case 2:
            audio_channel.play(mixer.Sound(audiofiles[0]))
            audio_channel.queue(mixer.Sound(audiofiles[1]))
        case _:
            audio_channel.play(mixer.Sound(audiofiles[0]))
            audio_channel.queue(mixer.Sound(audiofiles[1]))
            for i in range(2, audio_nb):
                audio_queue.append(mixer.Sound(audiofiles[i]))


################################## MAIN LOOP ###################################

while True:
    while sleeping():
        sleep(0.1)

    play_audio("accueil", "menu")

    while working():
        key = keypad.pressed_keys
        audio_queue_handler()
        audio_process_handler(key)

        if 0 in key:
            play_audio("menu")
        elif 1 in key:
            play_audio("beep")
            start_recording()
        elif 2 in key:
            play_audio("prerandom", "beep", get_random_audio())
        elif 3 in key:
            play_audio("audio3")
        elif 4 in key:
            play_audio("audio31")
        elif 5 in key:
            play_audio("audio31")

        sleep(0.1)

    stop_all()
