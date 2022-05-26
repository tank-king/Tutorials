"""
PLEASE READ THIS PART...

Code to demonstrate multiprocessing in python using a loading screen
This code is only for demonstrate a simple scenario
For complicated situations involving multiple child processes,
it is recommended to create a queue of such processes to manage them properly

This demo uses pygame to represent the loading screen,
but it can be extended to any graphics library

"""

import multiprocessing
import os
import time
from multiprocessing.connection import Connection

import pygame

pygame.init()


def load_directory(sender_connection: Connection, directory: str):
    """
    loads all images from a given directory and converts to ASCII
    sends a list of values [size, image's string format] to the connection object
    returns None
    """

    def image_to_ascii(_img: pygame.Surface):
        size = 10
        chars = "  _.,-=+:;cba|?0123456789$W#@"[::-1]
        font = pygame.font.SysFont('consolas', size)

        _img = pygame.transform.scale_by(_img, 0.25)

        def text(msg):
            return font.render(msg, True, (255, 255, 255))

        def map_to_range(value, from_x, from_y, to_x, to_y):
            return value * (to_y - to_x) / (from_y - from_x)

        w, h = text('a').get_size()
        x = 7
        surf = pygame.Surface(((_img.get_width() - 1) * x + w, (_img.get_height() - 1) * x + h))
        _img.lock()
        for j in range(_img.get_height()):
            for i in range(_img.get_width()):
                r, g, b, _ = _img.get_at([i, j])
                if (r, g, b) == (255, 255, 255):
                    continue
                k = (r + g + b) / 3
                index = round(map_to_range(k, 0, 255, 0, len(chars) - 1))
                t = text(chars[index])
                surf.blit(t, (i * x, j * x))
        _img.unlock()
        return surf

    files = os.listdir(directory)
    files.sort(key=lambda a: int(a.split('.')[0].split('_')[1]))  # this is used to sort the files alphabetically [format -> car_{num}.png]

    _c = 0
    for file in files:
        _c += 1
        img = pygame.image.load(os.path.join(directory, file))
        img = image_to_ascii(img)
        data_to_send = [
            img.get_size(),
            pygame.image.tostring(img, 'RGB')
        ]
        sender_connection.send(data_to_send)
        print(f'loaded image... {_c}')


def loading_screen(receiver_connection: Connection, item_c):
    """
    Loads and returns the loaded images while displaying a loading screen
    All loaded images are retrieved using the connection object
    """
    images = []
    _fps = 60
    _clock = pygame.time.Clock()
    _c = 0
    while True:
        for _e in pygame.event.get():
            if _e.type == pygame.QUIT:
                quit()
            if _e.type == pygame.KEYDOWN:
                if _e.key == pygame.K_ESCAPE:
                    quit()
        if receiver_connection.poll():
            img = receiver_connection.recv()
            img = pygame.image.fromstring(img[1], img[0], "RGB")
            img.set_colorkey((0, 0, 0))
            images.append(img)
            _c += 1
            if _c >= item_c:
                return images
        screen.fill((0, 0, 55))
        w, h = 1000, 800
        _w = w // (2 * item_c)
        pygame.draw.rect(screen, 'white', (w // 4, h // 2 - 50, w // 2, 100), 5)
        for i in range(_c):
            pygame.draw.rect(screen, 'white', (w // 4 + i * _w, h // 2 - 50, _w, 100))
        pygame.display.update()
        _clock.tick(_fps)


if __name__ == '__main__':
    screen = pygame.display.set_mode((1000, 800))
    pygame.display.set_caption('Loading Screen with MultiProcessing')
    fps = 60
    clock = pygame.time.Clock()
    # creating a Pipe object and assigning the receiver and sender
    receiver, sender = multiprocessing.Pipe(duplex=False)  # duplex=False means that the pipe is unidirectional

    process = multiprocessing.Process(target=load_directory, args=(sender, os.path.abspath('car'),))  # initializing new process
    process.daemon = True
    process.start()

    all_images = loading_screen(receiver, len(os.listdir(os.path.abspath('car'))))  # retrieve all images from the loading screen

    timer = time.time()
    c = 0

    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                quit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    quit()
        screen.fill((0, 0, 55))
        if time.time() - timer > 0.1:
            timer = time.time()
            c += 1
            c %= len(all_images)
        image = all_images[c]
        screen.blit(image, image.get_rect(center=(500, 400)))
        pygame.display.update()
        clock.tick(fps)
