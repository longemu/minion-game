##TODO LIST
# AUDIO
    # Background Music - DONE
    # Hit Music - DONE
    # Banana Collecting Music - DONE
    # Died Music
    # Won Music
# LOOKS
    # Fire Makeover - DONE
    # Banana Makeover - DONE
    # Hit Looks - DONE
    # Scoreboard Makeover
    # Won Screen
    # Died Screen
# FEATURES
    # Coding Logic for Levels
    # Level 1
    # Level 2
    # Level 3

import os
import random   
import math
import pygame
from os import listdir
from os.path import isfile,join
pygame.init()

pygame.display.set_caption("Minion-Game")

BG_COLOR = (255,255,255)
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
block_size = 96

window = pygame.display.set_mode((WIDTH,HEIGHT))

audio_path = os.path.join("assets", "audio")

# Initialize the mixer with appropriate settings
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Load the background music and hit sound
background_music = os.path.join(audio_path, 'happy_with_lyrics.wav')
hit_sound = pygame.mixer.Sound(os.path.join(audio_path, 'hit.wav'))
banana_collect_sound = pygame.mixer.Sound(os.path.join(audio_path, 'banana_collect.wav'))

# Play the background music
pygame.mixer.music.load(background_music)
pygame.mixer.music.play(-1)  # Loop the music indefinitely



def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {} ##the dictionary

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

######################################################################PLAYER CLASS

class Player(pygame.sprite.Sprite):

    COLOR = (255,0,0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("characters","minion", 32, 32, True)
    ANIMATION_DELAY = 3
    HIT_COUNTDOWN = 60
    #hitted = pygame.mixer.Sound('hit.wav')

    def __init__(self, x, y, width, height, hit_sound):
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.lives = 3
        self.hit_cooldown = 0
        self.score = 0
        self.hit_sound = hit_sound
    
    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0


    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def been_hit(self):
        if self.hit_cooldown == 0:
            self.hit = True
            self.hit_count = 0
            self.lives -= 1
            self.hit_cooldown = self.HIT_COUNTDOWN
            self.hit_sound.play()
    
    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0
    
    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1,(self.fall_count / fps) * self.GRAVITY)#################################### disabled gravity
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False

        if self.hit_cooldown > 0:  # Decrement cooldown timer
            self.hit_cooldown -= 1

        self.update_sprite()

        self.fall_count += 1

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"

        if self.hit:
            sprite_sheet = "hit"
        if self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"
    

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites) ## Confusing... trace logic later
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

    

######################################################################OBJECT CLASS

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width,height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, window, offset_x):
        window.blit(self.image, (self.rect.x - offset_x, self.rect.y))

######################################################################BLOCK CLASS

class Block(Object):
    def __init__(self,x,y,size):
        super().__init__(x,y,size,size)
        block = get_block(size)
        self.image.blit(block, (0,0))
        self.mask = pygame.mask.from_surface(self.image)


######################################################################Banana CLASS

class Banana(Object):

    ANIMATION_DELAY = 3
    SCORE_COOLDOWN = 60

    def __init__(self, x, y, width, height, collect_sound):
        super().__init__(x, y, width, height, "banana")
        self.banana = load_sprite_sheets("items", "points", width, height)
        self.animation_count = 0
        self.image = self.banana["Bananas"][0]  # Ensure this is a list of sprites
        self.mask = pygame.mask.from_surface(self.image)
        self.score_cooldown = 0
        self.collect_sound = collect_sound

    def loop(self):
        sprites = self.banana["Bananas"]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

        if self.score_cooldown > 0:  # Decrement cooldown timer
            self.score_cooldown -= 1

    def collect(self, player):
        if self.score_cooldown == 0:
            print("COLLECTING")
            self.collect_sound.play()
            player.score += 1  # Increase player's score
            #self.kill()  # Remove the banana from the game
            print("BANANA REMOVED")
            self.score_cooldown = self.SCORE_COOLDOWN

        

######################################################################FIRE CLASS

class Fire(Object):

    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("traps","fire", width, height)
        self.animation_count = 0
        self.animation_name = "on"
        self.image = self.fire[self.animation_name][0]
        self.mask = pygame.mask.from_surface(self.image)




    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

######################################################################FUNCTIONS

def get_background(name):
    image = pygame.image.load(join("assets", "background", name))
    _,_, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH//width + 1):
        for j in range(HEIGHT//height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles,image

def draw_lives(window, lives):
    font = pygame.font.SysFont('Century Gothic', 30)
    lives_text = font.render(f'Lives: {lives}', True, (0, 0, 0))
    window.blit(lives_text, (10, 10))

def draw_score(window, score):
    font = pygame.font.SysFont('Century Gothic', 30)
    lives_text = font.render(f'Bananas: {score}', True, (0, 0, 0))
    window.blit(lives_text, (10, 50))

def draw(window,background, bg_image,player,objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)
    draw_lives(window, player.lives)
    draw_score(window, player.score)

    pygame.display.update()

def handle_vertical_collision(player,objects,dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy> 0:
                player.rect.bottom = obj.rect.top
                player.landed()
                collided_objects.append(obj)
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
                collided_objects.append(obj)

    return collided_objects

def collision(player,objects,dx):
    player.move(dx,0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player,obj):
            collided_object = obj
            break
    
    player.move(-dx,0)
    player.update()
    return collided_object

def handle_move(player,objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collided_left = collision(player,objects,-PLAYER_VEL *2)
    collided_right = collision(player,objects,PLAYER_VEL *2)

    if keys[pygame.K_LEFT] and not collided_left:
        player.move_left(PLAYER_VEL)
    elif keys[pygame.K_RIGHT] and not collided_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player,objects,player.y_vel)
    to_check = [collided_left,collided_right,*vertical_collide]
    objects_to_remove = []

    for obj in to_check:
        if obj and obj.name == "fire":
            player.been_hit()  
        elif obj and obj.name == "banana":
            obj.collect(player)
            objects_to_remove.append(obj)
            print("COLLECTED")
    
    for obj in objects_to_remove:
        if obj in objects:
            objects.remove(obj)

def get_block(size):
    path = join("assets", "terrain", "minion_block.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size,size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96,0,size,size)
    surface.blit(image, (0,0), rect)
    return pygame.transform.scale2x(surface)

def died_screen(window, score):
    font = pygame.font.SysFont('Century Gothic', 50)
    game_over_text = font.render('You Died!', True, (255, 0, 0))
    score_text = font.render(f'Bananas: {score}', True, (255, 0, 0))
    restart_text = font.render('Press R to Restart or Q to Quit', True, (255, 0, 0))

    window.fill((0, 0, 0))
    window.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
    window.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    window.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 100))
    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                    main(window)
                elif event.key == pygame.K_q:
                    pygame.quit()
                    quit()
def won_screen(window, score):
    font = pygame.font.SysFont('Century Gothic', 50)
    game_over_text = font.render('You Won!', True, (255, 255, 0))
    score_text = font.render(f'Bananas: {score}', True, (255, 255, 0))
    restart_text = font.render('Press R to Restart or Q to Quit', True, (255, 255, 0))

    window.fill((0, 0, 0))
    window.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
    window.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    window.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 100))
    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                    main(window)
                elif event.key == pygame.K_q:
                    pygame.quit()
                    quit()

def level_transition(window, score,):
    font = pygame.font.SysFont('Century Gothic', 50)
    game_over_text = font.render('Level Completed!', True, (255, 255, 0))
    score_text = font.render(f'Bananas: {score}', True, (255, 255, 0))
    restart_text = font.render('Press C to continue or Q to Quit', True, (255, 255, 0))

    window.fill((0, 0, 0))
    window.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
    window.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
    window.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 100))
    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    return True
                elif event.key == pygame.K_q:
                    return False 

def load_level(level_index):
    level_data = levels[level_index]
    level_end = level_data["ending"]
    background, bg_image = get_background(level_data["background"])
    blocks = [Block(x, y, size) for x, y, size in level_data["blocks"]]
    fires = [Fire(x, y, width, height) for x, y, width, height in level_data["fires"]]
    bananas = [Banana(x, y, width, height, banana_collect_sound) for x, y, width, height in level_data["bananas"]]
    return level_end, background, bg_image, blocks + fires + bananas

###################################################################### LEVELS

levels = [
    #default level
    {
        "ending": 26,
        "background": "clouds_one.jpeg",
        "blocks": [
            (0 * block_size, HEIGHT - block_size, block_size), (1 * block_size, HEIGHT - block_size, block_size), (2 * block_size, HEIGHT - block_size, block_size),
            (3 * block_size, HEIGHT - block_size, block_size), (4 * block_size, HEIGHT - block_size, block_size), (5 * block_size, HEIGHT - block_size, block_size),
            (6 * block_size, HEIGHT - block_size, block_size), (7 * block_size, HEIGHT - block_size, block_size), (8 * block_size, HEIGHT - block_size, block_size),
            (2 * block_size, HEIGHT - 3 * block_size, block_size), (5 * block_size, HEIGHT - 4 * block_size, block_size), (6 * block_size, HEIGHT - 4 * block_size, block_size),
            (7 * block_size, HEIGHT - 4 * block_size, block_size), (5 * block_size, HEIGHT - 6 * block_size, block_size), (7 * block_size, HEIGHT - 7 * block_size, block_size),
            (8 * block_size, HEIGHT - 7 * block_size, block_size), (9 * block_size, HEIGHT - 7 * block_size, block_size), (10 * block_size, HEIGHT - 7 * block_size, block_size),
            (12 * block_size, HEIGHT - 5 * block_size, block_size), (13 * block_size, HEIGHT - 5 * block_size, block_size), (13 * block_size, HEIGHT - block_size, block_size),
            (14 * block_size, HEIGHT - block_size, block_size), (17 * block_size, HEIGHT - 3 * block_size, block_size), (18 * block_size, HEIGHT - 3 * block_size, block_size),
            (19 * block_size, HEIGHT - 3 * block_size, block_size), (20 * block_size, HEIGHT - 3 * block_size, block_size), (21 * block_size, HEIGHT - 3 * block_size, block_size),
            (18 * block_size, HEIGHT - 5 * block_size, block_size), (19 * block_size, HEIGHT - 6 * block_size, block_size), (20 * block_size, HEIGHT - 6 * block_size, block_size),
            (23 * block_size, HEIGHT - block_size, block_size), (24 * block_size, HEIGHT - block_size, block_size), (25 * block_size, HEIGHT - block_size, block_size),
            (26 * block_size, HEIGHT - block_size, block_size)
        ],
        "fires": [
            (2 * block_size, HEIGHT - block_size - 64, 16, 32), (4 * block_size, HEIGHT - block_size - 64, 16, 32),
            (4 * block_size + 48, HEIGHT - block_size - 64, 16, 32), (5 * block_size, HEIGHT - block_size - 64, 16, 32),
            (7 * block_size, HEIGHT - 7 * block_size - 64, 16, 32), (12 * block_size, HEIGHT - 5 * block_size - 64, 16, 32),
            (20 * block_size + 32, HEIGHT - 3 * block_size - 64, 16, 32), (19 * block_size + 32, HEIGHT - 6 * block_size - 64, 16, 32)
        ],
        "bananas": [
            (3 * block_size, HEIGHT - 2 * block_size, 32, 32), (6 * block_size, HEIGHT - 5 * block_size, 32, 32),
            (9 * block_size, HEIGHT - 8 * block_size, 32, 32)
        ]
    },
    # easy level
    {
        "ending": 33,
        "background": "clouds_one.jpeg",
        "blocks": [
            (0 * block_size, HEIGHT - block_size, block_size), (1 * block_size, HEIGHT - block_size, block_size), (2 * block_size, HEIGHT - block_size, block_size),
            (3 * block_size, HEIGHT - block_size, block_size), (4 * block_size, HEIGHT - block_size*2, block_size), (5 * block_size, HEIGHT - block_size*2, block_size),
            (6 * block_size, HEIGHT - block_size*2, block_size), (7 * block_size, HEIGHT - block_size*2, block_size), (8 * block_size, HEIGHT - block_size*3, block_size),
            (9 * block_size, HEIGHT - block_size*3, block_size), (10 * block_size, HEIGHT - block_size*3, block_size), (11 * block_size, HEIGHT - block_size*3, block_size),
            (12 * block_size, HEIGHT - block_size*3, block_size), (13 * block_size, HEIGHT - block_size*3, block_size), (14 * block_size, HEIGHT - block_size*5, block_size),
            (15 * block_size, HEIGHT - block_size*5, block_size), (16 * block_size, HEIGHT - block_size*5, block_size), (17 * block_size, HEIGHT - block_size*3, block_size),
            (18 * block_size, HEIGHT - block_size*3, block_size), (19 * block_size, HEIGHT - block_size*3, block_size), (22 * block_size, HEIGHT - block_size*3, block_size),
            (23 * block_size, HEIGHT - block_size*3, block_size), (24 * block_size, HEIGHT - block_size*3, block_size), (26 * block_size, HEIGHT - block_size*4, block_size),
            (27 * block_size, HEIGHT - block_size*5, block_size), (28 * block_size, HEIGHT - block_size*5, block_size), (30 * block_size, HEIGHT - block_size, block_size),
            (31 * block_size, HEIGHT - block_size, block_size), (32 * block_size, HEIGHT - block_size, block_size), (33 * block_size, HEIGHT - block_size, block_size)
        ],
        "fires": [
            (10 * block_size, HEIGHT - block_size*3 - 64, 16, 32),(23 * block_size, HEIGHT - block_size*3 - 64, 16, 32),(28 * block_size, HEIGHT - block_size*5 - 64, 16, 32),
        ],
        "bananas": [
            (2 * block_size, HEIGHT - 2 * block_size, 32, 32),(3 * block_size, HEIGHT - 2 * block_size, 32, 32),(4 * block_size, HEIGHT - 3 * block_size, 32, 32),
            (5 * block_size, HEIGHT - 3 * block_size, 32, 32),(6 * block_size, HEIGHT - 3 * block_size, 32, 32),(7 * block_size, HEIGHT - 3 * block_size, 32, 32),
            (12 * block_size, HEIGHT - 4 * block_size, 32, 32),(13 * block_size, HEIGHT - 4 * block_size, 32, 32),(15 * block_size, HEIGHT - 6 * block_size, 32, 32),
            (16 * block_size, HEIGHT - 6 * block_size, 32, 32),(17 * block_size, HEIGHT - 7 * block_size, 32, 32),(17 * block_size, HEIGHT - 4 * block_size, 32, 32),
            (18 * block_size, HEIGHT - 4 * block_size, 32, 32),(19 * block_size, HEIGHT - 4 * block_size, 32, 32),(26 * block_size, HEIGHT - 6 * block_size, 32, 32),
            (33 * block_size, HEIGHT - 2 * block_size, 32, 32)
        ]
    },

]

######################################################################MAIN FUNCTION

def main(window):
    clock = pygame.time.Clock()
    level_index = 1
    level_end, background, bg_image, objects = load_level(level_index)#############change background
 

    player = Player(100,100,50,50, hit_sound)

        #########################STILL ADD FIRE TO BE DRAWN

    offset_x = 0
    offset_y = 0##if needed
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
        
        ###animation loops
        player.loop(FPS)
        for obj in objects:
            if hasattr(obj, 'loop'):
                obj.loop()
            #if isinstance(obj, Fire):
                #obj.loop()

        handle_move(player, objects)
        draw(window,background,bg_image,player,objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

        if player.rect.top > HEIGHT:
            player.lives -= 1
            if player.lives == 0:
                run = False
                died_screen(window,player.score)

            #pygame.time.wait(1000)  # Add a 1-second delay
            target_x = 100
            target_offset_x = max(0, target_x - WIDTH // 2)  # Calculate the target offset

            # Smoothly move the view to the target position
            while offset_x != target_offset_x:
                if offset_x < target_offset_x:
                    offset_x = min(offset_x + PLAYER_VEL, target_offset_x)
                else:
                    offset_x = max(offset_x - PLAYER_VEL, target_offset_x)

                draw(window, background, bg_image, player, objects, offset_x)
                pygame.time.delay(10)  # Adjust the delay for smoother transition

            player.rect.x = target_x
            player.rect.y = 100

        if player.lives == 0:
            run = False
            died_screen(window, player.score)

        if player.rect.x > (block_size*level_end):#undo comment for finish line later
            level_index += 1
            if level_index >= len(levels):
                run = False
                won_screen(window, player.score)
            else:
                if level_transition(window, player.score):
                    level_end, background, bg_image, objects = load_level(level_index)
                    player.rect.x = 100
                    player.rect.y = 100
                    offset_x = 0
                else:
                    pygame.quit()
                    quit()
    

    pygame.quit()
    quit()

if __name__ == "__main__":
    main(window)