#!/usr/bin/env python3

import os, sys, time
import pygame
from pygame.locals import *
import threading

# Set up some constants
colors = {
    "white"     : pygame.Color(255, 255, 255),
    "black"     : pygame.Color(0, 0, 0),
    "gray"      : pygame.Color(127, 127, 127)
}
FADE_IN_TIME = 5
FADE_OUT_TIME = 5
FADE_IN_EASING = lambda x: x # Linear
FADE_OUT_EASING = lambda x: x # Linear

fontdir = os.path.dirname(os.path.abspath( __file__))

pygame.init()
pygame.mouse.set_visible(False)

font = pygame.font.Font(os.path.join(fontdir, "data/fonts", "FloodStd.otf"), 64)
screen = pygame.display.set_mode((1024, 768))
screen.fill(colors['black'])
pygame.display.flip()

clock = pygame.time.Clock()
done = False

class myThread(threading.Thread):
    def __init__(self, threadID, name, fading_text):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.fading_text = fading_text
    def run(self):
        if self.name == 'fade_in':
            self.fading_text.fade_in()
        elif self.name == 'fade_out':
            self.fading_text.fade_out()
        

class FadingText:
    
    ST_FADEIN = 0
    ST_FADEOUT = 1
    
    def __init__(self, screen, text):
        self.thr = None
        self.stopping = False
        self.screen = screen
        self.text = text
        self.state = None
        self.alpha = 0.0
        self.state_time = time.time()
        self.last_state_change = time.time()
        self.t1 = font.render(text, True, colors['white'])
        width, height = pygame.display.Info().current_w, pygame.display.Info().current_h
        self.t1_rect = self.t1.get_rect(center=(width / 2, height / 2))
        rt = self.t1
        self.draw(rt)
        
    def fade(self, new_state):
        if self.thr is not None:
            if self.thr.isAlive():
                return
            
        if new_state == FadingText.ST_FADEIN:
            self.thr = myThread(0, 'fade_in', self)
            self.thr.start()
            # don't join the thread so that new events aren't queued
        elif new_state == FadingText.ST_FADEOUT:
            self.thr = myThread(0, 'fade_out', self)
            self.thr.start()
        else:
            return
        
    def stop(self):
        self.stopping = True
    
    def fade_in(self):
        if self.state == FadingText.ST_FADEIN:
            return

        self.stopping = False

        last_state_change = time.time()

        while self.alpha < 1.0:
            if self.stopping:
                return

            state_time = time.time() - last_state_change
            self.alpha = FADE_IN_EASING(1.0 * state_time / FADE_IN_TIME)
            
            rt = self.t1
            self.draw(rt)
            clock.tick(50)
            
        self.state = FadingText.ST_FADEIN
    
    def fade_out(self):
        if self.state == FadingText.ST_FADEOUT:
            return

        self.stopping = False

        last_state_change = time.time()

        while self.alpha > 0.0:
            if self.stopping:
                return

            state_time = time.time() - last_state_change
            self.alpha = 1. - FADE_OUT_EASING(1.0 * state_time / FADE_OUT_TIME)
            
            rt = self.t1
            self.draw(rt)
        
        self.state = FadingText.ST_FADEOUT

    def draw(self, rt):
        print("alpha: {}".format(self.alpha))
        s2 = pygame.surface.Surface((self.t1_rect.width, self.t1_rect.height))
        s2.set_alpha(255 * self.alpha)
        self.screen.fill(colors['black'])
        
        s2.blit(rt, (0,0))
        self.screen.blit(s2, self.t1_rect)
        pygame.display.flip()

def center(width, height):
    disp_info = pygame.display.Info()
    center_w = disp_info.current_w // 2 - width // 2
    center_h = disp_info.current_h // 2 - height // 2
    return (center_w, center_h)

fading_text = FadingText(screen, "hello, world!")
# fading_text.fade_in()

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                done = True
            elif event.key == pygame.K_UP:
                fading_text.fade(fading_text.ST_FADEIN)
            elif event.key == pygame.K_DOWN:
                fading_text.fade(fading_text.ST_FADEOUT)
            else:
                fading_text.stop()
                screen.fill(colors['black'])
                pygame.display.flip()
                
