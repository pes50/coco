import random
from unittest.mock import DEFAULT
import pygame
from pygame.locals import *
import sys
import os.path

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
NEUTRAL_COLOR = (40,255,40)
P1_COLOR = (255,40,40)
P2_COLOR = (40,40,255)
TEXT_OFFSET = 5
TARGET_SCORE = 10
TEXT_COLOR = (255, 255, 255)
TEXT_OUTLINE = (0, 0, 0)

class Acid(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y, tolerance = -1):
        super().__init__()
        self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE*(1-ACID_HEIGHT)))
        self.tolerance = tolerance
        if self.tolerance == -1:
            self.tolerance = random.choice((None, p1, p2))
        if self.tolerance == None:
            self.surf.fill(NEUTRAL_COLOR)
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

class Laser(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y, tolerance = -1):
        super().__init__()
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.surf = pygame.Surface((CELL_SIZE/2, CELL_SIZE))
        self.set_tolerance(tolerance)
        self.cooldown = -FPS*5
        self.on = True
        self.start = False
        self.parts = []

    def set_tolerance(self, tolerance = -1):
        if tolerance == -1:
            self.tolerance = random.choice((None, p1, p2))
        else:
            self.tolerance = tolerance
        if self.tolerance == None:
            self.surf.fill(NEUTRAL_COLOR)
        else:
            self.surf.fill(P1_COLOR if self.tolerance == p1 else P2_COLOR)
        self.rect = self.surf.get_rect(topleft = (self.grid_x * CELL_SIZE + CELL_SIZE/4, self.grid_y * CELL_SIZE))

    def step(self):
        self.cooldown += 1
        if self.cooldown == 0:
            self.cooldown = -FPS*5
            if self.on:
                self.on = False
            else:
                self.on = True
                if self.start:
                    self.set_tolerance()

    

class Pickup(pygame.sprite.Sprite):
    def __init__(self, player, x, y):
        super().__init__() 
        self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.surf.fill(P1_COLOR if player == 1 else P2_COLOR)
        self.rect = self.surf.get_rect(topleft = (CELL_SIZE, CELL_SIZE))
    
        self.player = player
        self.x = x
        self.y = y

    def check_collision(self, pickups):
        player_collisions = pygame.sprite.spritecollide(self, players, False)
        for p in player_collisions:
            if p.player == self.player:
                pos = pickups.pop()
                pickups.insert(0, pos)
                if p.player == 1:
                    if pos[0]*CELL_SIZE == pickup2.x and pos[1]*CELL_SIZE == pickup2.y:
                        pos = pickups.pop()
                        pickups.insert(0, pos)
                    p1.score += 1
                else:
                    if pos[0]*CELL_SIZE == pickup1.x and pos[1]*CELL_SIZE == pickup1.y:
                        pos = pickups.pop()
                        pickups.insert(0, pos)
                    p2.score += 1
                self.set_position(pos[0]*CELL_SIZE, pos[1]*CELL_SIZE)


    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.rect.topleft = (self.x, self.y)       

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
        self.score = 0

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
        # Acid collision
        hits = pygame.sprite.spritecollide(self, acids, False)
        if hits:
            if hits[0].tolerance != self:
                self.respawn()
        # Laser collision
        hits = pygame.sprite.spritecollide(self, lasers, False)
        if hits:
            if hits[0].on:
                if hits[0].tolerance != self:
                    self.respawn()
        # Spike collision
        if pygame.sprite.spritecollide(self, spikes, False):
            self.respawn()
        
        self.acc_x = 0
        self.acc_y = 0
        
        if self.y > WINDOW_HEIGHT:
            self.respawn()
    
    def respawn(self):
        sp = random.choice(spawnpoints)
        self.set_position(sp[0]*CELL_SIZE + CELL_SIZE/2, sp[1] * CELL_SIZE)
        self.multiplier = 1
        if self.player == 1:
            p2.score += 1
        else:
            p1.score += 1
            pygame.mouse.set_pos((self.x,self.y))

    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.rect.center = (self.x, self.y)

class Spike(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y):
        super().__init__()
        self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE/2))
        self.surf.fill((255, 128, 128))
        self.rect = self.surf.get_rect(topleft = (grid_x * CELL_SIZE, grid_y * CELL_SIZE))

class Teleport(pygame.sprite.Sprite):
    def __init__(self, id, grid_x, grid_y):
        super().__init__()
        self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.surf.fill((int(id)*20,int(id)*20,int(id)*15))
        self.rect = self.surf.get_rect(topleft = (grid_x * CELL_SIZE, grid_y * CELL_SIZE))
        
        self.id = int(id)
        teleports.add(self)
        self.x = grid_x * CELL_SIZE
        self.y = grid_y * CELL_SIZE
        self.cooldown = 0

    def check_collision(self, teleports):
        self.cooldown += 1
        if self.cooldown > 0:
            player_collisions = pygame.sprite.spritecollide(self, players, False)
            for p in player_collisions:
                options = []
                for option in teleports:
                    if option.id == self.id:
                        if option != self:
                            options.append(option)
                if len(options) > 0:
                    port = random.choice(options)
                    p.set_position(port.x + CELL_SIZE/2, port.y)
                    if p.player == 2:
                        pygame.mouse.set_pos((p.x, p.y))
                    port.cooldown = -FPS
                    self.cooldown = -FPS

class Wall(pygame.sprite.Sprite):
    def __init__(self, grid_x, grid_y, acid = False):
        super().__init__()
        if acid:
            sprite = pygame.image.load("sprite/wall.png")
            self.surf = pygame.Surface((CELL_SIZE, CELL_SIZE*ACID_HEIGHT))
            self.surf.blit(sprite, (0, -(1-ACID_HEIGHT)*CELL_SIZE))
            self.rect = self.surf.get_rect(topleft = (grid_x * CELL_SIZE, grid_y * CELL_SIZE + CELL_SIZE*(1 - ACID_HEIGHT))) 
        else:
            self.surf = pygame.image.load("sprite/wall.png")
            self.rect = self.surf.get_rect(topleft = (grid_x * CELL_SIZE, grid_y * CELL_SIZE))

def main():
    global FPS_CLOCK, DISPLAY_SURFACE, BASIC_FONT, p1, p2, pickup1, pickup2, acids, walls, bullets, s_pickups, players, teleports, spikes, lasers

    pygame.init()
    FPS_CLOCK = pygame.time.Clock()
    DISPLAY_SURFACE = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Hra')
    BASIC_FONT = pygame.font.Font('freesansbold.ttf', BASIC_FONT_SIZE)
    # Sprite groups
    acids = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    players = pygame.sprite.Group()
    s_pickups = pygame.sprite.Group()
    teleports = pygame.sprite.Group()
    spikes = pygame.sprite.Group()
    lasers = pygame.sprite.Group()
    p1 = Player(1, 0, 0)
    players.add(p1)
    pickup1 = Pickup(1, 0, 0)
    s_pickups.add(pickup1)
    p2 = Player(2, 0, 0)
    players.add(p2)
    pickup2 = Pickup(2, 0, 0)
    s_pickups.add(pickup2)
    bullets = []

    levels = 0
    while os.path.exists('level' + str(levels + 1) + '.txt'):
        levels += 1
    while True:
        start_level(f'level{random.randrange(1,levels+1)}.txt', teleports)
        winner = game_cycle()
        show_game_over_screen(winner)

def game_cycle():
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

        pickup1.check_collision(pickups)
        pickup2.check_collision(pickups)

        for port in teleports:
            port.check_collision(teleports)

        for laser in lasers:
            laser.step()
            if laser.start:
                for l in laser.parts:
                    l.set_tolerance(laser.tolerance)



        DISPLAY_SURFACE.fill((255,255,255))
        #Temp
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            pygame.draw.line(DISPLAY_SURFACE, (0,0,0), (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            pygame.draw.line(DISPLAY_SURFACE,  (0,0,0), (0, y), (WINDOW_WIDTH, y))        
        # Draw walls
        for wall in walls:
            DISPLAY_SURFACE.blit(wall.surf, wall.rect)
        # Draw spikes
        for spike in spikes:
            DISPLAY_SURFACE.blit(spike.surf, spike.rect)
        # Draw lasers
        for laser in lasers:
            if laser.on:
                DISPLAY_SURFACE.blit(laser.surf, laser.rect)
        # Draw teleports
        for teleport in teleports:
            DISPLAY_SURFACE.blit(teleport.surf, teleport.rect)
        # Draw players
        for player in players:
            DISPLAY_SURFACE.blit(player.surf, player.rect)
        # Draw acid
        for acid in acids:
            DISPLAY_SURFACE.blit(acid.surf, acid.rect)        
        # Draw bullets
        for bullet in bullets:
            DISPLAY_SURFACE.blit(bullet.surf, bullet.rect)
        # Draw pickups
        for pick in s_pickups:
            DISPLAY_SURFACE.blit(pick.surf, pick.rect)

        draw_score()

        pygame.display.update()
        if p1.score == TARGET_SCORE and p2.score == TARGET_SCORE:
            return None
        if p1.score == TARGET_SCORE:
            return 1
        if p2.score == TARGET_SCORE:
            return 2
        FPS_CLOCK.tick(FPS)

def draw_score():
    draw_text_outline(p1.score, TEXT_OFFSET, TEXT_OFFSET)
    score_width = BASIC_FONT.render(str(p2.score), True, TEXT_COLOR).get_width()
    draw_text_outline(p2.score, WINDOW_WIDTH - score_width - TEXT_OFFSET, TEXT_OFFSET)

def draw_text_outline(text, x, y, origin = "topleft"):
    text = str(text)
    text_rect = BASIC_FONT.render(text, True, TEXT_OUTLINE)
    if origin == "center":
        x += text_rect.get_width()/2
        y += text_rect.get_height()/2
    elif origin == "midbottom":
        x -= text_rect.get_width()/2
        y -= text_rect.get_height()
    elif origin == "midtop":
        x -= text_rect.get_width()/2

    DISPLAY_SURFACE.blit(text_rect, (x-1, y-1))
    DISPLAY_SURFACE.blit(text_rect, (x+1, y+1))
    DISPLAY_SURFACE.blit(text_rect, (x-1, y+1))
    DISPLAY_SURFACE.blit(text_rect, (x+1, y-1))
    text_rect = BASIC_FONT.render(text, True, TEXT_COLOR)
    DISPLAY_SURFACE.blit(text_rect,(x, y))

def show_game_over_screen(winner):
    dark = pygame.Surface(DISPLAY_SURFACE.get_size()).convert_alpha()
    dark.fill((0, 0, 0, 70))
    DISPLAY_SURFACE.blit(dark, (0, 0))
    draw_text_outline("Draw!" if winner == None else "Player 1" if winner == 1 else "Player 2", WINDOW_WIDTH/2, WINDOW_HEIGHT/2, "midbottom")

    if winner != None:
        draw_text_outline("is the WINNER!", WINDOW_WIDTH / 2, WINDOW_HEIGHT/2 + TEXT_OFFSET, "midtop")

    wait_for_key_pressed()

def start_level(filename, teleports):
    # Cleanup
    p1.score = 0
    p2.score = 0
    for acid in acids:
        acid.kill()
        acids.remove(acid)
    for laser in lasers:
        laser.kill()
        lasers.remove(laser)
    for spike in spikes:
        spike.kill()
        spikes.remove(spike)
    for teleport in teleports:
        teleport.kill()
        teleports.remove(teleport)
    for wall in walls:
        wall.kill()
        walls.remove(wall)
    global pickups, spawnpoints
    pickups = []
    spawnpoints = []
    teleports = [[] for i in range(10)]
    with open(filename, 'r') as f:
        level_map = [line.strip() for line in f]

    for y in range(CELLS_Y):
        level_map[y] = list(level_map[y])
    for y in range(CELLS_Y):
        for x in range(CELLS_X):
            if level_map[y][x].isnumeric():
                Teleport(level_map[y][x], x, y)
            else:
                if level_map[y][x] == '#':
                    wall = Wall(x, y)
                    walls.add(wall)
                elif level_map[y][x] == '|':
                    laser = Laser(x,y)
                    lasers.add(laser)
                    laser.start = True
                    tolerance = laser.tolerance 
                    yy = y
                    while level_map[yy + 1][x] == '|':
                        yy += 1
                        level_map[yy][x] = '-'
                        l = Laser(x, yy, tolerance)
                        lasers.add(l)
                        laser.parts.append(l)
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
                elif level_map[y][x] == 'P':
                    pickups.append((x, y))
                elif level_map[y][x] == 'T':
                    spike = Spike(x, y)
                    spikes.add(spike)
                elif level_map[y][x] == 'S':
                    spawnpoints.append((x, y))

    # Pickups
    random.shuffle(pickups)
    pick1 = pickups.pop()
    pick2 = pickups.pop()
    pickup1.set_position(pick1[0] * CELL_SIZE,  pick1[1] * CELL_SIZE)
    pickup2.set_position(pick2[0] * CELL_SIZE, pick2[1] * CELL_SIZE)
    pickups = [pick2] + [pick1] + pickups
    # Spawnpoints
    random.shuffle(spawnpoints)
    p1.set_position(spawnpoints[0][0] * CELL_SIZE + CELL_SIZE/2, spawnpoints[0][1] * CELL_SIZE)
    p2.set_position(spawnpoints[1][0] * CELL_SIZE + CELL_SIZE/2, spawnpoints[1][1] * CELL_SIZE)
    pygame.mouse.set_pos((p2.x,p2.y))

def terminate():
    pygame.quit()
    sys.exit()

def wait_for_key_pressed():
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                return
        pygame.display.update()
        FPS_CLOCK.tick(FPS)

if __name__ == '__main__':
    main()