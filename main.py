import random
import pygame
from pygame.locals import *
import sys
import os.path

BASIC_FONT_SIZE = 32
BIG_FONT_SIZE = 128
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
SELECTED_COLOR = (240,240, 30)

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
        self.x = player.x + player.direction * 10
        self.y = player.y + 16
        self.player = player
        self.direction = player.direction
        self.surf = pygame.Surface((10, 4))
        self.surf.fill((255,255,40))
        self.rect = self.surf.get_rect(center = (self.x, self.y))
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
        self.surf = pygame.image.load(f"sprite/pickup{player}.png")
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
        self.surf = [None for i in range(3)]
        self.surf[0] = pygame.image.load(f"sprite/player{player}.png")
        self.surf[1] = pygame.image.load(f"sprite/player{player}walk1.png")
        self.surf[2] = pygame.image.load(f"sprite/player{player}walk2.png")

        self.rect = self.surf[0].get_rect(center = (20, 80))

        self.player = player
        self.set_position(x, y)
        self.acc_x = 0
        self.acc_y = 0
        self.acc_previous = 0
        self.acc_this_frame = 0
        self.walking_state = 0
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
        
        self.acc_this_frame = self.acc_x
        if self.acc_x != 0:
            self.acc_previous = self.acc_x
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
        self.surf = pygame.image.load(f"sprite/spike.png")
        self.rect = self.surf.get_rect(topleft = (grid_x * CELL_SIZE, grid_y * CELL_SIZE))

class Teleport(pygame.sprite.Sprite):
    def __init__(self, id, grid_x, grid_y):
        super().__init__()
        self.surf = pygame.image.load(f"sprite/teleport{id}.png")
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
    global FPS_CLOCK, DISPLAY_SURFACE, BASIC_FONT, BIG_FONT, p1, p2, pickup1, pickup2, acids, walls, bullets, s_pickups, players, teleports, spikes, lasers

    global background_level
    background_level = pygame.image.load("sprite/background-level.png")

    pygame.init()
    FPS_CLOCK = pygame.time.Clock()
    DISPLAY_SURFACE = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Hra')
    BASIC_FONT = pygame.font.Font('freesansbold.ttf', BASIC_FONT_SIZE)
    BIG_FONT = pygame.font.Font('freesansbold.ttf', BIG_FONT_SIZE)
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
    
    levels = first_screen()
    while True:
        start_level(f'level{random.randrange(1,levels+1)}.txt', teleports)
        winner = game_cycle()
        show_game_over_screen(winner)

def first_screen():
    levels = 0
    while os.path.exists(f'level{levels + 1}.txt'):
        levels += 1

    for lvl in range(levels):
        level = load_level(f'level{lvl + 1}.txt')
        if len(level) != CELLS_Y:
            level_error(f'Invalid level{lvl+1}.txt height. Expected {CELLS_Y}, got {len(level)}.')

        for row in level:
            if len(row) != CELLS_X:
                level_error(f'Invalid level{lvl+1}.txt width. Expected {CELLS_X}, got {len(row)}.')

        pick = 0
        spawn = 0
        for y in range(CELLS_Y):
            for x in range(CELLS_X):
                if level[y][x] == 'P':
                    pick += 1
                elif level[y][x] == 'S':
                    if y == 0:
                        spawn += 1
                    elif level[y-1][x] == 'X':
                        spawn += 1
                    else:
                        level_error(f'Spawnpoint in level{lvl+1}.txt is not safe for respawn.')

    background_menu = pygame.image.load("sprite/background-menu.png")
    DISPLAY_SURFACE.blit(background_menu, (0, 0))
    draw_text_outline("Game", WINDOW_WIDTH/2, 100, origin = "midtop", font = BIG_FONT)
    font_start = pygame.font.Font('freesansbold.ttf', 75)

    p1_img = pygame.image.load("sprite/player1.png")
    p1_img = pygame.transform.scale(p1_img, (CELL_SIZE*4, CELL_SIZE*4*2))
    p1_rect = p1_img.get_rect()
    p1_rect.bottomleft = (TEXT_OFFSET, WINDOW_HEIGHT - TEXT_OFFSET)
    DISPLAY_SURFACE.blit(p1_img, p1_rect)

    p2_img = pygame.image.load("sprite/player2.png")
    p2_img = pygame.transform.scale(p2_img, (CELL_SIZE*4, CELL_SIZE*4*2))
    p2_img = p2_img = pygame.transform.flip(p2_img, True, False)
    p2_rect = p2_img.get_rect()
    p2_rect.bottomright = (WINDOW_WIDTH - TEXT_OFFSET, WINDOW_HEIGHT - TEXT_OFFSET)
    DISPLAY_SURFACE.blit(p2_img, p2_rect)

    while True:
        font_rect = draw_text_outline("Start", WINDOW_WIDTH/2, 450, origin= "midtop", font = font_start)
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONUP:
                if  mouse_x > font_rect.x and mouse_x < font_rect.x + font_rect.width and mouse_y > font_rect.y and mouse_y < font_rect.y + font_rect.height:
                    return levels
            if event.type == QUIT:
                terminate()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()

        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x > font_rect.x and mouse_x < font_rect.x + font_rect.width and mouse_y > font_rect.y and mouse_y < font_rect.y + font_rect.height:
            draw_text_outline("Start", WINDOW_WIDTH/2, 450, origin= "midtop", font = font_start, color = SELECTED_COLOR)
        pygame.display.update()
        FPS_CLOCK.tick(FPS)

def level_error(error):
    background_error = pygame.image.load("sprite/background-menu.png")
    DISPLAY_SURFACE.blit(background_error, (0, 0))
    draw_text_outline("Oh no...", WINDOW_WIDTH/2, 100, origin = "midtop", font = BIG_FONT)
    font_start = pygame.font.Font('freesansbold.ttf', 75)

    p1_img = pygame.image.load("sprite/player1.png")
    p1_img = pygame.transform.scale(p1_img, (CELL_SIZE*4, CELL_SIZE*4*2))
    p1_rect = p1_img.get_rect()
    p1_rect.bottomleft = (TEXT_OFFSET, WINDOW_HEIGHT - TEXT_OFFSET)
    DISPLAY_SURFACE.blit(p1_img, p1_rect)

    p2_img = pygame.image.load("sprite/player2.png")
    p2_img = pygame.transform.scale(p2_img, (CELL_SIZE*4, CELL_SIZE*4*2))
    p2_img = p2_img = pygame.transform.flip(p2_img, True, False)
    p2_rect = p2_img.get_rect()
    p2_rect.bottomright = (WINDOW_WIDTH - TEXT_OFFSET, WINDOW_HEIGHT - TEXT_OFFSET)
    DISPLAY_SURFACE.blit(p2_img, p2_rect)

    while True:
        draw_text_outline(error, WINDOW_WIDTH/2, 300, origin= "midtop")
        font_rect = draw_text_outline("Ok", WINDOW_WIDTH/2, 450, origin= "midtop", font = font_start)
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONUP:
                if  mouse_x > font_rect.x and mouse_x < font_rect.x + font_rect.width and mouse_y > font_rect.y and mouse_y < font_rect.y + font_rect.height:
                    terminate()
            if event.type == QUIT:
                terminate()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()

        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x > font_rect.x and mouse_x < font_rect.x + font_rect.width and mouse_y > font_rect.y and mouse_y < font_rect.y + font_rect.height:
            draw_text_outline("Ok", WINDOW_WIDTH/2, 450, origin= "midtop", font = font_start, color = (240, 10, 10))
        pygame.display.update()
        FPS_CLOCK.tick(FPS)

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



        DISPLAY_SURFACE.blit(background_level, (0, 0)) 
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
            if player.acc_this_frame != 0:
                player.walking_state += 1
                if player.walking_state == FPS/2:
                    player.walking_state = 0
                surf = player.surf[1 if player.walking_state < FPS/4 else 2].copy()
            else:
                surf = player.surf[0].copy()
            if player.acc_previous == -PLAYER_SPEED:
                surf = pygame.transform.flip(surf, True, False)
            DISPLAY_SURFACE.blit(surf, player.rect)

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
    draw_text_outline(p1.score, TEXT_OFFSET, TEXT_OFFSET, color = P1_COLOR, origin="topleft")
    draw_text_outline(p2.score, WINDOW_WIDTH - TEXT_OFFSET, TEXT_OFFSET, color = P2_COLOR, origin="topright")

def draw_text_outline(text, x, y, origin = "topleft", color = TEXT_COLOR, font = None):
    text = str(text)
    if font == None:
        font = BASIC_FONT

    text_surf = font.render(text, True, TEXT_OUTLINE)
    text_rect = text_surf.get_rect()

    if origin == "center":
        text_rect.center = (x, y)
    elif origin == "midbottom":
        text_rect.midbottom = (x, y)
    elif origin == "topright":
        text_rect.topright = (x, y)
    elif origin == "topleft":
        text_rect.topleft = (x, y)
    elif origin == "midtop":
        text_rect.midtop = (x, y)

    xx = text_rect.x
    yy = text_rect.y

    DISPLAY_SURFACE.blit(text_surf, (xx-1, yy-1))
    DISPLAY_SURFACE.blit(text_surf, (xx+1, yy+1))
    DISPLAY_SURFACE.blit(text_surf, (xx-1, yy+1))
    DISPLAY_SURFACE.blit(text_surf, (xx+1, yy-1))

    text_surf = font.render(text, True, color)
    DISPLAY_SURFACE.blit(text_surf,text_rect)
    return text_rect

def show_game_over_screen(winner):
    dark = pygame.Surface(DISPLAY_SURFACE.get_size()).convert_alpha()
    dark.fill((0, 0, 0, 70))
    DISPLAY_SURFACE.blit(dark, (0, 0))
    draw_text_outline("Draw!" if winner == None else "Player 1" if winner == 1 else "Player 2", WINDOW_WIDTH/2, WINDOW_HEIGHT/2, "midbottom")

    if winner != None:
        draw_text_outline("is the WINNER!", WINDOW_WIDTH / 2, WINDOW_HEIGHT/2 + TEXT_OFFSET, "midtop")

    wait_for_key_released()

def load_level(filename):
    with open(filename, 'r') as f:
        level_map = [line.strip() for line in f]

    for y in range(CELLS_Y):
        level_map[y] = list(level_map[y])
    return level_map

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
    level_map = load_level(filename)

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
                elif level_map[y][x] == '/':
                    wall = Wall(x, y, True)
                    walls.add(wall)
                    acid = Acid(x, y, None)
                    acids.add(acid)
                    tolerance = acid.tolerance
                    while level_map[y][x + 1] == '/':
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

def wait_for_key_released():
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            if event.type == KEYUP:
                if event.key == K_ESCAPE:
                    terminate()
                return
        pygame.display.update()
        FPS_CLOCK.tick(FPS)

if __name__ == '__main__':
    main()