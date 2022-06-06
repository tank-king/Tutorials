"""
Please Read this before testing the program
This program assumes the display aspect ratio is 16:9 and has a resolution of 1920 X 1080 pixels
To stop all the windows, force stop from Pycharm (if you are using) or else press Ctrl + C in the terminal
Or you can individually exit all windows by pressing ESCAPE

Select a window and Press R to toggle between Resizable or not
"""

import os
import sys
from multiprocessing import Lock, Pipe, Process
from multiprocessing.connection import Connection
from random import randint

import pygame

pygame.init()


class Config:
    W = 200
    H = 200


def make_new_surface(send_conn: Connection, recv_conn: Connection, lck: Lock, x=None, y=None):
    """
    starts and runs a new process with a new window
    """
    w, h = Config.W, Config.H
    _clock = pygame.time.Clock()
    if x is None or y is None:
        pos_x, pos_y = randint(0, 500), randint(0, 500)
    else:
        pos_x, pos_y = x, y
    os.environ['SDL_VIDEO_WINDOW_POS'] = '%d, %d' % (pos_x, pos_y)
    no_frame = True
    screen = pygame.display.set_mode((Config.W, Config.H), pygame.NOFRAME)
    send_conn.send('loaded')
    images = [pygame.image.load(f'car/{i}.png') for i in range(24)]
    images = [pygame.transform.scale_by(i, 2.5) for i in images]
    i2 = [pygame.Surface((1920, 1080)) for _ in images]
    for i in range(len(i2)):
        i2[i].blit(images[i], images[i].get_rect(center=(1920 // 2, 1080 // 2)))
    images = [i for i in i2]
    font = pygame.font.SysFont('consolas', 25)
    text = font.render('Loading...', True, 'white')
    screen.blit(text, text.get_rect(center=screen.get_rect().center))
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                sys.exit(0)
            if e.type == pygame.WINDOWMOVED:
                print(e)
                pos_x, pos_y = e.x, e.y
            if e.type == pygame.WINDOWRESIZED:
                w, h = e.x, e.y
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    sys.exit(0)  # close this specific process
                if e.key == pygame.K_r:
                    no_frame = not no_frame
                    if no_frame:
                        screen = pygame.display.set_mode((w, h), pygame.NOFRAME)
                    else:
                        screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        lck.acquire()
        if recv_conn.poll():
            pass
            data = recv_conn.recv()
            while recv_conn.poll():
                data = recv_conn.recv()
            screen.fill('black')
            state = data
            img = images[int(state)]
            screen.blit(img, (0, 0), (pos_x, pos_y, w, h))
        else:
            pass
        lck.release()
        pygame.display.update()
        _clock.tick(60)


if __name__ == '__main__':

    pipes = []

    lock = Lock()

    info = pygame.display.Info()
    W, H = info.current_w, info.current_h

    processes = 0
    process_list = []

    clock = pygame.time.Clock()

    for r in range(1, 5 - 1):
        for c in range(1, 9 - 1):
            rr, ss = Pipe()
            pipes.append([rr, ss])
            process = Process(target=make_new_surface, args=(ss, rr, lock, c * (Config.W + 10) + 20, r * (Config.H + 10) + 15))
            process.daemon = True
            process.start()
            processes += 1
            process_list.append(process)


    def main_game():
        global processes, process_list
        import time
        t = time.time()
        count = 0
        ready = 0
        while True:
            if time.time() - t > 0.05:
                t = time.time()
                count += 1
            if count >= 24:
                count = 0
            data = str(count)
            process_list = [i for i in process_list if i.is_alive()]
            processes = len(process_list)
            if processes <= 0:
                sys.exit(0)
            lock.acquire()
            for i in pipes:
                recv, s = i
                if recv.poll():
                    s1 = recv.recv()
                    if s1 == 'loaded':
                        ready += 1
                if ready >= 21:
                    s.send(data)
                else:
                    pass
            lock.release()
            clock.tick(60)


    main_game()
