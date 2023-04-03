import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()


## Global Variables ##
pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
# Set caption and window
window = pygame.display.set_mode((WIDTH, HEIGHT))

# Flip sprites for right movement
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

# Get sprites
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]
    
    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0,0), rect)
            sprites.append(pygame.transform.scale2x(surface))
        
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")]  = sprites
            
    return all_sprites

# Get blocks
def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

## Create and control player ##
class Player(pygame.sprite.Sprite):
    # Class variable for all players
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3
    
    def __init__(self, x, y, width, height):
        # Player rectangle
        self.rect = pygame.Rect(x, y, width, height)
        # Speed of player in each frame
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
    
    # Jump    
    def jump(self):
        # Change y_vel up, then gravity will take player down
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        # For double jump + remove gravity (count)
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    
    # Displacement per frame, move x and y of player Rect (i.e. one while loop iteration)
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy
        
    def make_hit(self):
        self.hit = True
        self.hit_count = 0
    
    # Movement
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
    
    # Called once per frame - move, update animation etc.
    def loop(self, fps):
        self.move(self.x_vel, self.y_vel)
        
        # Increment y_vel (e.g. fall for 60 frames, fall_count = 60, falling for 1 second, inc y by 1)
        self.y_vel += min( 1, (self.fall_count / fps) * self.GRAVITY)
    

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0
        
        # Add +1 to fall count
        self.fall_count += 1
        self.update_sprite()
    
    def landed(self):
        # Stop adding to gravity
        self.fall_count = 0
        # Stop moving down
        self.y_vel = 0
        # Reset double jump
        self.jump_count = 0
    
    def hit_head(self):
        # Start count
        self.count = 0
        # Bounce off block
        self.y_vel = -1
        # Reset double jump
        self.jump_count = 0
    
    
    
    # Animating characters  
    def update_sprite(self):
        # No movement is idle animation
        sprite_sheet = "idle2"
        
        if self.hit:
            sprite_sheet = "hit"
            
        # Jumping/falling
        if self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        
        # If movement, run animation
        if self.x_vel != 0:
            sprite_sheet = "run"  
        
        # For left and right   
        sprite_sheet_name = sprite_sheet + "_" + self.direction
        
        # Getting resource
        sprites = self.SPRITES[sprite_sheet_name]
        
        # Changing animation every 3 frames. Looping depending on number of sprites in animation
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()
    
    def update(self):
        # Allowing adjustment to sprite shape
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        # Map sprite pixels - for pixel perfect collision vs rectangle collision
        self.mask = pygame.mask.from_surface(self.sprite)
    
    # Draw sprites
    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

        
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
     
    def draw(self, win, offset_x):
         win.blit(self.image, (self.rect.x - offset_x, self.rect.y))   

## Blocks ##   
class Block(Object):
    # Size, draw on surface, collision
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)  
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

## Fire traps ##
class Fire(Object):
    
    ANIMATION_DELAY = 3
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"
    
    def on(self):
        self.animation_name = "on"
    
    def off(self):
        self.animation_name = "off"
    
    def loop(self):
        # Getting resource
        sprites = self.fire[self.animation_name]
        
        # Changing animation every 3 frames. Looping depending on number of sprites in animation
        sprite_index = (self.animation_count // 
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        # Allowing adjustment to sprite shape
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        # Map sprite pixels - for pixel perfect collision vs rectangle collision
        self.mask = pygame.mask.from_surface(self.image)
        
        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


## Get background ##
def get_background(name):
    # Load background asset, get wxh, 
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    
    tiles = []
    # Loop through no. of x&y tiles
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            # Position of each tile
            pos = (i * width, j * height)
            tiles.append(pos)
    
    return tiles, image
    
## Draw objects ##    
def draw(window, background, bg_image, player, objects, offset_x):
    # Loop through every tile and bg_image
    for tile in background:
        window.blit(bg_image, tile)
    
    for obj in objects:
        obj.draw(window, offset_x)
       
    # Draw player    
    player.draw(window, offset_x)
        
    pygame.display.update()   
    
## Vertical collision ##    
def handle_vertical_collision(player, objects, dy):
    
    collided_objects = []
    
    # Pass player and object Object. If masks collide
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            # If moving down, player bot = object top
            if dy > 0:
                player.rect.bottom = obj.rect.top
                # What happens when...
                player.landed()
            # Vice-versa    
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
            
            collided_objects.append(obj)
    
    return collided_objects

## Horizontal collision ##
def collide(player, objects, dx):
    # Move player
    player.move(dx, 0)
    # Update mask
    player.update()
    # Check if player would collide
    collided_object = None
    for obj in objects:
        # If yes, get collide object
        if pygame.sprite.collide_mask(player, obj): 
            collided_object = obj
            break
    # Reverse movement
    player.move(-dx, 0)
    # Re-update mask
    player.update()

    return collided_object
    
    
                

## Input control ##    
def handle_move(player, objects):
    keys = pygame.key.get_pressed()
    
    player.x_vel = 0
    
    # Call hor collision functions (*2 mini hack)
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)
    
    # Move L and R if key pressed and no hor collision
    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)
    
    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit() 
    
## Main function to start the game ##
def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")
    
    block_size = 96
    
    # Call a Player object
    player = Player(100, 100, 50, 50)
    fire = Fire(100, HEIGHT - block_size -64, 16, 32)
    fire.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) 
            for i in range(-WIDTH // block_size, WIDTH * 2 // block_size )]
    
    objects  = [*floor, Block(0, HEIGHT - block_size * 2, block_size), 
                Block(block_size * 3, HEIGHT - block_size * 4, block_size),
                fire]
    
    # Scrolling
    offset_x = 0
    scroll_area_width = 200
    
    run = True
    while run:
        # Ensure loop only runs at given FPS
        clock.tick(FPS)
        
        for event in pygame.event.get():
            # First event to check - Quit game
            if event.type == pygame.QUIT:
                run = False
                break
            
            # Not in handle_move to ensure holding key down does not continually jump
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
            
            
        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)
        
        # Call background draw function
        draw(window, background, bg_image, player, objects, offset_x)
        
        # Check if player has crossed a boundary (area) and check moving right/left.
        # If true, offset the screen by player vel
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel
            
    pygame.quit()
    quit()
    
    
# Only call main function when run file directly
if __name__ == "__main__":
    main(window)
    
