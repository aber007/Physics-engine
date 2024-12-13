import pygame as pg
import sys
import math

class Block:
    def __init__(self, x, y, width, height, parent=None, elasticity=0.8):
        self.parent : Game = parent
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.color = (0, 128, 255)
        self.vx = 10
        self.vy = 0
        self.eslasticity = elasticity
        


    def draw(self, screen):
        pg.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def update(self):
        self.vy += self.parent.gravity
        self.y += self.vy
        self.x += self.vx

        # Check for collision with the ground
        if self.y > 500 + self.width:
            self.y = 500 + self.width
            self.vy = -self.vy * self.eslasticity
            if abs(self.vy) < 0.2:
                self.vy = 0
        else:
            self.vy *= self.parent.air_resistance
        
        # Check for collision with the walls
        if self.x < 0:
            self.vx = -self.vx * self.eslasticity
            self.x = 0
        elif self.x > 800 - self.width:
            self.vx = -self.vx * self.eslasticity
            self.x = 800 - self.width
        else:
            self.vx *= self.parent.air_resistance

        # Apply friction
        if self.vy == 0:
            self.vx *= self.parent.friction
        else:
            self.vx *= self.parent.air_resistance

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((800, 600))
        pg.display.set_caption("Physics")
        self.clock = pg.time.Clock()
        self.done = False
        self.line = False
        
        self.gravity = 0.5
        self.friction = 0.9
        self.air_resistance = 0.995
        self.elasticity = 0.8

        self.player = Block(375, 0, 50, 50, self, self.elasticity)
    def get_mouse_pos(self):
        x, y = pg.mouse.get_pos()
        return x, y
    
    def get_location_of_block_from_mouse(self):
        x, y = self.get_mouse_pos()
        return math.sqrt((x - self.player.x-(self.player.width/2))**2 + (y - self.player.y-(self.player.width/2))**2)
    
    def grab(self):
        if pg.mouse.get_pressed()[0]:    
            line_length = self.get_location_of_block_from_mouse()
            if line_length < 150 or self.line:
                self.line = True
                self.air_resistance = 0.99
                pg.draw.line(self.screen, (0, 0, 0), (self.player.x + self.player.width/2, self.player.y + self.player.width/2), self.get_mouse_pos(), 2)
                if line_length > 150:
                    self.player.vx -= ((self.player.x + self.player.width/2 - self.get_mouse_pos()[0]) / 10) * (self.player.eslasticity / 2)
                    self.player.vy -= ((self.player.y + self.player.width/2 - self.get_mouse_pos()[1]) / 10) * (self.player.eslasticity / 2)
            else:
                self.air_resistance = 0.995
        else:
            self.line = False
            self.air_resistance = 0.995
    
    def run(self):
        while not self.done:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.done = True
            
            self.screen.fill((255, 255, 255))
            self.player.update()
            self.player.draw(self.screen)
            self.grab()

            


            

            pg.display.flip()
            self.clock.tick(60)

        pg.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()