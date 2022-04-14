from csv import Dialect
import random
from tkinter.messagebox import NO
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
MULTIPLIER_ADD = 1.5
MAX_MULTIPLIER = CELL_SIZE*3
ACID_HEIGHT = 0.65
ACID_NEUTRAL_COLOR = (40,40,255)
P1_COLOR = (128,255,40)
P2_COLOR = (255,128,40)

""" Generate level template
with open('level1.txt', 'w') as f:
    for y in range(CELLS_Y):
        for x in range(CELLS_X):
            f.write('X')
        f.write('\n')
"""

class Acid(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y, tolerance = -1):
        super().__init__()
        self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE*(1-ACID_HEIGHT)))
        self.tolerance = tolerance
        if self.tolerance == -1:
            self.tolerance = random.choice((None, p1, p2))
        if self.tolerance == None:
            self.surf.fill(ACID_NEUTRAL_COLOR)
        else:
            self.surf.fill(P1_COLOR if self.tolerance == p1 else P2_COLOR)
        self.rect = self.surf.get_rect(topleft = (grid_x * CELL_SIZE, grid_y * CELL_SIZE))


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
        hits_wall = pygame.sprite.spritecollide(self, walls, False)
        hits_player = pygame.sprite.spritecollide(self, players, False)
        if hits_player:
            for p in hits_player:
                if p != self.player:
                    p.multiplier = min(p.multiplier*MULTIPLIER_ADD, MAX_MULTIPLIER)
                    if p.horizontal_speed != 0 and p.horizontal_speed/abs(p.horizontal_speed) == self.direction:
                        p.horizontal_speed += self.direction * p.multiplier
                    else:
                        p.horizontal_speed = self.direction * p.multiplier 
                    
                    if p.vertical_speed != 0 and p.vertical_speed != GRAVITY:
                        p.vertical_speed = 0
                    self.kill()
                    bullets.remove(self)
                    return

        if hits_wall or self.x < -CELL_SIZE or self.x > WINDOW_WIDTH + CELL_SIZE:
            self.kill()
            bullets.remove(self)

        

class Player(pygame.sprite.Sprite):
    def __init__(self, player, x, y):
        super().__init__() 
        self.surf = pygame.Surface((40, 80))
        self.surf.fill(P1_COLOR if player == 1 else P2_COLOR)
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
        self.multiplier = 1

    def create_bullet(self):
        Bullet(self)

    def step(self):
        previous_horizontal_speed = 0
        previous_vertical_speed = 0

        if self.cooldown > 0:
            self.cooldown -= 1

        self.horizontal_speed += self.acc_x

        if self.horizontal_speed > -.2 and self.horizontal_speed < .2:
            self.horizontal_speed = 0

        # Horizontal movement
        self.set_position(self.x + self.horizontal_speed, self.y)
        hits = pygame.sprite.spritecollide(self, walls, False)
        if hits:
            if self.horizontal_speed != 0:
                self.set_position(hits[0].rect.left - self.rect.width/2 if self.horizontal_speed > 0 else hits[0].rect.right + self.rect.width/2, self.y)
                previous_horizontal_speed = self.horizontal_speed
                self.horizontal_speed = 0
        else:
            self.horizontal_speed *= .5

        while pygame.sprite.spritecollide(self, walls, False):
                self.set_position(self.x - previous_horizontal_speed/abs(previous_horizontal_speed), self.y)

        # Vertical movement
        self.set_position(self.x, self.y + self.vertical_speed)
        hits = pygame.sprite.spritecollide(self, walls, False)
        if hits:
            if self.vertical_speed > 0:
                self.set_position(self.x, hits[0].rect.top - self.rect.height/2)
                previous_vertical_speed = self.vertical_speed
                self.vertical_speed = 0
                self.vertical_speed += self.acc_y
            elif self.vertical_speed < 0:
                self.set_position(self.x, hits[0].rect.bottom + self.rect.height/2)
                previous_vertical_speed = self.vertical_speed
                self.vertical_speed = 0
        else:
            self.vertical_speed += GRAVITY

        while pygame.sprite.spritecollide(self, walls, False):
                self.set_position(self.x, self.y - previous_vertical_speed/abs(previous_vertical_speed))

        hits_acid = pygame.sprite.spritecollide(self, acids, False)
        if hits_acid:
            if hits_acid[0].tolerance != self:
                self.respawn()

        self.acc_x = 0
        self.acc_y = 0
        
        if self.y > WINDOW_HEIGHT:
            self.respawn()
    
    def respawn(self):
        sp = random.choice(spawnpoints)
        self.set_position(sp[0]*CELL_SIZE + CELL_SIZE/2, sp[1] * CELL_SIZE)
        self.multiplier = 1

    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.rect.center = (self.x, self.y)

        

class Wall(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y, acid = False):
        super().__init__()
        if acid:
            self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE*ACID_HEIGHT))
            self.surf.fill((255,0,40))
            self.rect = self.surf.get_rect(topleft = (grid_x * CELL_SIZE, grid_y * CELL_SIZE + CELL_SIZE*(1 - ACID_HEIGHT))) 
        else:
            self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
            self.surf.fill((255,0,40))
            self.rect = self.surf.get_rect(topleft = (grid_x * CELL_SIZE, grid_y * CELL_SIZE))

def main():
    global FPS_CLOCK, DISPLAY_SURFACE, BASIC_FONT, p1, p2, p1_kills, p2_kills, acids, walls, bullets, players

    pygame.init()
    FPS_CLOCK = pygame.time.Clock()
    DISPLAY_SURFACE = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Hra')
    BASIC_FONT = pygame.font.Font('freesansbold.ttf', BASIC_FONT_SIZE)
    # Sprite groups
    acids = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    players = pygame.sprite.Group()
    p1 = Player(1, 0, 0)
    players.add(p1)
    p2 = Player(2, 0, 0)
    players.add(p2)
    bullets = []

    start_game('level1.txt')

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                terminate()
        # Get input
        keys = pygame.key.get_pressed()
        # Player 1 move
        p1.acc_x = 0
        if keys[K_a]:
            p1.acc_x -= PLAYER_SPEED
            p1.direction = -1
        if keys[K_d]:
            p1.acc_x += PLAYER_SPEED
            p1.direction = 1
        if keys[K_w]:
            p1.acc_y = -PLAYER_JUMP_SPEED
        p1.step()
        # Player 2 move
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
        p2.step()
        # Players attacks
        if keys[K_e]:
            if p1.cooldown == 0:
                p1.create_bullet()
                p1.cooldown = p1.cooldown_max     
        if mouse_keys[0]:
            if p2.cooldown == 0:
                p2.create_bullet()
                p2.cooldown = p2.cooldown_max

        for bull in bullets:
            bull.move()

        DISPLAY_SURFACE.fill((0,0,0))
        #Temp
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(DISPLAY_SURFACE, (255,255,255), (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(DISPLAY_SURFACE,  (255,255,255), (0, y), (WINDOW_WIDTH, y))        
        
        for wall in walls:
            DISPLAY_SURFACE.blit(wall.surf, wall.rect)

        for player in players:
            DISPLAY_SURFACE.blit(player.surf, player.rect)

        for acid in acids:
            DISPLAY_SURFACE.blit(acid.surf, acid.rect)        

        for bullet in bullets:
            DISPLAY_SURFACE.blit(bullet.surf, bullet.rect)

        pygame.display.update()
        FPS_CLOCK.tick(FPS)

def start_game(filename):
    global spawnpoints
    spawnpoints = []
    with open(filename, 'r') as f:
        level_map = [line.strip() for line in f]
    for y in range(CELLS_Y):
        level_map[y] = list(level_map[y])
        for x in range(CELLS_X):
            if level_map[y][x] == '#':
                wall = Wall(x, y)
                walls.add(wall)
            elif level_map[y][x] == '_':
                wall = Wall(x, y, True)
                walls.add(wall)
                acid = Acid(x, y)
                acids.add(acid)
                tolerance = acid.tolerance
                while level_map[y][x + 1] == '_':
                    x += 1
                    level_map[y][x] = '-'
                    wall = Wall(x, y, True)
                    walls.add(wall)
                    acid = Acid(x, y, tolerance)
                    acids.add(acid)
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