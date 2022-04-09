import random
import pygame
from pygame.locals import *
import sys

BASIC_FONT_SIZE = 32
FPS = 60
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
CELL_SIZE = 40
CELLS_X = int(WINDOW_WIDTH / CELL_SIZE)
CELLS_Y = int(WINDOW_HEIGHT / CELL_SIZE)
PLAYER_SPEED = 3
PLAYER_JUMP_SPEED = 20
GRAVITY = 1
COOLDOWN = FPS/3

""" generate level template
with open('level1.txt', 'w') as f:
    for y in range(CELLS_Y):
        for x in range(CELLS_X):
            f.write('X')
        f.write('\n')
"""

class Bullet(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.x = player.x
        self.y = player.y - 10
        self.player = player
        self.direction = player.direction
        self.surf = pygame.Surface((10, 4))
        self.surf.fill((255,255,40))
        self.rect = self.surf.get_rect(center = (player.x, player.y) if self.direction == 1 else (player.x, player.y))
        bullets.append(self)
    
    def move(self):
        self.x += 10 * self.direction
        self.rect.center = (self.x if self.direction == 1 else self.x + self.rect.width, self.y)

class Player(pygame.sprite.Sprite):
    def __init__(self, player, x, y):
        super().__init__() 
        self.surf = pygame.Surface((40, 80))
        self.surf.fill((128,255,40))
        self.rect = self.surf.get_rect(center = (20, 80))

        self.player = player
        self.set_position(x, y)
        self.acc_x = 0
        self.acc_y = 0
        self.horizontal_speed = 0
        self.vertical_speed = 0
        self.direction = 1
        self.cooldown = 0
        self.cooldown_max = COOLDOWN

    def step(self):
        if self.cooldown > 0:
            self.cooldown -= 1

        self.horizontal_speed += self.acc_x

        if self.horizontal_speed > -.2 and self.horizontal_speed < .2:
            self.horizontal_speed = 0

        self.set_position(self.x + self.horizontal_speed, self.y)

        hits = pygame.sprite.spritecollide(self, walls, False)
        if hits:
            if self.horizontal_speed != 0:
                self.set_position(hits[0].rect.left - self.rect.width/2 if self.horizontal_speed > 0 else hits[0].rect.right + self.rect.width/2, self.y)
                self.horizontal_speed = 0
        else:
            self.horizontal_speed *= .5

        self.set_position(self.x, self.y + self.vertical_speed)

        hits = pygame.sprite.spritecollide(self, walls, False)
        if hits:
            if self.vertical_speed > 0:
                self.set_position(self.x, hits[0].rect.top - self.rect.height/2)
                self.vertical_speed = 0
                self.vertical_speed += self.acc_y
            elif self.vertical_speed < 0:
                self.set_position(self.x, hits[0].rect.bottom + self.rect.height/2)
                self.vertical_speed = 0

        else:
            self.vertical_speed += GRAVITY

        self.acc_x = 0
        self.acc_y = 0
        
        if self.y > WINDOW_HEIGHT:
            self.respawn()
    
    def respawn(self):
        sp = random.choice(spawnpoints)
        self.set_position(sp[0]*CELL_SIZE + CELL_SIZE/2, sp[1] * CELL_SIZE)

    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.rect.center = (self.x, self.y)

        

class Wall(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y):
        super().__init__()
        self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.surf.fill((255,0,40))
        self.rect = self.surf.get_rect(center = (grid_x * CELL_SIZE + CELL_SIZE/2, grid_y * CELL_SIZE + CELL_SIZE/2))

def main():
    global FPS_CLOCK, DISPLAY_SURFACE, BASIC_FONT, all_sprites, walls, p1, p2, bullets

    pygame.init()
    FPS_CLOCK = pygame.time.Clock()
    DISPLAY_SURFACE = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Hra')
    BASIC_FONT = pygame.font.Font('freesansbold.ttf', BASIC_FONT_SIZE)

    all_sprites = pygame.sprite.Group()
    p1 = Player(1, 0, 0)
    all_sprites.add(p1)
    p2 = Player(2, 0, 0)
    all_sprites.add(p2)
    walls = pygame.sprite.Group()
    bullets = []

    start_game('level1.txt')

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                terminate()
            
        keys = pygame.key.get_pressed()
        p1.acc_x = 0
        if keys[K_a]:
            p1.acc_x -= PLAYER_SPEED
            p1.direction = -1
        if keys[K_d]:
            p1.acc_x += PLAYER_SPEED
            p1.direction = 1
        if keys[K_w]:
            p1.acc_y = -PLAYER_JUMP_SPEED
        if keys[K_e]:
            if p1.cooldown == 0:
                create_bullet(p1)
                p1.cooldown = p1.cooldown_max
        
        mouse_keys = pygame.mouse.get_pressed(num_buttons=3)
        mouse_position = pygame.mouse.get_pos()
        p2.acc_x = 0
        if mouse_position[0] < p2.x - p2.rect.width/2:
            p2.acc_x -= PLAYER_SPEED
            p2.direction = -1
        elif mouse_position[0] > p2.x + p2.rect.width/2:
            p2.acc_x += PLAYER_SPEED
            p2.direction = 1
        if mouse_keys[2]:
            p2.acc_y = -PLAYER_JUMP_SPEED
        if mouse_keys[0]:
            if p2.cooldown == 0:
                create_bullet(p2)
                p2.cooldown = p2.cooldown_max

        p1.step()
        p2.step()

        for bull in bullets:
            bull.move()

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

def create_bullet(player):
    bullet = Bullet(player)
    all_sprites.add(bullet)

def start_game(filename):
    global spawnpoints
    spawnpoints = []
    with open(filename, 'r') as f:
        level_map = [line.strip() for line in f]
    for y in range(CELLS_Y):
        for x in range(CELLS_X):
            if level_map[y][x] == '#':
                wall = Wall(x, y)
                walls.add(wall)
                all_sprites.add(wall)
            elif level_map[y][x] == 'S':
                spawnpoints.append((x, y))
    random.shuffle(spawnpoints)
    p1.set_position(spawnpoints[0][0] * CELL_SIZE + CELL_SIZE/2, spawnpoints[0][1] * CELL_SIZE)
    p2.set_position(spawnpoints[1][0] * CELL_SIZE + CELL_SIZE/2, spawnpoints[1][1] * CELL_SIZE)              


def terminate():
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()