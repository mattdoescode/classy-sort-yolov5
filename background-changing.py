import pygame
import sys

black = (0,0,0)
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
gray = (150,150,150)
yellow = (250,220, 65)


colors = [black,red,green,blue,gray,yellow]

pygame.init()
screen = pygame.display.set_mode((2560,1440))

clock = pygame.time.Clock()
time_elapsed_since_last_action = 0

color_index = 0

while 1:
    dt = clock.tick() 
    time_elapsed_since_last_action += dt
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

    if time_elapsed_since_last_action > 18000:
        color_index = (color_index + 1) % len(colors)
        time_elapsed_since_last_action = 0

    screen.fill(colors[color_index])
    pygame.display.flip()