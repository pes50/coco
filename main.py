from os import access
import pygame
from pygame.locals import *
import sys

BASIC_FONT_SIZE = 32
FPS = 60
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
CELL_SIZE = 40
PLAYER_SPEED = 3

class Player(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__() 
        self.surf = pygame.Surface((40, 80))
        self.surf.fill((128,255,40))
        self.rect = self.surf.get_rect(center = (20, 80))

        self.x = 0
        self.y = 0
        self.horizontal_speed = 0
        self.vertical_speed = 0
        self.acc_x = 0
        self.acc_y = 0
    
    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.rect.center = (self.x, self.y)

    def move(self):
        self.horizontal_speed += self.acc_x
        self.vertical_speed += self.acc_y

        if self.horizontal_speed > -.2 and self.horizontal_speed < .2:
            self.horizontal_speed = 0

        self.x += self.horizontal_speed
        self.y += self.vertical_speed
        self.rect.center = (self.x, self.y)

        self.acc_x = 0
        self.acc_y = 0
        self.horizontal_speed *= .5

        

class Wall(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.surf.fill((255,0,0))
        self.rect = self.surf.get_rect()

def main():
    global FPS_CLOCK, DISPLAY_SURFACE, BASIC_FONT

    pygame.init()
    FPS_CLOCK = pygame.time.Clock()
    DISPLAY_SURFACE = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Hra')
    BASIC_FONT = pygame.font.Font('freesansbold.ttf', BASIC_FONT_SIZE)

    p1 = Player(1)
    p2 = Player(2)
    wall = Wall()

    all_sprites = pygame.sprite.Group()
    all_sprites.add(p1)
    all_sprites.add(p2)
    all_sprites.add(wall)

    p1.set_position(100, 100)
    p2.set_position(200, 100)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                terminate()
            
        keys = pygame.key.get_pressed()
        p1.acc_x = 0
        if keys[K_a]:
            p1.acc_x -= PLAYER_SPEED
        if keys[K_d]:
            p1.acc_x += PLAYER_SPEED
        
        p2.acc_x = 0
        if keys[K_LEFT]:
            p2.acc_x -= PLAYER_SPEED
        if keys[K_RIGHT]:
            p2.acc_x += PLAYER_SPEED

        p1.move()
        p2.move()

        DISPLAY_SURFACE.fill((0,0,0))
        #Docasne
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(DISPLAY_SURFACE, (255,255,255), (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(DISPLAY_SURFACE,  (255,255,255), (0, y), (WINDOW_WIDTH, y))        
        
        for entity in all_sprites:
            DISPLAY_SURFACE.blit(entity.surf, entity.rect)

        pygame.display.update()
        FPS_CLOCK.tick(FPS)


def terminate():
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()