# program by: tank king
# demonstration of flame particles

# requires pygame 2.0.0 for pygame.SCALED flag
# to use pygame 1.9.x remove the SCALED flag when initializing the display

import pygame
import sys
import random
import math

pygame.init()

# resolution is high for demonstration purposes
# FPS can be highly improved at lower resolutions
screen_width = 1280
screen_height = 720

screen = pygame.display.set_mode((screen_width, screen_height), pygame.SCALED | pygame.FULLSCREEN)
pygame.display.set_caption('Flame Sparks Testing')

clock = pygame.time.Clock()
FPS = 60

TARGET_FPS = 60

draw_circle = pygame.draw.circle
new_surface = pygame.Surface
randint = random.randint


class FlameParticle:
    alpha_layer_qty = 2
    alpha_glow_difference_constant = 0.75

    def __init__(self, x=50, y=50, r=5):
        self.x = x
        self.y = y
        self.r = r
        self.original_r = r
        self.alpha_layers = FlameParticle.alpha_layer_qty
        self.alpha_glow = FlameParticle.alpha_glow_difference_constant
        max_surf_size = 2 * self.r * self.alpha_layers * self.alpha_layers * self.alpha_glow
        self.surf = pygame.Surface((max_surf_size, max_surf_size), pygame.SRCALPHA)
        self.burn_rate = 0.05 * randint(1, 8)

    def update(self, dt):
        self.y -= (7 - self.r) * dt / 4
        self.x += randint(-self.r, self.r) * dt * 0.33
        self.original_r -= self.burn_rate * dt
        self.r = int(self.original_r)
        if self.r <= 0:
            self.r = 1

    def draw(self):
        max_surf_size = 2 * self.r * self.alpha_layers * self.alpha_layers * self.alpha_glow
        self.surf = new_surface((max_surf_size, max_surf_size), pygame.SRCALPHA)
        for i in range(self.alpha_layers, -1, -1):
            alpha = 255 - i * (255 // self.alpha_layers - 5)
            if alpha <= 0:
                alpha = 0
            radius = self.r * i * i * self.alpha_glow
            if self.r == 4 or self.r == 3:
                r, g, b = (255, 0, 0)
            elif self.r == 2 or self.r == 1:
                r, g, b = (255, 150, 0)
            else:
                r, g, b = (75, 75, 75)
            # r, g, b = (0, 0, 255)  # uncomment this to make the flame blue
            color = (r, g, b, alpha)
            draw_circle(self.surf, color, (self.surf.get_width() * 0.5, self.surf.get_height() * 0.5), radius)
        screen.blit(self.surf, self.surf.get_rect(center=(self.x, self.y)))


class Flame:
    def __init__(self, x=50, y=50):
        self.x = x
        self.y = y
        self.flame_intensity = 1
        self.flame_particles = []
        self.generate_flame_particles()

    def generate_flame_particles(self):
        self.flame_particles.clear()
        for i in range(int(self.flame_intensity) * 1):
            self.flame_particles.append(FlameParticle(self.x + randint(-1, -1), self.y, randint(1, 5)))

    def draw_flame(self, dt):
        for i in self.flame_particles:
            if i.original_r <= 0:
                self.flame_particles.remove(i)
                self.flame_particles.append(FlameParticle(self.x + randint(-1, -1), self.y, randint(1, 5)))
                del i
                continue
            i.update(dt)
            i.draw()


flames = []

color_ranges = {
    'white': '>225,>225>225',
    'red': '>100,<50,<50',
    'yellow': '>200,>200,<50',
    'black': '<50,<50,<50'
}


def check_color(color, condition: str):
    r, g, b = condition.split(',')
    r1, g1, b1 = color

    def compare(x, y, compare_type):
        x, y = int(x), int(y)
        if compare_type == '>':
            return x > y
        elif compare_type == '<':
            return x < y
        elif compare_type == '==':
            return x == y

    red_compare_results = compare(r1, r[1:], r[0])
    green_compare_results = compare(g1, g[1:], g[0])
    blue_compare_results = compare(b1, b[1:], b[0])

    if red_compare_results and green_compare_results and blue_compare_results:
        return True
    else:
        return False


def extract_points_from_img(image: pygame.Surface, image_color_range: dict, allowed_colors=('black', 'red')):
    extracted_points = []
    image.lock()
    for x in range(image.get_width()):
        for y in range(image.get_height()):
            pixel_color = image.get_at([x, y])
            r, g, b, alpha = pixel_color
            if alpha > 127:
                for color in list(image_color_range.keys()):
                    if color in allowed_colors:
                        if check_color((r, g, b), image_color_range[color]):
                            extracted_points.append([x, y])
    image.unlock()
    return extracted_points


img = pygame.image.load('durga1.png').convert()
img = pygame.transform.scale(img, (int(img.get_width() * 720 / img.get_height()), 720))
print('Loading Points...')
points = extract_points_from_img(img, color_ranges)
print('Points Loaded')


def remove_point_cluttering(point_list):
    # basic function to reduce the number of points
    # only keeps points for every 4th point iterated
    point_list.sort(key=lambda a: a[1])
    point_list = [i for i in point_list if point_list.index(i) % 4 == 0]
    return point_list


print('Removing Point Cluttering')
points = remove_point_cluttering(point_list=points)
print('Point Cluttering Reduced')

# shifting all points to center of screen
print('Shifting all points to center')
for p in points:
    p[0] += screen_width // 2 - img.get_width() // 2
print('All points shifted to center')

# circular points
points2 = [[screen_width // 2 + 25 + screen_height // 2 * math.cos(math.radians(i)), screen_height // 2 + screen_height // 2 * math.sin(math.radians(i))] for i in range(360)]


def main_game():
    dt = 1
    surf = pygame.Surface(screen.get_size())  # to make the background fade away
    surf.set_alpha(0)
    alpha = 0
    start = True  # set it to False if you want to manually trigger the animation after loading
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit(0)
            if e.type == pygame.KEYDOWN:
                # manually trigger the animation by pressing any key
                start = True
                if e.key == pygame.K_ESCAPE:
                    sys.exit(0)
        screen.fill((0, 0, 0))
        screen.blit(img, (screen_width // 2 - img.get_width() // 2, 0))
        screen.blit(surf, (0, 0))  # the fading effect can also be done by changing the alpha of the image directly (can be used to improve FPS)
        if start:
            if len(flames) < len(points):
                qty = 5 if len(points) - len(flames) > 5 else len(points) - len(flames)
                for _ in range(qty):
                    flames.append(Flame(*points[len(flames)]))
            else:
                alpha += 0.5
                if alpha > 255:
                    alpha = 255
                surf.set_alpha(int(alpha))
        if alpha >= 255:
            if len(flames) < len(points) + len(points2):
                temp = Flame(*points2[len(flames) - len(points)])
                temp.flame_intensity = 10
                temp.generate_flame_particles()
                flames.append(temp)
        for i in flames:
            i.draw_flame(dt)
        pygame.display.update()
        pygame.display.set_caption('Flame Particles Testing FPS = ' + str(int(clock.get_fps())))
        dt = TARGET_FPS * clock.tick(FPS) * 0.001


main_game()
