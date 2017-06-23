#!/usr/bin/env python3

import os, sys, time
import pygame
import threading
import json
from pygame.locals import *
from random import *

# Set up some constants
FADE_IN_TIME = 3
FADE_OUT_TIME = 2
FADE_IN_EASING = lambda x: x # Linear
FADE_OUT_EASING = lambda x: x # Linear

class myThread(threading.Thread):

    def __init__(self, threadID, name, fading_text, fade_interval):
        threading.Thread.__init__(self)
        self.threadID = threadID
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
    MARGIN = 0.05

    COLORS = {
        "white": pygame.Color(255, 255, 255),
        "black": pygame.Color(0, 0, 0),
        "gray": pygame.Color(127, 127, 127)
    }

    def __init__(self, screen, fontlib, text):
        self.thr = None
        self.stopping = False
        self.screen = screen
        self.text = text
        self.state = None
        self.alpha = 0.0
        self.position = (0, 0)  # Overwritten in predraw()
        self.state_time = time.time()
        self.last_state_change = time.time()
        self.font = choice(fontlib)
        self.rendered_text = []
        self.predraw()

    def fade(self, direction, fade_interval):
        if self.thr is not None:
            if self.thr.isAlive():
                return
            
        if direction == FadingText.ST_FADEIN:
            self.thr = myThread(0, 'fade_in', self, fade_interval)
            self.thr.start()
            # don't join the thread so that new events aren't queued
        elif direction == FadingText.ST_FADEOUT:
            self.thr = myThread(0, 'fade_out', self, fade_interval)
            self.thr.start()
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
            self.alpha = FADE_IN_EASING(1.0 * state_time / fade_interval)

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
            self.alpha = 1. - FADE_OUT_EASING(1.0 * state_time / fade_interval)

            self.draw()
        
        self.state = FadingText.ST_FADEOUT
        self.alpha = 0.0

    # Use predraw in the constructor
    # so that we only have to do this work one time
    def predraw(self):
        # see http://pygame.org/wiki/TextWrap
        text = self.text
        y = 0

        screen_w, screen_h = pygame.display.Info().current_w, pygame.display.Info().current_h

        screen_w = int(screen_w * (1 - FadingText.MARGIN))
        screen_h = int(screen_h * (1 - FadingText.MARGIN))

        font_height = self.font.size('Tg')[1]
        longest_line_length = 0

        while text:
            i = 1
            if y + font_height > screen_h:
                break

            while self.font.size(text[:i])[0] < screen_w and i < len(text):
                i += 1

            if i < len(text):
                i = text.rfind(" ", 0, i) + 1

            rendered_line = self.font.render(text[:i], True, FadingText.COLORS['white'])

            if rendered_line.get_rect().width > longest_line_length:
                longest_line_length = rendered_line.get_rect().width

            self.rendered_text.append(rendered_line)
            y += font_height + FadingText.LINE_SPACING
            text = text[i:]

        self.position = self.random_position(longest_line_length, y)

        print("random position: {}".format(self.position))

        return text

    def draw(self):

        x, y = self.position
        font_height = self.font.size('Tg')[1]

        # clear the screen
        screen_w, screen_h = pygame.display.Info().current_w, pygame.display.Info().current_h
        s2 = pygame.surface.Surface((screen_w, screen_h))
        s2.set_alpha(255 * self.alpha)
        self.screen.fill(FadingText.COLORS['black'])

        for rendered_line in self.rendered_text:
            s2.blit(rendered_line, (x, y))
            y += font_height + FadingText.LINE_SPACING

        self.screen.blit(s2, (0, 0))  # always draw onto 0,0 of the screen surface
        pygame.display.flip()

    def random_position(self, r_width, r_height):
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
    fontdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fonts")

    pygame.init()
    pygame.mouse.set_visible(False)
    font_exts = ['.otf', '.ttf']
    fontlib = []
    for file in os.listdir(fontdir):
        filename, extension = os.path.splitext(file)
        if extension in font_exts:
            fontlib.append(pygame.font.Font(os.path.join(fontdir, file), 72))

    screen = pygame.display.set_mode((1024, 768))
    screen.fill(FadingText.COLORS['black'])
    pygame.display.flip()

    clock = pygame.time.Clock()
    done = False

    with open('phrases.json') as phrase_file:
        phrases = json.load(phrase_file)

    # Randomize the sequence - but don't choose a random phrase from the list each time
    # otherwise, you risk duplicate consecutive phrases
    shuffle(phrases)

    phrase_index = 0
    fading_text = FadingText(screen, fontlib, phrases[phrase_index]['text'])

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    fading_text.stop
                    done = True
                elif event.key == pygame.K_UP:
                    fading_text.fade(fading_text.ST_FADEIN, 3)
                elif event.key == pygame.K_DOWN:
                    fading_text.fade(fading_text.ST_FADEOUT, 1)
                elif event.key == pygame.K_b:
                    print("Fast fade out")
                    fading_text.fade(fading_text.ST_FADEOUT, 1)
                elif event.key == pygame.K_SPACE:
                    phrase_index += 1
                    if phrase_index >= len(phrases):
                        phrase_index = 0
                    fading_text.stop()
                    fading_text = FadingText(screen, fontlib, phrases[phrase_index]['text']) # create a new one
                    fading_text.fade(fading_text.ST_FADEIN, 3)
                else:
                    fading_text.stop()

if __name__ == "__main__":
    main()