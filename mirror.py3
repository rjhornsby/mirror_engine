#!/usr/bin/env python3
import os, sys, time
import pygame

GPIO_SIMULATED = True
if GPIO_SIMULATED:
    from EmulatorGUI import GPIO
    SENSOR_PUD = GPIO.PUD_DOWN
else:
    import RPi.GPIO as GPIO
    SENSOR_PUD = GPIO.PUD_UP

import mirror_display

# Map relay index to GPIO BCM pin id
RELAYS = {
    1: 5,
    2: 6,
    3: 13,
    4: 19
}

SENSOR_GPIO_PIN = 21

class Sound:
    def __init__(self):
        os.system('amixer sset "PCM" 100%')
        pygame.mixer.init()
        self.library = {}
        self.now_playing = None
        self.base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

        self.audio_path = os.path.join(self.base_path, 'audio')
        pygame.mixer.music.load(os.path.join(self.audio_path, 'beauty_theme_1s_delay.mp3'))

    def play(self):
        pygame.mixer.music.load(os.path.join(self.audio_path, 'beauty_theme_1s_delay.mp3'))
        self.now_playing = pygame.mixer.music.play(-1)

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
        log("Initializing relays, please wait")

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SENSOR_GPIO_PIN, GPIO.IN, pull_up_down=SENSOR_PUD)

        for pin in relay_list:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)

        if not quiet:
            for pin in relay_list:  # cycle individual
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.25)
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0)

            for pin in relay_list:  # all on
                GPIO.output(pin, GPIO.LOW)
            time.sleep(1.0)

            for pin in relay_list:  # all off
                GPIO.output(pin, GPIO.HIGH)


class SensorPad:

    def __init__(self, relay_list):
        self.sound = Sound()
        self.mirror = mirror_display.MirrorText(fullscreen=False)
        self.relay_list = relay_list

    def stop(self):
        self.mirror.stop()
        self.sound.stop(100)
        # Let the thread finish
        if self.mirror.thr is not None:
            while self.mirror.thr.isAlive():
                log("waiting for thread to finish")
                pass

        GPIO.output(RELAYS[2], GPIO.HIGH)
        GPIO.output(RELAYS[3], GPIO.HIGH)

    def state_changed(self, state):
        log("pin status: " + str(state))
        if state == True:

            if not self.sound.is_busy():
                self.sound.play()
            else:
                log("Sound already playing")

            time.sleep(1.5)
            GPIO.output(RELAYS[1], GPIO.LOW)  # relay 1
            time.sleep(2)
            GPIO.output(RELAYS[2], GPIO.LOW)  # relay 2
            time.sleep(2)
            GPIO.output(RELAYS[3], GPIO.LOW)  # relay 3
            self.mirror.run()

        else:
            self.mirror.stop()
            time.sleep(1.5)
            GPIO.output(RELAYS[2], GPIO.HIGH)
            time.sleep(1.5)
            GPIO.output(RELAYS[3], GPIO.HIGH)

            self.sound.stop()

            GPIO.output(RELAYS[1], GPIO.HIGH)


def log(message):
    log_message = time.strftime('[%a %Y-%m-%d %H:%M:%S]: ' + message)
    print(log_message)
    log_fh = open(os.path.abspath(__file__) + '.log', 'a')
    log_fh.write(log_message + "\n")
    log_fh.close()


def main(argv):

    relay_list = list(RELAYS.values())
    MirrorIO.init_gpio(relay_list, quiet=False)
    last_input_state = GPIO.input(SENSOR_GPIO_PIN)
    pad = SensorPad(relay_list)

    done = False

    try:
        log("Ready, starting loop")
        while not done:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True

            if GPIO.input(SENSOR_GPIO_PIN) != last_input_state:
                time.sleep(0.25)  # wait to make sure it really changed
                if GPIO.input(SENSOR_GPIO_PIN) != last_input_state:
                    last_input_state = GPIO.input(SENSOR_GPIO_PIN)
                    pad.state_changed(GPIO.input(SENSOR_GPIO_PIN))
            time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        sys.exit
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main(sys.argv)
