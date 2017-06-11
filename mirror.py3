#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import sys
import os
import random
import pygame.mixer
from threading import Thread

class Sound():
    def __init__(self):
        valid_extensions = ['.wav']
        self.library = {}
        self.channel = pygame.mixer.Channel(0)
        for file in os.listdir('audio'):
            print('Loading audio file %s' % (file))
            filename, extension = os.path.splitext(file)
            if extension in valid_extensions:
                self.library[file] = pygame.mixer.Sound(file)
        print('Loaded %s sounds' % (len(self.library)))
    def play(self):
        name, sound = random.choice(list(self.library.items()))
        print('playing %s' % (name))
        self.channel.play(sound)
    
    def stop(self):
        if self.is_busy():
            self.channel.fadeout(1000) 
        
    def is_busy(self):
        return self.channel.get_busy()
        
# class Audio(Thread):
#     def __init__(self):
#         ''' Constructor '''
#         Thread.__init__(self)
#     def run(self):
#         track = 'audio/' + random.choice(os.listdir('audio'))
#         print "[%s] Playing track: %s" % (self.getName(), track)
#         os.system('omxplayer ' + track)
#     def terminate(self):
#         self._running = False
    
def init_relays(relay_list, quiet=True):
    print("Initializing relays, please wait")
    for pin in relay_list:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        
    if quiet == False:
        for pin in relay_list: # cycle individual
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.25)
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0)

        for pin in relay_list: # all on
            GPIO.output(pin, GPIO.LOW)
        time.sleep(1.0)

        for pin in relay_list: # all off
            GPIO.output(pin, GPIO.HIGH)

def init_audio(use_hdmi=False):
    # pygame.mixer.init(44100,-16,2,2048)
    pygame.mixer.init()
    # pygame.mixer.music.load('sunrise.mp3')
    # pygame.mixer.music.play()
    # audio1 = pygame.mixer.Sound('sunrise.wav')
    # channel1 = pygame.mixer.Channel(1)
    # channel1.play(audio1)
    
    if use_hdmi:
        print('Audio: using HDMI')
        os.system('amixer cset numid=3 2')
        # This makes no sense. From the command line,
        # there's no 'PCM' control, only 'Master'.
        # But from within python, the same call there's only
        # 'PCM', not 'Master'.
        # os.system('amixer sset "Master" 100%')
        os.system('amixer sset "PCM" 100%')
    else:
        print('Audio: using 3.5mm')
        os.system('amixer cset numid=3 1')
        os.system('amixer sset "PCM" 100%')
    
class SwitchPad:

    def __init__(self, relay_list):
        self.sounds = Sound()
        self.relay_list = relay_list
        
    def state_changed(self, state):
        print(time.strftime('%H:%M:%S: ' + str(state)))
        if state == True:
            if not self.sounds.is_busy():
                self.sounds.play()
            else:
                print("Sound already playing")
                # self.sounds.stop()
            random_list = self.relay_list
            random.shuffle(random_list)
            for pin in self.relay_list:
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.50)
        else:
            for pin in self.relay_list:
                GPIO.output(pin, GPIO.HIGH)
            self.sounds.stop()
        
def main(argv):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # relay_list = [5, 6, 13, 19]
    relay_list = [5]
    init_audio(True)
    init_relays(relay_list, True)
    last_input_state = GPIO.input(21)
    
    pad = SwitchPad(relay_list)
    
    try:
        print("Ready, starting loop")
        while True:
            input_state=GPIO.input(21)
            if GPIO.input(21) != last_input_state:
                time.sleep(0.25) # wait to make sure it really changed
                if GPIO.input(21) != last_input_state:
                    last_input_state = GPIO.input(21)
                    pad.state_changed(GPIO.input(21))
            time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        sys.exit
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main(sys.argv)

# GPIO.cleanup()
