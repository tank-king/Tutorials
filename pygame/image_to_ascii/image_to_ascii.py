import pygame

screen_width = 1000
screen_height = 800

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Image To ASCII')

clock = pygame.time.Clock()
FPS = 60

IMAGE = pygame.image.load('among us.jpg')
IMAGE = pygame.transform.scale_by(IMAGE, 0.05)

chars = "_.,-=+:;cba|?0123456789$W#@"

pygame.init()


def map_to_range(value, from_x, from_y, to_x, to_y):
    return value * (to_y - to_x) / (from_y - from_x)


def text(msg, size=15):
    return pygame.font.SysFont('consolas', size).render(msg, True, (255, 255, 255))


def image_to_ascii(image: pygame.Surface):
    w, h = text('A').get_size()
    surf = pygame.Surface(((image.get_width() - 1) * 15 + w, (image.get_height() - 1) * 15 + h))
    image.lock()
    for i in range(image.get_width()):
        for j in range(image.get_height()):
            r, g, b, _ = image.get_at([i, j])
            k = (r + g + b) / 3
            index = round(map_to_range(k, 0, 255, 0, len(chars) - 1))
            t = text(chars[index])
            surf.blit(t, (i * 15, j * 15))
            # pygame.display.update()
    image.unlock()
    return surf


def main_game():
    ascii_image = image_to_ascii(IMAGE)
    pygame.image.save(ascii_image, 'save.png')
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit()
        screen.fill((0, 0, 0))
        screen.blit(ascii_image, (0, 0))
        pygame.display.update()
        clock.tick(FPS)


main_game()
