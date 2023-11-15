import asyncio
import time
from functools import lru_cache

import pygame
from pygame.math import clamp

pygame.init()
W, H = 1000, 800
screen = pygame.display.set_mode([W, H])
SCREEN_RECT = pygame.Rect(0, 0, W, H)

BG = pygame.image.load('bg.png').convert()
BG.fill([40] * 3, special_flags=pygame.BLEND_RGB_MULT)

IMAGE_SIZE = [100, 100]
TEXT_SIZE = 2000 // 2
RELATIVE_DIR = ''
FONT = pygame.font.Font('font3.ttf', TEXT_SIZE)
FONT_SIZE = FONT.render('|', True, 'white').get_size()
clock = pygame.time.Clock()
TARGET_FPS = 60
pygame.key.set_repeat(500, 50)


class Rect:
    def __init__(self, x, y=None, w=None, h=None):
        if isinstance(x, pygame.Rect):
            self.x, self.y, self.w, self.h = x
        else:
            self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def width(self):
        return self.w

    @property
    def height(self):
        return self.h

    def move(self, x, y):
        self.x = x
        self.y = y

    def move_top_left(self, x, y):
        self.x = x
        self.y = y

    def move_bottom_left(self, x, y):
        self.x = x
        self.y = y - self.height

    def move_center(self, x, y):
        self.x = x - self.width // 2
        self.y = y - self.height // 2

    @property
    def center(self):
        return self.x + self.w / 2, self.y + self.h / 2

    @center.setter
    def center(self, value):
        self.move_center(*value)

    @property
    def size(self):
        return [self.w, self.h]

    @property
    def rect(self):
        return [self.x, self.y, self.w, self.h]

    def __getitem__(self, item):
        return self.rect.__getitem__(item)


def colliderect(rect1, rect2):
    left1, top1, width1, height1 = rect1
    left2, top2, width2, height2 = rect2

    right1, bottom1 = left1 + width1, top1 + height1
    right2, bottom2 = left2 + width2, top2 + height2

    # Check for no collision
    if (right1 <= left2) or (right2 <= left1) or (bottom1 <= top2) or (bottom2 <= top1):
        return False
    else:
        return True


def lerp(val, to, step):
    step = clamp(step, 0, 0.9999999999)
    return pygame.Vector2(val, val).lerp([to, to], step).x


class Timer:
    def __init__(self, timeout):
        self.timeout = timeout
        self.timer = time.time()

    @property
    def tick(self):
        if time.time() - self.timer >= self.timeout:
            self.timer = time.time()
            return True
        else:
            return False


class FrameTimer:
    def __init__(self, timeout):
        self.timeout = timeout
        self.total_frames = timeout * TARGET_FPS
        self.frames = 0

    def step(self, dt):
        self.frames += dt

    @property
    def tick(self):
        if self.frames >= self.total_frames:
            self.frames = 0
            return True
        else:
            return False


class TextObject:
    def __init__(self, name, size, desc, heading=None, offset: float = 0, rel_scale=0.6):
        self.pos = pygame.Vector2()
        self.name = name
        self.heading = name if not heading else heading
        self.size = size
        self.desc = desc
        self.offset = offset
        self.rel_scale = rel_scale  # how much window it will occupy vertically
        self.img = self.get_image(name)
        self.img_size = self.img.get_size()
        self.ratio = self.img_size[0] / self.img_size[1]
        self.points = [pygame.Vector2(*i) - [self.img.get_width() // 2, self.img.get_height() // 2] for i in
                       pygame.mask.from_surface(self.img).outline(5)]
        self.text_for_size = self.get_text_for_size()
        self.reflection_map = self.get_reflection_light_map()

    @staticmethod
    def get_reflection_light_map():
        s = pygame.Surface([100, 255])
        for i in range(255):
            a = lerp(255, 0, i ** 1.2 / 255)
            pygame.draw.line(s, [a, a, a], [0, i], [100, i], 1)
        return s

    def get_text_for_size(self):
        number = self.size
        if abs(number) >= 10 ** 12:
            return f"{number // 10 ** 12} trillion"
        elif abs(number) >= 10 ** 9:
            return f"{number // 10 ** 9} billion"
        elif abs(number) >= 10 ** 6:
            return f"{number // 10 ** 6} million"

        s = str(self.size)[::-1]
        arr = [[]]
        c = 0
        for i in s:
            c += 1
            arr[-1].append(i)
            if c % 3 == 0:
                arr.append([])

        arr = arr[::-1]
        result = ' '.join([''.join(i[::-1]) for i in arr])

        if len(s) % 3 == 0:
            result = result[1:]
        return result

    # @lru_cache(maxsize=100)
    def get_points(self, pos, scale=1):
        points = [(i * scale + pos) for i in self.points]
        print(self.name, pos, points)
        return points

    def get_image(self, text):
        t = FONT.render(text, True, 'white')
        s = FONT.render('@', True, 'white')
        surf = t.subsurface(t.get_bounding_rect())
        img = pygame.Surface([surf.get_width(), s.get_bounding_rect().h])
        if self.name != '|':
            img.blit(surf, surf.get_rect(midbottom=[img.get_width() // 2, img.get_rect().bottom - self.offset]))
        else:
            img.blit(surf, surf.get_rect(bottom=img.get_rect().bottom - self.offset, right=img.get_rect().right + 50))
        img.set_colorkey('black')
        # img.blit(surf, surf.get_rect(midbottom=img.get_rect().midbottom))
        return img

    @property
    def width(self):
        rect = self.img.get_rect()
        ratio = self.size / rect.h
        return rect.w * ratio

    def rect(self, pos=(0, 0), scale=1) -> Rect:
        rect = self.img.get_rect()
        rect = Rect(rect)
        # scale by the height (as width can vary always, but the height is always 1 line)
        ratio = self.size / rect.h
        rect.w *= ratio
        rect.h = self.size * scale
        rect.w *= scale
        rect.center = pos
        return rect

    @lru_cache(maxsize=20)
    def image(self, scale=1):
        try:
            img = pygame.transform.smoothscale(self.img, self.rect([0, 0], scale).size)
        except pygame.error:
            img = self.img
        return img

    @lru_cache(maxsize=20)
    def reflection(self, scale=1):
        img = pygame.transform.flip(self.image(scale), False, True)
        # s = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        # s.blit(img, [0, 0])
        t = pygame.transform.scale(self.reflection_map, img.get_size())
        img.blit(t, [0, 0], special_flags=pygame.BLEND_RGBA_MULT)
        return img

    @lru_cache(maxsize=20)
    def size_text(self, scale=1):
        t = pygame.font.Font('font.ttf', round(clamp(self.size * scale * 0.2, 0, TEXT_SIZE))).render(
            str(self.text_for_size) + ' km', True, 'white')
        return t

    @lru_cache(maxsize=20)
    def heading_text(self, scale=1):
        f = pygame.font.Font('font1.ttf', round(clamp((self.size * scale * 0.1), 0, TEXT_SIZE)))
        t = f.render(self.heading, True, 'white')
        return t

    def update(self, events: list[pygame.event.Event], dt=1):
        pass

    def draw(self, surf: pygame.Surface, pos, scale=1):
        rect = self.rect(pos, scale)
        if pos.x - rect.w / 2 > W + 100 or pos.x + rect.w / 2 < 0:
            return
        if rect.w <= 2:
            if self.name == '*':
                print(self.size * scale, rect)
            return
        if not colliderect(SCREEN_RECT, rect):
            return
        # print(self.name, rect, SCREEN_RECT, colliderect(SCREEN_RECT, rect))
        img = self.image(scale)
        # surf.blit(img, (0, 0))

        surf.blit(img, img.get_rect(center=pos))
        p = img.get_rect(center=pos).bottomleft
        surf.blit(self.reflection(scale), p)

        pygame.draw.line(surf, 'white', [0, p[1]], [W, p[1]], 2)
        t = self.size_text(scale)
        t_rect = t.get_rect(midright=img.get_rect(center=pos).topleft)
        surf.blit(t, t_rect)
        t = self.heading_text(scale)
        surf.blit(t, t.get_rect(center=t_rect.midtop))


class Camera:
    def __init__(self):
        self.scale = 1
        self.pos = pygame.Vector2()
        self.target_pos = pygame.Vector2()
        self.lerp_rate = 0.1
        self.target_scale = 1
        self.scale_lerp_rate = 0.1

    def update_scale(self, scale):
        self.scale = scale

    def move_to(self, pos, rate: float = 1):
        self.target_pos = pygame.Vector2(pos)
        self.lerp_rate = rate

    def set_zoom(self, scale, rate: float = 1):
        self.target_scale = scale
        self.scale_lerp_rate = rate

    def change_zoom_by(self, zoom):
        self.set_zoom(self.scale + zoom)

    def update(self, dt=1):
        d = 0.0000000000001
        self.scale = lerp(self.scale, self.target_scale, self.scale_lerp_rate * dt)
        self.pos = self.pos.lerp(self.target_pos, clamp(self.lerp_rate * dt, 0, 0.9999999))
        self.scale = clamp(self.scale, d, 10000)
        self.target_scale = clamp(self.target_scale, d, 10000)

        if abs(self.target_scale - self.scale) < d:
            self.scale = self.target_scale

    def draw(self, objects: list[TextObject], surf: pygame.Surface):
        for i in objects:
            i.draw(surf, (i.pos - self.pos) * self.scale + [W // 2, H // 2], self.scale)


class Stage:
    def __init__(self, initial_objects: list[TextObject]):
        self.objects: list[TextObject] = initial_objects if initial_objects is not None else []
        self.arrange_objects()
        self.camera = Camera()
        self.timer = FrameTimer(4.5)
        # self.curr_obj_index = len(self.objects) - 1
        self.curr_obj_index = 0
        self.camera.pos = self.objects[self.curr_obj_index].pos

    def arrange_objects(self):
        if not self.objects:
            self.objects.append(TextObject("<UNTITLED>", 100, "yooo"))
        last_obj = self.objects[0]
        last_obj.pos.y = -last_obj.rect().h // 2
        for i in self.objects[1:]:
            i.pos = last_obj.pos + [last_obj.rect().w // 2 + i.width // 2 + i.size * 1 / 2, 0]
            i.pos.y = -i.size // 2
            # i.pos.y = (r := i.rect()).bottom - r.h
            last_obj = i

    def next_object(self):
        self.curr_obj_index += 1
        if self.curr_obj_index >= len(self.objects):
            self.curr_obj_index -= 1

    def prev_object(self):
        self.curr_obj_index -= 1
        if self.curr_obj_index < 0:
            self.curr_obj_index += 1

    def reset(self):
        self.__init__(self.objects)

    def update(self, events: list[pygame.event.Event], dt=1):
        self.camera.move_to(((obj := self.objects[self.curr_obj_index]).pos.x - obj.size * 0.5, obj.pos.y), 0.1)
        self.camera.set_zoom((H / obj.size) * obj.rel_scale, 0.2)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RIGHT:
                    self.next_object()
                if e.key == pygame.K_LEFT:
                    self.prev_object()
        for i in self.objects:
            i.update(events, dt)
        self.camera.update(dt)
        if self.timer.tick:
            self.next_object()
        self.timer.step(dt)
        # self.camera.pos += [dt, dt * 0.2]

    def draw(self, surf: pygame.Surface, scale=1):
        self.camera.draw(self.objects, surf)


async def main():
    __size = 10

    def get_object(name, size_multiplier, desc, rel_scale=0.65, offset=0, heading=None):
        nonlocal __size
        __size *= size_multiplier
        __size = round(__size)
        return TextObject(name, __size, desc, rel_scale=rel_scale, offset=offset, heading=heading)

    stage = Stage(
        [
            get_object("=", 1, "Assignment", heading='Assignment', offset=40),
            get_object(":=", 2, "Walrus", heading='Walrus'),
            get_object("lambda", 2, "Lambda", heading='Lambda', rel_scale=0.3),
            get_object("if-else", 2, "Conditional", heading='Conditional', rel_scale=0.4),
            get_object("or", 2, "Boolean OR", heading='Boolean OR'),
            get_object("and", 2, "Boolean AND", heading='Boolean AND', rel_scale=0.6),
            get_object("not", 2, "Boolean NOT", heading='Boolean NOT'),
            get_object("==", 2, "Equality", heading='Equality', offset=40),
            get_object("!=", 2, "Inequality", heading='Inequality'),
            get_object(">=", 2, "Greater Than Or Equal To", heading='Greater Than Or Equal To'),
            get_object(">", 2, "Greater Than", heading='Greater Than'),
            get_object("<=", 2, "Less Than Or Equal To", heading='Less Than Or Equal To'),
            get_object("<", 2, "Less Than", heading='Less Than'),
            get_object("is not", 2, "Identity Inequality", heading='Identity Inequality', rel_scale=0.4),
            get_object("is", 2, "Identity Equality", heading='Identity Equality'),
            get_object("not in", 2, "Membership (Absence)", heading='Membership (Absence)', rel_scale=0.4),
            get_object("in", 2, "Membership (Presence)", heading='Membership (Presence)'),
            get_object("|", 2, "Bitwise OR", heading='Bitwise OR'),
            get_object("^", 2.2, "Bitwise XOR", heading='Bitwise XOR', rel_scale=0.65),
            get_object("&", 2.2, "Bitwise AND", heading='Bitwise AND'),
            get_object(">>", 2.2, "Right Shift", heading='Right Shift'),
            get_object("<<", 2, "Left Shift", heading='Left Shift'),
            get_object("-", 2.2, "Subtraction", heading='Subtraction', offset=40),
            get_object("+", 2, "Addition", heading='Addition', rel_scale=0.74),
            get_object("%", 2.2, "Remainder", heading='Remainder'),
            get_object("//", 2, "Floor Division", heading='Floor Division'),
            get_object("/", 2, "Division", heading='Division'),
            get_object("@", 2, "Matrix Multiplication", heading='Matrix Multiplication', rel_scale=0.59),
            get_object("*", 2, "Multiplication", heading='Multiplication'),
            get_object("~", 2.2, "Bitwise NOT", heading='Bitwise NOT'),
            get_object("-x", 2, "Negative", heading='Negative', rel_scale=0.5),
            get_object("+x", 2, "Positive", heading='Positive', rel_scale=0.5),
            get_object("**", 2.2, "Exponentiation", heading='Exponentiation', rel_scale=0.5),
            get_object("await", 2.2, "Await", heading='Await', rel_scale=0.33),
            get_object("x.a", 2.2, "Attribute", heading='Attribute', rel_scale=0.4),
            get_object("x(...)", 2, "Call", heading='Call', rel_scale=0.35),
            get_object("x[::]", 2, "Slicing", heading='Slicing', rel_scale=0.45),
            get_object("x[i]", 2, "Subscription", heading='Subscription', rel_scale=0.45),
            get_object("{...}", 2.2, "Set Display", heading='Set Display', rel_scale=0.5),
            get_object("{k:v}", 2, "Dictionary Display", heading='Dictionary Display', rel_scale=0.45),
            get_object("[...]", 2, "List Display", heading='List Display', rel_scale=0.5),
            get_object("(...)", 2, "Parenthesis", heading='Parenthesis', rel_scale=0.5),

        ]
    )
    dt = 1
    running = True
    while running:

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                if e.key == pygame.K_r:
                    stage.reset()
                if e.key == pygame.K_UP:
                    stage.camera.change_zoom_by(stage.camera.scale)
                if e.key == pygame.K_DOWN:
                    stage.camera.change_zoom_by(-stage.camera.scale // 2)
            if e.type == pygame.QUIT:
                running = False
        # screen.fill(0)
        screen.blit(BG, [0, 0])
        stage.update(events, dt)
        stage.draw(screen)
        pygame.display.update()
        # fps = 1000 / clock.tick(60)
        try:
            dt = TARGET_FPS * clock.tick(0) * 0.001
        except ZeroDivisionError:
            dt = 1
        # dt = 1
        pygame.display.set_caption(str(clock.get_fps()))
        await asyncio.sleep(0)


if __name__ == '__main__':
    asyncio.run(main())
