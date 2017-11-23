#!/usr/bin/env python3

import os, sys, time
import pygame
import threading
import json
from logger import Logger
from pygame.locals import *
from random import *

# Set up some constants
FADE_IN_TIME = 3
FADE_OUT_TIME = 2

class MirrorText:
    def __init__(self, fullscreen=True):
        Logger.write.info("MirrorText: init()")
        self.fontlib = []
        self.fontsize = 72
        self.screen = None
        self.phrases = None
        self.thr = None
        self.stopping = False
        self.base_path = os.path.dirname(os.path.abspath(__file__))

        fontdir = os.path.join(self.base_path, "data", "fonts")
        pygame.init()

        pygame.mouse.set_visible(False)
        font_exts = ['.otf', '.ttf']

        if fullscreen:
            pygame_screen_mode = pygame.FULLSCREEN | pygame.NOFRAME
            pygame_screen_res = (0, 0)
        else:
            pygame_screen_mode = 0
            pygame_screen_res = (600, 400)
            self.fontsize = 56
        for file in os.listdir(fontdir):
            filename, extension = os.path.splitext(file)
            if extension in font_exts:
                self.fontlib.append(pygame.font.Font(os.path.join(fontdir, file), self.fontsize))

        Logger.write.info("loaded " + str(len(self.fontlib)) + " fonts")

        self.screen = pygame.display.set_mode(pygame_screen_res, pygame_screen_mode)
        self.screen.fill(FadingText.COLORS['black'])
        pygame.display.flip()

        Logger.write.info("MirrorText ready!")

    def run(self):
        if self.thr is not None:
            if self.thr.isAlive():
                return
        self.stopping = False

        with open(os.path.join(self.base_path, 'cache/phrases.json')) as phrase_file:
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
                fading_text.stop()
                fading_text.fade(FadingText.ST_FADEOUT, 1)
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


class FadeThread(threading.Thread):

    def __init__(self, thread_id, name, fading_text, fade_interval):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.fading_text = fading_text
        self.fade_interval = fade_interval

    def run(self):
        if self.name == 'fade_in':
            self.fading_text.fade_in(self.fade_interval)
        elif self.name == 'fade_out':
            self.fading_text.fade_out(self.fade_interval)
        

class FadingText:
    
    ST_FADEIN = 0
    ST_FADEOUT = 1
    LINE_SPACING = -2
    MARGIN = 0.10
    FADE_IN_EASING = lambda x: x  # Linear
    FADE_OUT_EASING = lambda x: x  # Linear

    COLORS = {
        "white": pygame.Color(255, 255, 255),
        "black": pygame.Color(0, 0, 0),
        "gray": pygame.Color(127, 127, 127)
    }

    def __init__(self, screen, fontlib, text, center_text=False):
        self.thr = None
        self.stopping = False
        self.screen = screen
        self.text = text
        self.center_text = center_text
        self.state = None
        self.alpha = 0.0
        self.position = (0, 0)  # Overwritten in predraw()
        self.state_time = time.time()
        self.last_state_change = time.time()
        self.font = choice(fontlib)
        self.rendered_text = []
        self.drawing_surface = None
        self.predraw()

    def fade(self, direction, fade_interval):
        if self.thr is not None:
            if self.thr.isAlive():
                return
            
        if direction == FadingText.ST_FADEIN:
            self.thr = FadeThread(0, 'fade_in', self, fade_interval)
            self.thr.start()
            self.thr.join()
        elif direction == FadingText.ST_FADEOUT:
            self.thr = FadeThread(0, 'fade_out', self, fade_interval)
            self.thr.start()
            self.thr.join()
        else:
            return

    def stop(self):
        self.stopping = True
    
    def fade_in(self, fade_interval):
        if self.alpha >= 1.0:
            return

        self.stopping = False

        last_state_change = time.time()
        adv_offset = 0

        if self.alpha < 1.0:
            adv_offset = self.alpha * fade_interval

        while self.alpha < 1.0:
            if self.stopping:
                return

            state_time = time.time() + adv_offset - last_state_change
            self.alpha = FadingText.FADE_IN_EASING(1.0 * state_time / fade_interval)

            self.draw()
            
        self.state = FadingText.ST_FADEIN
        self.alpha = 1.0
    
    def fade_out(self, fade_interval):
        if self.alpha <= 0.0:
            return

        self.stopping = False

        last_state_change = time.time()
        adv_offset = 0
        # If we're not completely transparent, artifically pretend that
        # we're farther along in the fade than we are, which gives the
        # effect of resuming fade
        if self.alpha > 0.0:
            adv_offset = fade_interval - self.alpha * fade_interval
            
        while self.alpha > 0.0:
            if self.stopping:
                return

            state_time = time.time() + adv_offset - last_state_change
            self.alpha = 1. - FadingText.FADE_OUT_EASING(1.0 * state_time / fade_interval)

            self.draw()
        
        self.state = FadingText.ST_FADEOUT
        self.alpha = 0.0

    # Use predraw in the constructor
    # so that we only have to do this work one time
    def predraw(self):
        # see http://pygame.org/wiki/TextWrap
        lines = self.text.splitlines()
        y = 0
        screen_w, screen_h = pygame.display.Info().current_w, pygame.display.Info().current_h

        screen_w = int(screen_w * (1 - FadingText.MARGIN))
        screen_h = int(screen_h * (1 - FadingText.MARGIN))

        font_height = self.font.size('Tg')[1]
        line_spacing = font_height + FadingText.LINE_SPACING
        longest_line_length = 0

        while lines:
            if y + font_height > screen_h:
                break

            line = lines.pop(0)

            # render a blank line
            if len(line) == 0:
                rendered_line = self.font.render("", True, FadingText.COLORS['white'])
                self.rendered_text.append(rendered_line)
                y += line_spacing

            while line:
                i = 1

                while self.font.size(line[:i])[0] < screen_w and i < len(line):
                    i += 1

                if i < len(line):
                    i = line.rfind(" ", 0, i) + 1

                rendered_line = self.font.render(line[:i], True, FadingText.COLORS['white'])

                if rendered_line.get_rect().width > longest_line_length:
                    longest_line_length = rendered_line.get_rect().width

                self.rendered_text.append(rendered_line)
                y += line_spacing
                line = line[i:]
            if self.center_text:
                self.position = self.centered(longest_line_length, y)
            else:
                self.position = self.random_position(longest_line_length, y)

    def draw(self):

        x, y = self.position
        font_height = self.font.size('Tg')[1]

        # clear the screen
        screen_w, screen_h = pygame.display.Info().current_w, pygame.display.Info().current_h
        s2 = pygame.surface.Surface((screen_w, screen_h))
        self.drawing_surface = s2
        s2.set_alpha(255 * self.alpha)
        self.screen.fill(FadingText.COLORS['black'])

        for rendered_line in self.rendered_text:
            s2.blit(rendered_line, (x, y))
            y += font_height + FadingText.LINE_SPACING

        self.screen.blit(s2, (0, 0))  # always draw onto 0,0 of the screen surface
        pygame.display.flip()

    @staticmethod
    def centered(r_width, r_height):

        screen_w, screen_h = pygame.display.Info().current_w, pygame.display.Info().current_h
        x = screen_w / 2 - r_width / 2
        y = screen_h / 2 - r_height / 2

        return x, y

    @staticmethod
    def random_position(r_width, r_height):
        screen_w, screen_h = pygame.display.Info().current_w, pygame.display.Info().current_h
        x_margin = int(0.05 * screen_w)
        y_margin = int(0.05 * screen_h)

        min_x = x_margin
        min_y = y_margin
        max_x = screen_w - x_margin
        max_y = screen_h - y_margin

        try:
            x = randint(min_x, max_x - r_width)
        except ValueError:
            x = min_x
        try:
            y = randint(min_y, max_y - r_height)
        except ValueError:
            y = min_y
        
        return x, y


def main():

    mirror = MirrorText(fullscreen=False)
    mirror.run()
    # done = False
    #
    # phrase_index = 0
    # fading_text = FadingText(mirror.screen, mirror.fontlib, mirror.phrases[phrase_index]['text'])
    #
    # while not done:
    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             done = True
    #         if event.type == pygame.KEYDOWN:
    #             if event.key == pygame.K_ESCAPE:
    #                 fading_text.stop
    #                 done = True
    #             elif event.key == pygame.K_UP:
    #                 fading_text.fade(fading_text.ST_FADEIN, 3)
    #             elif event.key == pygame.K_DOWN:
    #                 fading_text.fade(fading_text.ST_FADEOUT, 1)
    #             elif event.key == pygame.K_b:
    #                 print("Fast fade out")
    #                 fading_text.fade(fading_text.ST_FADEOUT, 1)
    #             elif event.key == pygame.K_SPACE:
    #                 phrase_index += 1
    #                 if phrase_index >= len(mirror.phrases):
    #                     phrase_index = 0
    #                 fading_text.stop
    #                 fading_text = FadingText(mirror.screen, mirror.fontlib, mirror.phrases[phrase_index]['text'])  # create a new one
    #                 fading_text.fade(fading_text.ST_FADEIN, 3)
    #             else:
    #                 fading_text.stop()


if __name__ == "__main__":
    main()
