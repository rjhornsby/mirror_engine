import json
import os
import threading
import time
from random import *
import pygame
from lib.fading_text import FadingText
from logger import Logger

# Set up some constants
FADE_IN_TIME = 3
FADE_OUT_TIME = 2


class MirrorText:
    def __init__(self, basepath, screen):
        Logger.write.info("MirrorText: init()")
        self.basepath = basepath
        self.screen = screen
        self.fontlib = []
        self.fontsize = 72
        self.phrases = None
        self.thr = None
        self.stopping = False

        self.load_fonts(
            os.path.join(self.basepath, "data", "fonts"), ['.otf', '.ttf'])

        Logger.write.info("MirrorText ready!")

    def load_fonts(self, fontdir, font_exts):
        for file in os.listdir(fontdir):
            filename, extension = os.path.splitext(file)
            if extension in font_exts:
                self.fontlib.append(pygame.font.Font(os.path.join(fontdir, file), self.fontsize))

        Logger.write.info("loaded " + str(len(self.fontlib)) + " fonts")

    def run(self):
        if self.thr is not None:
            if self.thr.isAlive():
                return
        self.stopping = False

        with open(os.path.join(self.basepath, 'cache/phrases.json')) as phrase_file:
            self.phrases = json.load(phrase_file)['phrases']
        Logger.write.info("Loaded " + str(len(self.phrases)) + " phrases")

        # Randomize the sequence - but don't choose a random phrase from the list each time
        # otherwise, you risk duplicate consecutive phrases
        shuffle(self.phrases)

        self.thr = MirrorThread(0, 'loop', self)
        self.thr.start()

    def loop(self):
        phrase_index = 0
        last_change = 0
        phrase = self.phrases[phrase_index]
        fading_text = FadingText(self.screen, self.fontlib, phrase['text'])
        while True:

            if self.stopping:
                Logger.write.debug('MirrorText stopping')
                fading_text.stop()
                fading_text.fade(FadingText.ST_FADEOUT, 1)
                Logger.write.debug('MirrorText stopped')
                return

            if time.time() > phrase['duration'] + last_change:
                fading_text.fade(FadingText.ST_FADEOUT, FADE_OUT_TIME)
                # Next
                phrase_index += 1
                if phrase_index >= len(self.phrases):
                    phrase_index = 0

                phrase = self.phrases[phrase_index]
                fading_text = FadingText(self.screen, self.fontlib, phrase['text'])
                last_change = time.time()
                fading_text.fade(FadingText.ST_FADEIN, FADE_IN_TIME)

    def stop(self):
        self.stopping = True


class MirrorThread(threading.Thread):
    def __init__(self, thread_id, name, mirror):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.mirror = mirror

    def run(self):
        self.mirror.loop()