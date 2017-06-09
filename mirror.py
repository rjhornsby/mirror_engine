#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import sys
import os
import random
from threading import Thread

class Audio(Thread):
    def __init__(self):
        ''' Constructor '''
        Thread.__init__(self)
    def run(self):
        track = 'audio/' + random.choice(os.listdir('audio'))
        print "[%s] Playing track: %s" % (self.getName(), track)
        os.system('omxplayer ' + track)
    def terminate(self):
        self._running = False
    
def init_relays(relay_list, quiet=True):
    print "Initializing relays, please wait"
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

def init_audio():
    os.system('amixer cset numid=3 2')
    os.system('amixer sset "PCM" 100%')

class SwitchPad:

    def __init__(self, relay_list):
        self.music = Audio()
        self.relay_list = relay_list
        
    def state_changed(self, state):
        print time.strftime('%H:%M:%S: ' + str(state))
        if state == True:
            if not self.music.is_alive():
                self.music = Audio()
                self.music.start()
            else:
                print "Music already playing"
                self.music.terminate()
            random_list = self.relay_list
            random.shuffle(random_list)
            for pin in self.relay_list:
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.50)
        else:
            for pin in self.relay_list:
                GPIO.output(pin, GPIO.HIGH)
        
def main(argv):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    relay_list = [5, 6, 13, 19]

    init_audio()
    init_relays(relay_list, False)
    last_input_state = GPIO.input(21)
    
    pad = SwitchPad(relay_list)
    
    try:
        print "Ready, starting loop"
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
