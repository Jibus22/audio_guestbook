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
import signal

################################## BOARD INIT ##################################

PICKUP_BUTTON = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(PICKUP_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

cols = [digitalio.DigitalInOut(x) for x in (board.D16, board.D26, board.D6)]
rows = [digitalio.DigitalInOut(x) for x in (board.D5, board.D22, board.D27, board.D17)]
keys = ((1, 2, 3), (4, 5, 6), (7, 8, 9), ("*", 0, "#"))
flattened_keys = list(chain.from_iterable(keys))
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

menu = None

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
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
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


def record_limit_handler(signum, frame):
    if record_process is None:
        return

    global menu
    global record_process
    menu = main_menu
    record_process = None
    play_audio("endrecord")


def start_recording():
    """
    Launch the 'arecord' subprocess to record a 'timestampedfile.wav' at 44.1kHz,
    16 bits, for a maximum time of 60 seconds
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    record_filename = os.path.join(RECORDDIRECTORY, f"{timestamp}.wav")
    signal.signal(signal.SIGCHLD, record_limit_handler)
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
            clean_audio_queue()
            audio_channel.play(mixer.Sound(audiofiles[0]))
            audio_channel.queue(mixer.Sound(audiofiles[1]))
            for i in range(2, audio_nb):
                audio_queue.append(mixer.Sound(audiofiles[i]))


#################################### MENUS #####################################


def menu31(key):
    match key:
        case 1:
            play_audio("audio31a")
        case 2:
            play_audio("audio31b")


def menu32(key):
    match key:
        case 1:
            play_audio("audio32a")
        case 2:
            play_audio("audio32b")


def menu33(key):
    match key:
        case 1:
            play_audio("audio33a")
        case 2:
            play_audio("audio33b")


def secondary_menu(key):
    global menu
    match key:
        case 1:
            play_audio("audio31")
            menu = menu31
        case 2:
            play_audio("audio32")
            menu = menu32
        case 3:
            play_audio("audio33")
            menu = menu33


def empty_menu(key):
    pass


def main_menu(key):
    global menu
    match key:
        case 1:
            play_audio("beep")
            start_recording()
            menu = empty_menu
        case 2:
            play_audio("prerandom", "beep", get_random_audio())
        case 3:
            play_audio("audio3")
            menu = secondary_menu


################################## MAIN LOOP ###################################


def phone_off():
    while sleeping():
        sleep(0.1)


def phone_on():
    global menu
    menu = main_menu
    play_audio("accueil", "menu")

    while working():
        pressed_keys = keypad.pressed_keys
        audio_queue_handler()

        if len(pressed_keys) == 0:
            sleep(0.05)
            continue

        key = pressed_keys[0]
        match key:
            case 0:
                menu = main_menu
                stop_record()
                play_audio("menu")
            case _:
                menu(key[0])

        sleep(0.1)

    stop_all()


def main_loop():
    while True:
        phone_off()
        phone_on()


main_loop()