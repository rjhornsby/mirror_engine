#!/usr/bin/env python3
import os
import sys
import time
from random import *
import mutagen
import pygame
from mutagen import mp3
from lib.display import MirrorDisplay
from lib.dme import DME
from logger import Logger


global GPIO_SIMULATED
GPIO_SIMULATED = False

if 'GPIO_SIMULATED' in os.environ:
    GPIO_SIMULATED = True
    from EmulatorGUI import GPIO
    SENSOR_PUD = GPIO.PUD_DOWN
else:
    import RPi.GPIO as GPIO
    SENSOR_PUD = GPIO.PUD_UP

# Map relay index to GPIO BCM pin id
RELAYS = {
    1: 5,
}

RELAY_ON = GPIO.HIGH
RELAY_OFF = GPIO.LOW

SENSOR_GPIO_PIN = 21
DEBOUNCE_TIME = 0.25

DISTANCE_THRESHOLD = 1000  # mm
DISTANCE_SAMPLES = 15

class Sound:
    def __init__(self):
        os.system('amixer sset "PCM" 100%')
        pygame.mixer.init()
        self.library = {}
        self.now_playing = None
        self.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        self.audio_dir = os.path.join(self.base_path, 'cache/audio')

    def _load_library(self):
        self.library = {}
        for file in os.listdir(self.audio_dir):
            filename = os.path.join(self.audio_dir, file)
            if self._verify_format(filename):
                self.library[filename] = self.audio_format(filename)

        Logger.write.info('Loaded ' + str(len(self.library)) + ' music files')

    def play(self):
        # reload the library each time in case the list has changed
        self._load_library()

        # If we have no music to play, don't play any music.
        if len(self.library.items()) == 0:
            return

        # If we're muted, don't play music
        if os.path.isfile(os.path.join(self.audio_dir, 'mute_audio.lock')):
            return

        filename, metadata = choice(list(self.library.items()))
        self._init_mixer(metadata)
        pygame.mixer.music.load(filename)
        self.now_playing = pygame.mixer.music.play(-1)

    # The mixer does not understand on its own how to play files at 48000Hz, etc.
    @staticmethod
    def _init_mixer(metadata):
        pygame.mixer.quit()
        frequency = int(metadata.sample_rate / metadata.channels)
        pygame.mixer.pre_init(frequency=frequency, channels=metadata.channels)
        pygame.mixer.init()

    @staticmethod
    def _verify_format(file):
        valid_format = True
        audio = mutagen.File(file)
        if type(audio) is not mutagen.mp3.MP3:
            Logger.write.warn("Invalid audio type '" + str(type(audio)) + "' for " + file)
            valid_format = False

        return valid_format

    @staticmethod
    def audio_format(file):
        audio = mutagen.File(file)
        return audio.info

    @staticmethod
    def stop(fade_delay=3000):
        pygame.mixer.music.fadeout(fade_delay)
        time.sleep(fade_delay / 1000)
        pygame.mixer.music.stop()

    @staticmethod
    def is_busy():
        return pygame.mixer.music.get_busy()


class MirrorIO:

    @staticmethod
    def init_gpio(relay_list, quiet=True):
        Logger.write.info("Initializing relays, please wait")

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SENSOR_GPIO_PIN, GPIO.IN, pull_up_down=SENSOR_PUD)

        for pin in relay_list:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, RELAY_OFF)

        if not quiet:
            for pin in relay_list:  # cycle individual
                GPIO.output(pin, RELAY_ON)
                time.sleep(0.25)
                GPIO.output(pin, RELAY_OFF)
                time.sleep(0)

            for pin in relay_list:  # all on
                GPIO.output(pin, RELAY_ON)
            time.sleep(1.0)

            for pin in relay_list:  # all off
                GPIO.output(pin, RELAY_OFF)


class ActivationSensor:

    def __init__(self, relay_list):
        self.switch_override_state = False
        self.sound = Sound()
        basepath = os.path.dirname(os.path.abspath(__file__))
        self.mirror = MirrorDisplay(basepath, fullscreen=(not GPIO_SIMULATED))
        # self.mirror = mirror_display.MirrorText(fullscreen=(not GPIO_SIMULATED))
        self.relay_list = relay_list
        self.dme = DME(DISTANCE_THRESHOLD, DISTANCE_SAMPLES)
        self.dme.run()

    def stop(self):
        self.mirror.stop()
        self.sound.stop(100)
        # Let the thread finish
        if self.mirror.thr is not None:
            while self.mirror.thr.isAlive():
                Logger.write.info("waiting for thread to finish")
                pass

        GPIO.output(RELAYS[1], RELAY_OFF)

    def input_override(self, state):
        Logger.write.debug("Overriding input: " + str(state))

        if state:
            self.switch_override_state = True
        else:
            self.switch_override_state = False

    def read_input_state(self):
        return self.dme.in_range() or self.switch_override_state

    def state_changed(self, state):
        Logger.write.info("pin status: " + str(state))
        if state == True:

            if not self.sound.is_busy():
                self.sound.play()
            else:
                Logger.write.info("Sound already playing")

            time.sleep(1.5)
            GPIO.output(RELAYS[1], RELAY_ON)  # relay 1
            time.sleep(2)
            self.mirror.run()

        else:
            self.mirror.stop()
            time.sleep(1.5)
            self.sound.stop()

            GPIO.output(RELAYS[1], RELAY_OFF)


def main(argv):
    # TODO: Make mirror display diagnostic info on startup (especially warnings)
    # TODO: Make mirror clear warnings and start loop on first sensor activation (or after X seconds?)

    log = Logger()  # this has to be called at least once
    Logger.write.info('Starting up')
    try:
        Logger.write.debug('Initializing pygame')
        pygame.init()
    except (KeyboardInterrupt, SystemExit) as err:
        Logger.write.error('FATAL:' + err)
        raise

    relay_list = list(RELAYS.values())
    MirrorIO.init_gpio(relay_list, quiet=False)

    sensor = ActivationSensor(relay_list)
    last_input_state = sensor.read_input_state

    done = False

    try:
        log.write.info('Ready, starting loop')
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        new_state = not sensor.switch_override_state
                        log.write.info("Setting state " + str(new_state))
                        sensor.input_override(new_state)
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        done = True

            input_state = sensor.read_input_state()
            if input_state != last_input_state:
                time.sleep(DEBOUNCE_TIME)  # wait to make sure it really changed
                if input_state != last_input_state:
                    last_input_state = input_state
                    sensor.state_changed(input_state)
            time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        # TODO: fix GPIO emulator threading bug that prevents clean shutdown
        GPIO.cleanup()
        sys.exit
    finally:
        sensor.dme.stop()
        GPIO.cleanup()
        sys.exit


if __name__ == "__main__":
    main(sys.argv)
