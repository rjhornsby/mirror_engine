#!/usr/bin/env python3

import os, sys, time
import pygame
import pygame_textinput


class Prompt:
    COLORS = {
        "white": pygame.Color(255, 255, 255),
        "black": pygame.Color(0, 0, 0),
        "gray": pygame.Color(127, 127, 127)
    }

    def __init__(self):
        fontdir = os.path.join(self.base_path, "data", "fonts")

        pygame.init()
        pygame_screen_res = (1280, 720)

        self.fontsize = 24
        self.font = pygame.font.Font(os.path.join(fontdir, 'Gotham-Medium.otf'), self.fontsize)

        self.screen = pygame.display.set_mode(pygame_screen_res, 0)
        self.screen.fill(Prompt.COLORS['black'])
        pygame.display.flip()

        self.textinput = pygame_textinput.TextInput()

    @staticmethod
    def get_wifi_networks():
        return [
            'ATT4QLN2h4'
            'Adara Pool 2.4'
            'Adara Pool 5'
            'Apple Store'
            'bells'
            'cirrus'
            'La Quinta Moore, OK'
            'LCTV - FREEWIFI'
            'pennygetyourownwifi'
            'pennyisafreeloader - 5G'
            'SouthwestWiFi'
            'Verizon - MiFi6620L - 3A6D'
            'Verizon - MiFi6620L - 950C'
            'Verizon - MiFi7730L - 3992'
            'viperdriver60'
            'piper'
        ]


def main():
    prompt = Prompt()
    screen = prompt.screen
    clock = pygame.time.Clock()

    while True:
        screen.fill(Prompt.Colors['black'])
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                exit()

        prompt.textinput.update(events)
        screen.blit(prompt.textinput.get_surface(), (10,10))
        pygame.display.update()
        clock.tick(30)


if __name__ == "__main__":
    main()
