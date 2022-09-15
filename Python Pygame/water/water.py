import math
import sys
from random import randint, random
from typing import Union

import pygame

Point = pygame.Vector2

# INITIAL RUNTIME CONFIGURATIONS

# You can edit these accordingly based on the modules you have

SMOOTH = True  # uses numpy + scipy
TEXTURE = True  # uses texture images
VOLUME_RISE = True
USE_PYMUNK = True  # uses pymunk
FPS = 60
GRAVITY = (0, 500)
DISPLAY_HELP = True

if SMOOTH:
    import numpy
    from scipy.interpolate import interp1d
if USE_PYMUNK:
    import pymunk

pygame.init()

screen_width = 1200
screen_height = 720

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Water')

clock = pygame.time.Clock()


font = pygame.font.SysFont('consolas', 25)

if USE_PYMUNK:
    space = pymunk.Space()
    space.gravity = GRAVITY

if TEXTURE:
    ROCK_IMAGE = pygame.image.load('rock.png').convert_alpha()
    BALL_IMAGE = pygame.image.load('ball.png').convert_alpha()


def map_to_range(value, from_x, from_y, to_x, to_y):
    return value * (to_y - to_x) / (from_y - from_x)


def create_rock(_space, x=None, y=None):
    if x is None:
        x = screen_width // 2 + random()
    if y is None:
        y = 0
    mass = randint(2, 10)
    body = pymunk.Body(mass=mass * 5, moment=mass * 1, body_type=pymunk.Body.DYNAMIC)
    body.position = (x + random(), y)
    body.splashed = False
    shape = pymunk.Circle(body, body.mass * 1)
    if TEXTURE:
        shape.img = ROCK_IMAGE
        shape.img = pygame.transform.scale(shape.img, (shape.radius * 2, shape.radius * 2))
    shape.friction = 0.05
    _space.add(body, shape)
    return shape


def draw_rock(rock, surf: pygame.Surface):
    if TEXTURE:
        try:
            angle = round(math.degrees(rock.body.angle))
        except ValueError:
            angle = 0
        img = pygame.transform.rotate(rock.img, -angle)
        surf.blit(img, img.get_rect(center=rock.body.position))
    else:
        pygame.draw.circle(surf, 'brown', rock.body.position, rock.radius)


def display_help():
    _text = [
        'Press ... to toggle',
        '',
        'S - Smoothness',
        'T - texture',
        'V - water rise',
        'P - use of pymunk',
        'H - help',
    ]
    y = 0
    for i in _text:
        y += 20
        text = font.render(i, True, 'white')
        screen.blit(text, (25, y))


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.height = randint(2, 10)
        self.width = randint(5, 50 + 20)
        self.dy = 0
        self.spring: Union['WaterSpring', None] = None
        self.next_spring: Union['WaterSpring', None] = None
        self.rot = randint(0, 360)
        self.rot = 0
        self.gravity = 0.5
        self.water_force = 2
        self.on_water_surface = False

    def update(self):
        if self.spring:
            if self.on_water_surface:
                self.y = self.spring.height - self.height
            else:
                self.dy -= self.water_force
                self.y += self.dy
                if self.dy < 0 and self.y < self.spring.height:
                    self.on_water_surface = True
        else:
            self.dy += self.gravity
            self.y += self.dy

    def draw(self, surf: pygame.Surface):
        size = 50
        if TEXTURE:
            img = pygame.transform.scale(BALL_IMAGE, (size, size))
            surf.blit(img, img.get_rect(center=(self.x, self.y)))
        else:
            pygame.draw.circle(surf, 'green', (self.x, self.y), size / 2)


class WaterSpring:
    def __init__(self, x=0, target_height=None):
        if not target_height:
            self.target_height = screen_height // 2 + 150
        else:
            self.target_height = target_height
        self.dampening = 0.05  # adjust accordingly
        self.tension = 0.01
        self.height = self.target_height
        self.vel = 0
        self.x = x

    def update(self):
        dh = self.target_height - self.height
        if abs(dh) < 0.01:
            self.height = self.target_height
        self.vel += self.tension * dh - self.vel * self.dampening
        self.height += self.vel

    def draw(self, surf: pygame.Surface):
        pygame.draw.circle(surf, 'white', (self.x, self.height), 1)


class Wave:
    def __init__(self):
        diff = 20
        self.springs = [WaterSpring(x=i * diff + 0) for i in range(screen_width // diff + 2)]
        self.points = []
        self.diff = diff

    def get_spring_index_for_x_pos(self, x):
        return int(x // self.diff)

    def get_target_height(self):
        return self.springs[0].target_height

    def set_target_height(self, height):
        for i in self.springs:
            i.target_height = height

    def add_volume(self, volume):
        height = volume / screen_width
        self.set_target_height(self.get_target_height() - height)

    def update(self):
        for i in self.springs:
            i.update()
        self.spread_wave()
        self.points = [Point(i.x, i.height) for i in self.springs]
        if SMOOTH:
            self.points = get_curve(self.points)
        self.points.extend([Point(screen_width, screen_height), Point(0, screen_height)])

    def draw(self, surf: pygame.Surface):
        pygame.draw.polygon(surf, (0, 0, 255, 50), self.points)

    def draw_line(self, surf: pygame.Surface):
        pygame.draw.lines(surf, 'white', False, self.points[:-2], 5)

    def spread_wave(self):
        spread = 0.1
        for i in range(len(self.springs)):
            if i > 0:
                self.springs[i - 1].vel += spread * (self.springs[i].height - self.springs[i - 1].height)
            try:
                self.springs[i + 1].vel += spread * (self.springs[i].height - self.springs[i + 1].height)
            except IndexError:
                pass

    def splash(self, index, vel):
        try:
            self.springs[index].vel += vel
        except IndexError:
            pass


def get_curve(points):
    x_new = numpy.arange(points[0].x, points[-1].x, 1)
    x = numpy.array([i.x for i in points[:-1]])
    y = numpy.array([i.y for i in points[:-1]])
    f = interp1d(x, y, kind='cubic', fill_value='extrapolate')
    y_new = f(x_new)
    x1 = list(x_new)
    y1 = list(y_new)
    points = [Point(x1[i], y1[i]) for i in range(len(x1))]
    return points


def create_walls():
    base = pymunk.Body(mass=10 ** 5, moment=0, body_type=pymunk.Body.STATIC)
    base.position = (screen_width // 2, screen_height + 25)
    base_shape = pymunk.Poly.create_box(base, (screen_width, 50))
    base_shape.friction = 0.2
    space.add(base, base_shape)

    wall_left = pymunk.Body(mass=10 ** 5, moment=0, body_type=pymunk.Body.STATIC)
    wall_left.position = (-50, screen_height // 2)
    wall_left_shape = pymunk.Poly.create_box(wall_left, (100, screen_height))
    space.add(wall_left, wall_left_shape)

    wall_right = pymunk.Body(mass=10 ** 5, moment=0, body_type=pymunk.Body.STATIC)
    wall_right.position = (screen_width + 50, screen_height // 2)
    wall_right_shape = pymunk.Poly.create_box(wall_right, (100, screen_height))
    space.add(wall_right, wall_right_shape)


def main_game():
    global USE_PYMUNK, SMOOTH, VOLUME_RISE, TEXTURE, DISPLAY_HELP
    if USE_PYMUNK:
        create_walls()
    wave = Wave()
    s = pygame.Surface(screen.get_size(), pygame.SRCALPHA).convert_alpha()
    objects: list[pymunk.Circle] = []
    floating_objects: list[Ball] = []

    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                sys.exit(0)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    sys.exit(0)
                if e.key == pygame.K_s:
                    SMOOTH = not SMOOTH
                if e.key == pygame.K_v:
                    VOLUME_RISE = not VOLUME_RISE
                if e.key == pygame.K_p:
                    USE_PYMUNK = not USE_PYMUNK
                if e.key == pygame.K_t:
                    TEXTURE = not TEXTURE
                if e.key == pygame.K_h:
                    DISPLAY_HELP = not DISPLAY_HELP
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1 and USE_PYMUNK:
                    mx, my = pygame.mouse.get_pos()
                    rock = create_rock(space, mx, my)
                    objects.append(rock)
                if e.button == 3:
                    mx, my = pygame.mouse.get_pos()
                    floating_objects.append(Ball(mx, my))
        if USE_PYMUNK:
            space.step(1 / FPS)
        screen.fill('black')
        s.fill(0)
        for i in objects:
            if not i.body.splashed:
                if i.body.position.y + i.radius > wave.get_target_height():
                    i.body.splashed = True
                    wave.splash(index=wave.get_spring_index_for_x_pos(i.body.position.x), vel=i.radius)
                    if VOLUME_RISE:
                        wave.add_volume(i.radius ** 2 * math.pi)
            draw_rock(i, screen)
        for i in floating_objects:
            i.update()
            i.draw(screen)
            index = wave.get_spring_index_for_x_pos(i.x)
            if i.y > wave.get_target_height():
                if not i.spring:
                    i.spring = wave.springs[index]
                    try:
                        i.next_spring = wave.springs[index + 1]
                    except IndexError:
                        pass
                    wave.splash(index, 2)
        wave.update()
        wave.draw(s)
        screen.blit(s, (0, 0))
        wave.draw_line(screen)
        if DISPLAY_HELP:
            display_help()
        pygame.display.update()
        clock.tick(FPS)
        # print(clock.get_fps())


main_game()
