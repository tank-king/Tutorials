import asyncio
import math
import os.path
import platform
import random
import sys
import time
from functools import lru_cache
from operator import attrgetter

import pygame
import pygame.mixer
from pygame.math import clamp

if sys.platform == "emscripten":
    platform.window.canvas.style.imageRendering = "pixelated"

RES = 1
W, H = 576 * RES, 324 * RES
SCREEN_RECT = pygame.Rect(0, 0, W, H)
SCREEN_COLLISION_RECT = SCREEN_RECT.inflate(500, 200)


GRAVITY = +0.01

pygame.init()

CAR_WINDOW_SOUND = pygame.mixer.Sound(os.path.join('assets', 'sounds', 'car-window.ogg'))
RAIN_SOUND = pygame.mixer.Sound(os.path.join('assets', 'sounds', 'rain.ogg'))
CAR_ENGINE_SOUND = pygame.mixer.Sound(os.path.join('assets', 'sounds', 'driving-ambience.ogg'))


class CHANNELS:
    CAR_WINDOW = pygame.mixer.Channel(0)
    RAIN = pygame.mixer.Channel(1)
    ENGINE = pygame.mixer.Channel(2)


def music_init():
    CHANNELS.CAR_WINDOW.set_source_location(-180, 200)
    CHANNELS.RAIN.play(RAIN_SOUND, -1)
    CHANNELS.RAIN.set_volume(0.0)
    CHANNELS.ENGINE.play(CAR_ENGINE_SOUND, -1)
    CHANNELS.ENGINE.set_volume(0.0)


def map_to_range(value, from_x, from_y, to_x, to_y):
    """map the pos from one range to another"""
    return clamp(value * (to_y - to_x) / (from_y - from_x), to_x, to_y)


@lru_cache(maxsize=100)
def load_image(path, scale, alpha=True, smooth=False):
    path = os.path.join('assets', 'images', path)
    img = pygame.image.load(path)
    if not alpha:
        img.set_colorkey('black')
    scale_func = pygame.transform.scale_by if not smooth else pygame.transform.smoothscale_by
    return scale_func(img.convert_alpha() if alpha else img.convert(), scale)


class Color(pygame.Color):
    def shade_factor(self, k):
        return Color(self.r * k, self.g * k, self.b * k)


class Timer:
    def __init__(self, timeout=0.0, reset=True):
        self.timeout = timeout
        self.timer = time.time()
        self.paused_timer = time.time()
        self.paused = False
        self._reset = reset
        self._callback = None

    def set_timeout(self, timeout):
        self.timeout = timeout

    def set_callback(self, callback):
        self._callback = callback

    def reset(self):
        self.timer = time.time()

    def pause(self):
        self.paused = True
        self.paused_timer = time.time()

    def resume(self):
        self.paused = False
        self.timer -= time.time() - self.paused_timer

    @property
    def elapsed(self):
        if self.paused:
            return time.time() - self.timer - (time.time() - self.paused_timer)
        return time.time() - self.timer

    @property
    def tick(self):
        if self.timeout == 'inf':
            return False
        if self.elapsed > self.timeout:
            if self._reset:
                self.reset()  # reset timer
            else:
                self.timeout = 'inf'
            if self._callback:
                self._callback()
            return True
        else:
            return False


class BaseStructure:
    def update(self, events: list[pygame.event.Event], dt):
        pass

    def draw(self, surf: pygame.Surface):
        pass


class BaseObject(BaseStructure):
    @property
    def z(self):
        return 0

    def interact_with(self, others: list['BaseObject']):
        pass


class SpriteBasedObject(BaseObject):
    def __init__(self, x, y, sprite_path, scale=4):
        self.sprite = load_image(sprite_path, scale)
        self.pos = pygame.Vector2(x, y)
        self.x, self.y = self.pos

    def collision_rect(self):
        return self.sprite.get_rect(center=self.pos).scale_by(0.9, 0.9)

    def draw(self, surf: pygame.Surface):
        surf.blit(self.sprite, self.sprite.get_rect(center=self.pos))


class ScrollingImage(BaseObject):
    def __init__(self, x, y, path, scale=1.0, alpha=True):
        self.x, self.y = x, y
        self.img = load_image(path, scale, alpha=alpha)
        self.img.set_colorkey('black')
        self.offset = pygame.Vector2(0, 0)  # supposed to roll over
        self.surf = pygame.Surface([*self.img.get_size()])
        self.surf.set_colorkey('black')

    def move(self, dx, dy):
        x, y = self.offset
        x = math.fmod((x + dx), self.img.get_width())
        y = math.fmod((y + dy), self.img.get_height())
        self.offset = pygame.Vector2(x, y)

    def draw(self, surf: pygame.Surface):
        w, h = self.img.get_size()
        dx, dy = int(self.offset.x), int(self.offset.y)
        self.surf.fill(0)
        self.surf.blit(self.img, [dx, dy])
        if dx > 0:
            self.surf.blit(self.img, [dx - w, dy], [w - dx, 0, dx, h])
        elif dx < 0:
            self.surf.blit(self.img, [dx + w, dy], [0, 0, w - dx, h])
        surf.blit(self.surf, [self.x, self.y])


class ParallaxScrollingImage(BaseObject):
    def __init__(self, x, y, image_paths, motion_factors, alpha=None, speed=100.0, scale=1.0):
        self.x, self.y = x, y
        if not alpha:
            alpha = [True] * len(image_paths)
        self.images = [ScrollingImage(x, y, path, scale=scale, alpha=alpha[i]) for i, path in enumerate(image_paths)]
        n = len(self.images)
        self.motion_factors = motion_factors if motion_factors else [i / n for i in range(n)]
        self.speed = speed

    def update(self, events: list[pygame.event.Event], dt):
        for i, j in enumerate(self.images):
            j.move(self.speed * dt * self.motion_factors[i], 0)

    def draw(self, surf: pygame.Surface):
        for i in self.images:
            i.draw(surf)


class RainParticle(BaseObject):
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle
        self.speed = 10
        self.dx = math.cos(math.radians(self.angle))
        self.dy = -math.sin(math.radians(self.angle))
        self.destroyed = False

    @property
    def pos(self):
        return [self.x, self.y]

    def update(self, events: list[pygame.event.Event], dt):
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        if not SCREEN_COLLISION_RECT.collidepoint(self.pos):
            self.destroyed = True


class Rain(BaseObject):
    def __init__(self):
        self.img = load_image('rain_drop.png', 1)
        self.img.set_colorkey('black')
        self.angle = 180 + 45
        self.particles: list[RainParticle] = []
        self.timer = Timer(1 / 60)

    def update(self, events: list[pygame.event.Event], dt):
        if self.timer.tick:
            self.particles.append(RainParticle(random.randint(0, int(W * 1.5)), -40, self.angle))
        self.particles = [i for i in self.particles if not i.destroyed]
        for i in self.particles:
            i.update(events, dt)

    def draw(self, surf: pygame.Surface):
        surf.fblits([(self.img, self.img.get_rect(center=i.pos)) for i in self.particles])


class Window(BaseObject):
    def __init__(self):
        self.rect = pygame.FRect(0, 0, W, H)
        self.s = pygame.Surface([*self.rect.size])
        self.s1 = self.s.copy()
        self.s2 = self.s.copy()
        self.timer = Timer(1 / 24)  # 24 FPS is the original FPS of recording of video
        self.curr_frame = 0

        def generate_strings():
            results = []
            for i in range(0, 2):  # hundreds place (0, 1)
                for j in range(0, 10):  # tens place (0-9)
                    for k in range(0, 5):  # units place (0-4)
                        results.append(f"{i}{j}{k}")
                        if i == 1 and j == 2 and k == 4:
                            return results
            return results

        self.images = [load_image(os.path.join('rain', f'frame_{i}.png'), RES * 0.3, alpha=False) for i in
                       generate_strings()[1:]]
        self.defog_timer = Timer(0.1)

    def pull_up(self, amt=1):
        self.rect = pygame.FRect(self.rect.x, self.rect.y - amt, self.rect.w, self.rect.h + amt)
        self.rect.y = pygame.math.clamp(self.rect.y, 0, H - 1)
        self.rect.h = pygame.math.clamp(self.rect.h, 1, H)
        self.s = pygame.Surface([*self.rect.size])
        self.s1 = self.s.copy()
        if not CHANNELS.CAR_WINDOW.get_busy():
            CHANNELS.CAR_WINDOW.play(CAR_WINDOW_SOUND, -1)
        if self.rect.y == 0 or self.rect.y == H:
            CHANNELS.CAR_WINDOW.stop()

    def pull_down(self, amt=1):
        self.pull_up(-amt)

    def update(self, events: list[pygame.event.Event], dt):
        if self.timer.tick:
            self.curr_frame += 1
            self.curr_frame %= len(self.images)
        keys = pygame.key.get_pressed()
        vec = 0
        if keys[pygame.K_DOWN]:
            vec -= 1
        if keys[pygame.K_UP]:
            vec += 1

        if vec:
            self.pull_up(vec * dt * 2)
        else:
            pass
            CHANNELS.CAR_WINDOW.stop()

        CHANNELS.RAIN.set_volume(map_to_range(self.rect.y, 0, H / 4, 0.02, 1))
        CHANNELS.ENGINE.set_volume(map_to_range(self.rect.y, 0, H / 4, 0.1, 1))

    def draw(self, surf: pygame.Surface):
        s = surf.subsurface(self.rect).copy()
        pygame.transform.box_blur(s, 100, dest_surface=self.s)
        # self.s.fill([220] * 3, special_flags=pygame.BLEND_RGB_MULT)
        self.s1.blit(s, [0, 0])
        # self.s1.fill([155] * 3, special_flags=pygame.BLEND_RGB_MULT)
        # pygame.draw.rect(self.s1, 'black', [0, 0, 200, H])
        if self.rect.y > 10:
            self.defog_timer.timeout = 1
        else:
            self.defog_timer.timeout = 0.1
        if self.defog_timer.tick:
            self.s2.fill([1] * 3, special_flags=pygame.BLEND_RGB_SUB)
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            pygame.draw.circle(self.s2, 'white', [mx, my - self.rect.y], 40)
        self.s1.blit(self.s2, [0, 0], special_flags=pygame.BLEND_RGB_MULT)
        self.s.blit(self.s1, [0, 0], special_flags=pygame.BLEND_RGB_MAX)
        self.s.blit(self.images[self.curr_frame], [0, 0], special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(self.s, self.rect)
        pygame.draw.line(surf, 'gray', [self.rect.x, self.rect.y - 1], [self.rect.x + self.rect.w, self.rect.y - 1],
                         math.ceil(RES))


class Game:
    def __init__(self):
        music_init()
        self.screen = pygame.display.set_mode([W, H])
        t = pygame.font.Font(os.path.join('assets', 'fonts', '04B_30__.TTF'), 25).render('Loading...', False, 'white')
        self.screen.blit(t, t.get_rect(center=SCREEN_RECT.center))
        pygame.display.update()
        self.clock = pygame.time.Clock()
        self.objects: list[BaseObject] = []
        self.full_screen = True
        # self.init_objects()

    def init_objects(self):
        self.objects = [
            ParallaxScrollingImage(0, 0, [os.path.join('bg', f'{i}.png') for i in [1, 2, 3, 4]], [0, 0.01, 0.5, 1],
                                   [False, False, False, False], -15, scale=RES),
            Rain(),
            Window(),
        ]

    def handle_events(self, events, dt):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE and sys.platform != 'emscripten':
                    sys.exit(0)
                if e.key == pygame.K_r:
                    # self.window.destroy()
                    self.init_objects()
                if e.key == pygame.K_f:
                    self.full_screen = not self.full_screen
                    if self.full_screen:
                        pygame.display.set_mode([W, H], pygame.SCALED | pygame.FULLSCREEN)
                    else:
                        pygame.display.set_mode([W, H], pygame.RESIZABLE)
            if e.type == pygame.QUIT:
                sys.exit(0)
        # self.objects.sort(key=attrgetter('z'))
        for i in self.objects:
            i.update(events, dt)
            i.interact_with(self.objects)

        # sound updates

    def draw(self, surf: pygame.Surface):
        for i in self.objects:
            i.draw(surf)

    async def run(self):
        self.init_objects()
        fps = 0
        # pygame.mouse.set_visible(False)
        try:
            dt = 1 / fps
        except ZeroDivisionError:
            dt = 0
        while True:
            events = pygame.event.get()
            self.handle_events(events, dt)
            self.draw(self.screen)
            pygame.display.update()
            dt = self.clock.tick(fps) * 0.001 * 60 * RES
            title = f'FPS = {self.clock.get_fps().__int__()}'
            pygame.display.set_caption(title)
            await asyncio.sleep(0)


asyncio.run(Game().run())
