#!/usr/bin/env python3

import os
import pygame
from lib.color import Color
from logger import Logger
from lib.mirror_text import MirrorText


class MirrorDisplay(object):
    def __init__(self, basepath, fullscreen=True):
        self.basepath = basepath

        pygame.init()
        pygame.mouse.set_visible(False)

        if fullscreen:
            pygame_screen_mode = pygame.FULLSCREEN | pygame.NOFRAME
            pygame_screen_res = (0, 0)
        else:
            pygame_screen_mode = 0
            pygame_screen_res = (600, 400)

        self._screen = pygame.display.set_mode(pygame_screen_res, pygame_screen_mode)

        self._screen.fill(Color.black.value)
        pygame.display.flip()

        # mirror_text = MirrorText(self._screen)
        Logger.write.info("MirrorDisplay ready!")

        self.mirror_text = MirrorText(self.basepath, self._screen)

    def run(self):
        self.mirror_text.run()

    def stop(self):
        self.mirror_text.stop()


