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
import signal

############################### CONSTANT VARIABLES #############################

PICKUP_BUTTON = 23
TIMEMAXREC = 60  # maximum recording time (sec)

BASEDIRECTORY = "/home/rasphone/share"
RECORDDIRECTORY = f"{BASEDIRECTORY}/record"
AUDIODIRECTORY = f"{BASEDIRECTORY}/audio_files"
AUDIOFILES = {
    "accueil": f"{AUDIODIRECTORY}/accueil.wav",
    "menu": f"{AUDIODIRECTORY}/menu.wav",
    "beep": f"{AUDIODIRECTORY}/beep.wav",
    "prerandom": f"{AUDIODIRECTORY}/prerandom.wav",
    "audio3": f"{AUDIODIRECTORY}/audio3.wav",
    "audio31": f"{AUDIODIRECTORY}/audio31.wav",
}
EXITCODE = "9889"  # state to be reached by 'exit_code' to trigger program exit
EXITCODE_VELOCITY = 1  # max duration between two keystrokes to type exit code (seconds)
# duration to sleep after any keystroke to mitigate rebound effect (seconds)
BOUNCETIME = 0.35
POLLING_PERIOD = 0.08  # duration to sleep between two loop cycle (seconds)

############################### MUTABLE VARIABLES ##############################

# homemade audio queue to extends the limited one from pygame.mixer.Channel
audio_queue = []
arecord_proc = None  # receives 'arecord' subprocess popen object to keep track of it
phone_menu = None  # dynamically takes reference to any menu to be executed in runtime
phone_exit_code = ""  # current state of phone exit code

############################### INITIALIZATION #################################

GPIO.setmode(GPIO.BCM)
GPIO.setup(PICKUP_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

cols = [digitalio.DigitalInOut(x) for x in (board.D16, board.D26, board.D6)]
rows = [digitalio.DigitalInOut(x) for x in (board.D5, board.D22, board.D27, board.D17)]
keys = [[1, 2, 3], [4, 5, 6], [7, 8, 9], ["*", 0, "#"]]
keypad = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keys)

mixer.init(frequency=44100, channels=1, buffer=4096)
audio_channel = mixer.Channel(0)

################################# FUNCTIONS ####################################


def working():
    return GPIO.input(PICKUP_BUTTON) == 0


def sleeping():
    return GPIO.input(PICKUP_BUTTON) != 0


def clean_audio_queue():
    global audio_queue
    audio_queue = []


def stop_audio():
    if audio_channel.get_busy():
        audio_channel.stop()


def stop_record():
    global arecord_proc
    if arecord_proc is not None and arecord_proc.poll() is None:
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        arecord_proc.terminate()

    arecord_proc = None


def stop_all():
    stop_audio()
    clean_audio_queue()
    stop_record()


def exit_code_velocity_handler(signum, frame):
    global phone_exit_code
    phone_exit_code = ""


def set_exit_code(key):
    global phone_exit_code
    mykey = str(key)

    if EXITCODE.find(mykey) == -1:
        signal.alarm(0)
        phone_exit_code = ""
        return

    signal.signal(signal.SIGALRM, exit_code_velocity_handler)
    signal.alarm(EXITCODE_VELOCITY)
    phone_exit_code += mykey
    print(f"exitcode: {phone_exit_code}")
    if phone_exit_code == EXITCODE:
        raise SystemExit


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
    """
    SIGCHLD handler, triggered when 60 sec of recording had elapsed, to reset
    record_process variable, send user back to main menu and audio announcing
    end of recording
    """
    global arecord_proc
    if arecord_proc is None:
        return

    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    global phone_menu
    phone_menu = main_menu
    arecord_proc = None
    play_audio("endrecord")


def start_recording():
    """
    Launch the 'arecord' subprocess to record a 'timestampedfile.wav' at 44.1kHz,
    16 bits, for a maximum time of 60 seconds
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    record_filename = os.path.join(RECORDDIRECTORY, f"{timestamp}.wav")
    signal.signal(signal.SIGCHLD, record_limit_handler)
    global arecord_proc
    arecord_proc = subprocess.Popen(
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
    global phone_menu
    match key:
        case 1:
            play_audio("audio31")
            phone_menu = menu31
        case 2:
            play_audio("audio32")
            phone_menu = menu32
        case 3:
            play_audio("audio33")
            phone_menu = menu33


def empty_menu(key):
    pass


def main_menu(key):
    global phone_menu
    match key:
        case 1:
            play_audio("beep")
            start_recording()
            phone_menu = empty_menu
        case 2:
            play_audio("prerandom", "beep", get_random_audio())
        case 3:
            play_audio("audio3")
            phone_menu = secondary_menu


############################## MAIN LOOP FUNCTIONS #############################


def keypad_polling():
    global phone_menu
    phone_menu = main_menu

    while working():
        pressed_keys = keypad.pressed_keys
        audio_queue_handler()

        if len(pressed_keys) == 0:
            sleep(POLLING_PERIOD)
            continue

        key = pressed_keys[0]
        set_exit_code(key)
        match key:
            case 0:
                phone_menu = main_menu
                stop_record()
                play_audio("menu")
            case _:
                phone_menu(key)

        sleep(POLLING_PERIOD + BOUNCETIME)


def phone_off():
    if sleeping() is False:
        return
    GPIO.wait_for_edge(PICKUP_BUTTON, GPIO.FALLING)
    sleep(BOUNCETIME)


def phone_on():
    if working() is False:
        return

    play_audio("accueil", "menu")
    keypad_polling()

    stop_all()
    sleep(BOUNCETIME)


def main_loop():
    while True:
        phone_off()
        phone_on()


################################## MAIN LOOP ###################################

try:
    main_loop()
except KeyboardInterrupt:
    print("interrupted by user")
finally:
    if arecord_proc is not None and arecord_proc.poll() is None:
        arecord_proc.terminate()
    mixer.quit()
    GPIO.cleanup()
    print("rasphone exiting")
