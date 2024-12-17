import pygame as pg
import sys
import math
from pygame.math import Vector2
from rich.console import Console

console = Console()

class Block:
    def __init__(self, x, y, width, height, parent=None, elasticity=0.8, player_no=0):
        self.parent = parent
        self.width = width
        self.height = height
        self.player_no = player_no
        self.x = x
        self.y = y
        self.color = (0, 128, 255)
        self.mass = self.width * self.height
        self.vx = 0
        self.vy = 0
        self.angle = 0  # Initial angle of rotation (in radians)
        self.angular_velocity = 0  # Initial angular velocity
        self.elasticity = elasticity

        # Moment of inertia for a rectangle about its center
        self.moment_of_inertia = (1 / 12) * self.mass * (self.width**2 + self.height**2)

    def draw(self, screen):
        # Draw the rotated block
        rect = pg.Rect(0, 0, self.width, self.height)
        rect.center = (self.x + self.width / 2, self.y + self.height / 2)
        rotated_image = pg.Surface((self.width, self.height), pg.SRCALPHA)
        rotated_image.fill(self.color)
        rotated_image = pg.transform.rotate(rotated_image, math.degrees(self.angle))
        rotated_rect = rotated_image.get_rect(center=rect.center)
        screen.blit(rotated_image, rotated_rect.topleft)

    def update(self):
        # Apply gravity if not on another block
        if not self.check_for_collision_with_block():
            self.vy += self.parent.gravity

        # Handle rotation and torque
        support_point = self.get_support_point()
        if support_point:
            torque = self.calculate_torque(support_point)
            self.angular_velocity += torque / self.moment_of_inertia
        else:
            self.angular_velocity *= 0.98  # Dampen angular velocity in free fall

        # Update position and rotation
        self.y += self.vy
        self.x += self.vx
        self.angle += self.angular_velocity

        # Collision with ground
        if self.y + self.height > self.parent.winheight:
            self.y = self.parent.winheight - self.height
            self.vy = -self.vy * self.elasticity
            self.angular_velocity *= -self.elasticity

        # Collision with walls
        if self.x < 0:
            self.x = 0
            self.vx = -self.vx * self.elasticity
        elif self.x + self.width > self.parent.winwidth:
            self.x = self.parent.winwidth - self.width
            self.vx = -self.vx * self.elasticity

    def calculate_torque(self, support_point):
        # Calculate torque based on the center of mass relative to the support point
        center_of_mass = Vector2(self.x + self.width / 2, self.y + self.height / 2)
        lever_arm = Vector2(support_point[0], support_point[1]) - center_of_mass
        force = Vector2(0, self.mass * self.parent.gravity)  # Force due to gravity
        return lever_arm.cross(force)  # Torque = lever_arm × force

    def get_support_point(self):
        # Check if the block is supported and return the support point
        for player in self.parent.players:
            if player != self and self.y + self.height == player.y:
                if self.x + self.width > player.x and self.x < player.x + player.width:
                    # Return the edge of the other block closest to this block's center of mass
                    if self.x + self.width / 2 < player.x + player.width / 2:
                        return (player.x, player.y)
                    else:
                        return (player.x + player.width, player.y)
        return None  # No support point found

    def check_for_collision_with_block(self):
        # Simplified collision detection
        for player in self.parent.players:
            if player != self:
                if self.x < player.x + player.width and self.x + self.width > player.x and self.y + self.height == player.y:
                    return True
        return False


class Game:
    def __init__(self):
        pg.init()
        self.winwidth = 1200
        self.winheight = 700
        self.screen = pg.display.set_mode((self.winwidth, self.winheight))
        pg.display.set_caption("Physics")
        self.clock = pg.time.Clock()
        self.done = False
        
        self.gravity = 0.5
        self.players = [Block(375, 0, 50, 50, self, 0.8)]

    def get_mouse_pos(self):
        return pg.mouse.get_pos()

    def create_delete_block(self):
        if pg.mouse.get_pressed()[2]:  # Right-click to create a block
            x, y = self.get_mouse_pos()
            self.players.append(Block(x, y, 50, 50, self, 0.8))

    def run(self):
        while not self.done:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.done = True

            self.screen.fill((255, 255, 255))
            
            self.create_delete_block()
            
            for player in self.players:
                player.update()
                player.draw(self.screen)

            pg.display.flip()
            self.clock.tick(60)

        pg.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
