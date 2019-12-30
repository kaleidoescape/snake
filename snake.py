import itertools
import sys
import random
import numpy as np
import pygame
from collections import deque
from pygame import K_DOWN, K_ESCAPE, K_LEFT, K_RIGHT, K_UP, QUIT

class GameException(BaseException):
    """Raise for errors running the game."""

class Snake():
    def __init__(self):
        self.head = None
        self.body = deque()

    def initialize(self, x, y, length=3):
        self.head = (x, y)
        tall = random.randint(0, 1)
        for i in range(1, length):
            if tall:
                new_x = x
                new_y = y + i
                last_move = K_UP
            else:
                new_x = x + i
                new_y = y
                last_move = K_LEFT
            self.body.append((new_x, new_y))
        return last_move

    def move(self, x, y):
        self.body.appendleft(self.head)
        self.head = (x, y)
        old_x, old_y = self.body.pop() #pop poop
        return old_x, old_y 
        
    def grow(self, x, y):
        old_x, old_y = self.head
        self.body.appendleft(self.head)
        self.head = (x, y)
        return old_x, old_y

class Board():
    def __init__(self, board_height, board_width, buffers=[1, 1]):
        self.height = board_height
        self.width = board_width
        self.buffers = buffers
        self.pieces = {
            'snake_head': 3,
            'snake_body': 2,
            'apple': 1,
            'empty': 0
        }
        self.piece_names = {self.pieces[k]:k for k in self.pieces}

        self.board = np.zeros((self.height, self.width), dtype=int)

    def random_free_spot(self, 
                         extra_buffers=[0, 0], 
                         use_basic_buffers=True):
        if use_basic_buffers:
            buffers = self.buffers
        else:
            buffers = [0, 0]
        while True:
            x = random.randint(
                buffers[0] + extra_buffers[0],              #from
                self.height - buffers[0] - extra_buffers[0] #to
            )
            y = random.randint(
                buffers[1] + extra_buffers[1],              #from
                self.height - buffers[1] - extra_buffers[1] #to
            )
            if self.get_piece(x, y) == 'empty':
                return (x, y)

    def set_piece(self, x, y, piece_name):
        self.board[x, y] = self.pieces[piece_name]
    
    def get_piece(self, x, y):
        name = self.piece_names[self.board[x, y]]
        return name

class Game():

    def __init__(self, board_height, board_width):
        self.board = Board(board_height, board_width)

        self.score = 0
        self.score_multiplier = 1
        self.game_over = False
        
        self.vert_speed = 1
        self.horiz_speed = 1
        self.initialize_movement()

        self.initialize_snake()

        self.n_apples = 1
        self.initialize_apples()

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

    def initialize_apples(self):
        self.apples = set()
        for i in range(self.n_apples):
            self.spawn_apple()

    def spawn_apple(self):
        x, y = self.board.random_free_spot()
        self.board.set_piece(x, y, 'apple')
        self.apples.add((x, y))

    def initialize_snake(self, snake_length=3):
        x, y = self.board.random_free_spot(
            extra_buffers=[snake_length, snake_length])
        self.snake = Snake()
        self.last_move = self.snake.initialize(x, y)
        self.backwards[None] = self.backwards[self.last_move]
        self.board.set_piece(x, y, 'snake_head')
        for x, y in self.snake.body:
            self.board.set_piece(x, y, 'snake_body')

    def get_move(self, key):
        if key == self.backwards[self.last_move]:
            key = self.last_move
        if key is None:
            key = self.last_move
        self.last_move = key

        delta_x, delta_y = self.movement[key]
        x, y = self.snake.head
        x = x + delta_x
        y = y + delta_y
        return (x, y)

    def update_snake(self, key):
        x, y = self.get_move(key)
        if self.collided(x, y):
            self.game_over = True
        elif (x, y) in self.apples:
            self.grow_snake(x, y)
        else:
            self.move_snake(x, y)

    def collided(self, x, y):
        if (x >= self.board.height or 
            x < 0 or
            y >= self.board.width or
            y < 0 or
            self.board.get_piece(x, y) == 'snake_body'):
            return True
        else:
            return False

    def move_snake(self, x, y):
        old_x, old_y = self.snake.move(x, y)
        self.board.set_piece(x, y, 'snake_head')
        self.board.set_piece(old_x, old_y, 'empty')
        
    def grow_snake(self, x, y):
        assert (x, y) in self.apples, 'no apple found at ({x}, {y})'

        self.apples.remove((x, y))
        old_x, old_y = self.snake.grow(x, y)
        self.board.set_piece(old_x, old_y, 'snake_body')
        self.board.set_piece(x, y, 'snake_head')
        self.score += self.score_multiplier
        self.spawn_apple()

class App():
    
    def __init__(self,
                 pixel_height = 25,
                 pixel_width = 25,
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
        for (x, y) in self.game.snake.body:
            self.draw(x, y, 'snake_body')

        x, y = self.game.snake.head
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

