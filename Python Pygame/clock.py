import pygame
import math
import time

screen_width = 600
screen_height = 600

pygame.init()

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Clock')


def draw_markings():
    d = 100
    d2 = 10
    for i in range(0, 360, 30):
        x1 = screen_width // 2 + d * math.cos(math.radians(i))
        y1 = screen_height // 2 + d * math.sin(math.radians(i))
        x2 = x1 + d2 * math.cos(math.radians(i))
        y2 = y1 + d2 * math.sin(math.radians(i))
        pygame.draw.line(screen, (255, 255, 255), (x1, y1), (x2, y2), 5)


def arc(center, radius, start, end, thickness, color):
    for i in range(start, end):
        x = center[0] + radius * math.cos(math.radians(i - 90))
        y = center[1] + radius * math.sin(math.radians(i - 90))
        pygame.draw.circle(screen, color, (int(x), int(y)), thickness)


def clock_hand(center, radius, angle, thickness, color):
    x = center[0] + radius * math.cos(math.radians(angle - 90))
    y = center[1] + radius * math.sin(math.radians(angle - 90))
    pygame.draw.line(screen, color, center, (int(x), int(y)), thickness)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()
    screen.fill((0, 0, 0))
    draw_markings()
    curr_time = time.strftime('%I%M%S', time.localtime(time.time()))
    s = int(curr_time[4]) * 10 + int(curr_time[5])
    m = int(curr_time[2]) * 10 + int(curr_time[3])
    h = int(curr_time[0]) * 10 + int(curr_time[1])
    arc((screen_width // 2, screen_height // 2), 200, 0, s * 6, 11, (0, 255, 0))
    arc((screen_width // 2, screen_height // 2), 180, 0, m * 6, 11, (0, 0, 255))
    arc((screen_width // 2, screen_height // 2), 160, 0, h * 30, 11, (255, 0, 0))
    clock_hand((screen_width // 2, screen_height // 2), 140, s * 6, 5, (0, 255, 0))
    clock_hand((screen_width // 2, screen_height // 2), 120, m * 6, 5, (0, 0, 255))
    clock_hand((screen_width // 2, screen_height // 2), 100, h * 30, 5, (255, 0, 0))
    pygame.display.update()
