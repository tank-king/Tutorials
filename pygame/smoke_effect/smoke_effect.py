import pygame
import random

screen_width = 750
screen_height = 650

screen = pygame.display.set_mode((screen_width, screen_height))

clock = pygame.time.Clock()
FPS = 60


def scale(img: pygame.Surface, factor):
    w, h = img.get_width() * factor, img.get_height() * factor
    return pygame.transform.scale(img, (int(w), int(h)))


IMAGE = pygame.image.load('smoke.png').convert_alpha()


class SmokeParticle:
    def __init__(self, x=screen_width // 2, y=screen_height // 2):
        self.x = x
        self.y = y
        self.scale_k = 0.1
        self.img = scale(IMAGE, self.scale_k)
        self.alpha = 255
        self.alpha_rate = 3
        self.alive = True
        self.vx = 0
        self.vy = 4 + random.randint(7, 10) / 10
        self.k = 0.01 * random.random() * random.choice([-1, 1])

    def update(self):
        self.x += self.vx
        self.vx += self.k
        self.y -= self.vy
        self.vy *= 0.99
        self.scale_k += 0.005
        self.alpha -= self.alpha_rate
        if self.alpha < 0:
            self.alpha = 0
            self.alive = False
        self.alpha_rate -= 0.1
        if self.alpha_rate < 1.5:
            self.alpha_rate = 1.5
        self.img = scale(IMAGE, self.scale_k)
        self.img.set_alpha(self.alpha)

    def draw(self):
        screen.blit(self.img, self.img.get_rect(center=(self.x, self.y)))


class Smoke:
    def __init__(self, x=screen_width // 2, y=screen_height // 2 + 150):
        self.x = x
        self.y = y
        self.particles = []
        self.frames = 0

    def update(self):
        self.particles = [i for i in self.particles if i.alive]
        self.frames += 1
        if self.frames % 2 == 0:
            self.frames = 0
            self.particles.append(SmokeParticle(self.x, self.y))
        for i in self.particles:
            i.update()

    def draw(self):
        for i in self.particles:
            i.draw()


smoke = Smoke()


def main_game():
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                quit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    quit()
        screen.fill((0, 0, 0))
        smoke.update()
        smoke.draw()
        pygame.display.update()
        clock.tick(FPS)
        pygame.display.set_caption(f'FPS = {clock.get_fps()}')


main_game()
