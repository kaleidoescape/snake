import itertools
import sys
import random
import numpy as np
import pygame
from collections import deque
from pygame import K_DOWN, K_ESCAPE, K_LEFT, K_RIGHT, K_UP, QUIT

class Game():

    def __init__(self, board_height, board_width):
        self.height = board_height
        self.width = board_width
        self.buffer = 1

        self.score = 0
        self.score_multiplier = 1
        self.game_over = False
        
        self.vert_speed = 1
        self.horiz_speed = 1
        self.initialize_movement()

        self.empty_icon = 0
        self.snake_icon = 1
        self.apple_icon = 2

        self.initialize_board()
        self.snake_body = None
        self.snake_head = None
        self.apples = None
        self.initialize_snake()
        self.initialize_apples()

    def initialize_board(self):
        self.board = np.zeros((self.height, self.width), dtype=int)

    def initialize_movement(self):
        self.movement = {
            None:    (0, 0),
            K_UP:    (0, -self.vert_speed),
            K_DOWN:  (0,  self.vert_speed),
            K_LEFT:  (-self.horiz_speed, 0), 
            K_RIGHT: ( self.horiz_speed, 0)
        }
        self.backwards = {
            None: None,
            K_UP: K_DOWN,
            K_DOWN: K_UP,
            K_LEFT: K_RIGHT,
            K_RIGHT: K_LEFT,
        }
        self.last_move = None 

    def initialize_snake(self, snake_length=3):
        if self.snake_head is None:
            x, y = self.random_free_spot(
                extra_x_buffer=snake_length, 
                extra_y_buffer=snake_length
            )
            self.snake_head = (x, y)
            self.board[x, y] = self.snake_icon
            self.snake_body = deque()

        tall = random.randint(0, 1)

        x, y = self.snake_head
        for i in range(1, snake_length):
            if tall:
                new_x = x
                new_y = y + i
                self.last_move = K_UP
                self.backwards[None] = K_DOWN
            else:
                new_x = x + i
                new_y = y
                self.last_move = K_LEFT
                self.backwards[None] = K_RIGHT
            self.board[new_x, new_y] = self.snake_icon
            self.snake_body.append((new_x, new_y))

    def initialize_apples(self, amount=1):
        if self.apples is None:
            self.apples = deque()

        for i in range(amount):
            self.spawn_apple()

    def get_move(self, key):
        if key == self.backwards[self.last_move]:
            key = self.last_move
        if key is None:
            key = self.last_move
        self.last_move = key


        delta_x, delta_y = self.movement[key]
        x, y = self.snake_head
        x = x + delta_x
        y = y + delta_y
        return (x, y)

    def update_snake(self, key):
        x, y = self.get_move(key)
        if self.collided(x, y):
            self.game_over = True
        elif (x, y) in self.apples:
            self.grow_snake()
        else:
            self.move_snake(x, y)

    def collided(self, x, y):
        if (x >= self.height or 
            x < 0 or
            y >= self.width or
            y < 0 or
            self.board[x, y] == self.snake_icon):
            return True
        else:
            return False

    def move_snake(self, x, y):
        self.snake_body.appendleft(self.snake_head)
        self.snake_head = (x, y)
        old_x, old_y = self.snake_body.pop()
        self.board[x, y] = self.snake_icon
        self.board[old_x, old_y] = self.empty_icon
        
    def spawn_apple(self):
        x, y = self.random_free_spot()
        self.board[x, y] = self.apple_icon
        self.apples.append((x, y))

    def grow_snake(self):
        x, y = self.apples.popleft() #TODO account for multiple apples
        self.board[x,y] = self.snake_icon
        self.snake_body.appendleft(self.snake_head)
        self.snake_head = (x, y)
        self.score += self.score_multiplier
        self.spawn_apple()

    def random_free_spot(self, 
                         extra_x_buffer=0, 
                         extra_y_buffer=0, 
                         use_buffer=True):
        if use_buffer:
            buffer = self.buffer
        else:
            buffer = 0
        while True:
            x = random.randint(
                self.buffer + extra_x_buffer, 
                self.height - buffer - extra_x_buffer
            )
            y = random.randint(
                self.buffer + extra_y_buffer,
                self.width - buffer - extra_y_buffer
            )
            if not self.board[x, y]:
                return (x, y)

class App():
    
    def __init__(self,
                 pixel_height = 20,
                 pixel_width = 20,
                 screen_height = 600,
                 screen_width = 600):
        self.pixel_height = pixel_height
        self.pixel_width = pixel_width
        self.screen_height = screen_height
        self.screen_width = screen_width
        self.colors = {
            'background': (200, 200, 200), 
            'snake_head': (5, 140, 55),
            'snake_body': (0, 160, 40),  
            'apple': (255, 0, 0),
            'text': (0, 0, 0)
        }
        self.usable_keys = [K_UP, K_DOWN, K_LEFT, K_RIGHT]

        self.board_height = int(screen_height / pixel_height)
        self.board_width = int(screen_height / pixel_height)
        self.game = Game(self.board_height, self.board_width)
        

    def coords_to_field(self, x, y):
        return (x * self.pixel_width, y * self.pixel_height)

    def draw(self, x, y, piece_name):
        x, y = self.coords_to_field(x, y)
        pygame.draw.rect(
            self.display, 
            self.colors[piece_name], 
            pygame.Rect(x, y, self.pixel_width, self.pixel_height)
        )

    def display_snake(self):
        for (x, y) in self.game.snake_body:
            self.draw(x, y, 'snake_body')

        x, y = self.game.snake_head
        self.draw(x, y, 'snake_head')
        
    def display_apples(self):
        for (x, y) in self.game.apples:
            self.draw(x, y, 'apple')

    def on_init(self):
        pygame.init()
        pygame.display.set_caption('Snake Game')
        self.display = pygame.display.set_mode(
            (self.screen_width, self.screen_height) 
        )
        self.clock = pygame.time.Clock()
        self._running = True
 
    def on_event(self, event):
        if event.type == QUIT:
            self._running = False

    def on_render(self):
        if self.game.game_over:
            self.on_game_over()
        else:
            self.display.fill(self.colors['background'])
            self.display_apples()
            self.display_snake()
        pygame.display.flip()

    def on_game_over(self, font_size=40):
        font = pygame.font.Font(None, font_size)

        game_over_text = font.render("Game Over", True, self.colors['text'])
        game_over_text_rect = game_over_text.get_rect()
        game_over_text_x = self.display.get_width() / 2 - game_over_text_rect.width / 2
        game_over_text_y = self.display.get_height() / 2 - game_over_text_rect.height / 2
        self.display.blit(game_over_text, [game_over_text_x, game_over_text_y])

        score_text = font.render(f"Score: {self.game.score}", True, self.colors['text'])
        score_text_rect = score_text.get_rect()
        score_text_x = self.display.get_width() / 2 - score_text_rect.width / 2
        score_text_y = game_over_text_y + font_size
        self.display.blit(score_text, [score_text_x, score_text_y])

    def on_loop(self, last_key):
        if self.game.game_over:
            self.on_game_over()

        for e in pygame.event.get():
            self.on_event(e)

        keys = pygame.key.get_pressed()
        if keys[K_ESCAPE]:
            self._running = False

        for k in self.usable_keys:
            if keys[k]:
                last_key = k

        if not last_key:
            return last_key

        self.game.update_snake(last_key)
        return last_key
    
    def on_cleanup(self):
        pygame.quit()
 
    def on_execute(self, speed=10):
        self.on_init()

        last_key = None
        while self._running:
            last_key = self.on_loop(last_key)
            self.on_render()
            self.clock.tick(speed)
        self.on_cleanup()



if __name__ == "__main__" :
    app = App()
    app.on_execute()

