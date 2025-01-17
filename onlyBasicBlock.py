import pygame as pg
import sys
import math
import os
from rich.console import Console
from pygame.math import Vector2

console = Console()

class Block:
    def __init__(self, x, y, width, height, parent=None, elasticity=0.8, player_no=0, fancy_parent=None):
        self.parent : Game = parent
        self.width = width
        self.height = height
        self.player_no = player_no
        self.x = x
        self.y = y
        self.color = (0, 128, 255)
        self.maxradius = math.sqrt((self.width/2)**2 + (self.height/2)**2)
        self.vx = 0
        self.vy = 0
        self.eslasticity = elasticity

        self.top = self.y
        self.bottom = self.y + self.height
        self.left = self.x
        self.right = self.x + self.width

        if self.width == 0 or self.height == 0:
            self.mass = self.fancy_parent.mass
        else:
            self.mass = self.width * self.height
        self.kinetic_energy = 1/2 * self.mass * (self.vx**2 + self.vy**2)
        self.potential_energy = self.mass * self.parent.gravity * self.y

        self.angular_velocity = 0
        self.moment_of_inertia = (1 / 12) * self.mass * (self.width**2 + self.height**2)
        self.angle = 0

    def draw(self, screen):
    # Draw the rotated block
        rect = pg.Rect(0, 0, self.width, self.height)
        rect.center = (self.x + self.width / 2, self.y + self.height / 2)
        rotated_image = pg.Surface((self.width, self.height), pg.SRCALPHA)
        rotated_image.fill(self.color)
        rotated_image = pg.transform.rotate(rotated_image, math.degrees(self.angle))
        rotated_rect = rotated_image.get_rect(center=rect.center)
        screen.blit(rotated_image, rotated_rect.topleft)


    
    def update(self, fancy=False, fancy_block_width=None, fancy_block_height=None, fancy_width=None, fancy_height=None):

        block_underneath = self.check_for_collision_with_block()
        
        
        if block_underneath == False:
            self.vy += self.parent.gravity
        else:
            if self.vy > 0.01:  # If falling, allow bounce
                self.vy = -self.vy * self.eslasticity
            else:  # If resting, do not override velocities from collision handling
                self.vy *= 0.5  # Slight damping to simulate rest without full stop
                self.vx *= self.parent.friction
                return


        self.y += self.vy
        self.x += self.vx
        # Check for collision with the ground
        if self.y > self.parent.winheight - self.height:
            self.y = self.parent.winheight - self.height
            self.vy = -self.vy * self.eslasticity
            self.parent.move_up = True
        else:
            self.vy *= self.parent.air_resistance

        # Check for collision with the ceiling
        if self.y < 0:
            self.y = 0
            self.vy = -self.vy * self.eslasticity
        else:
            self.vy *= self.parent.air_resistance
        
        # Check for collision with the walls
        if self.x < 0:
            self.vx = -self.vx * self.eslasticity
            self.x = 0
        elif self.x > self.parent.winwidth - self.width:
            self.vx = -self.vx * self.eslasticity
            self.x = self.parent.winwidth - self.width
        else:
            self.vx *= self.parent.air_resistance


        self.top = self.y
        self.bottom = self.y + self.height
        self.left = self.x
        self.right = self.x + self.width

        self.check_for_collision_with_block()

        # Apply friction
        if self.vy == 0:
            self.vx *= self.parent.friction
        else:
            self.vx *= self.parent.air_resistance


    def get_closest_side(self, player):
        top = abs(self.top - player.bottom)
        bottom = abs(self.bottom - player.top)
        left = abs(self.left - player.right)
        right = abs(self.right - player.left)
        
        closest = min(top, bottom, left, right)
        if closest == top:
            return "top"
        elif closest == bottom:
            return "bottom"
        elif closest == left:
            return "left"
        elif closest == right:
            return "right"
        
    def fix_overlap(self, player, closest_side):

        if closest_side == "top":
            self.y = player.bottom
            self.vy = max(self.vy, 0)  # Prevent downward velocity after correction
        elif closest_side == "bottom":
            self.y = player.top - self.height
            self.vy = min(self.vy, 0)  # Prevent upward velocity after correction
        elif closest_side == "left":
            self.x = player.right
        elif closest_side == "right":
            self.x = player.left - self.width
    
    def energy_transfer(self, player, closest_side):
        # Relative velocity components
        relative_vx = self.vx - player.vx
        relative_vy = self.vy - player.vy

        # Normal vector components based on the collision side
        if closest_side == "top" or closest_side == "bottom":
            normal_x, normal_y = 0, 1  # Collision normal is vertical
        elif closest_side == "left" or closest_side == "right":
            normal_x, normal_y = 1, 0  # Collision normal is horizontal
        else:
            return  # Exit if side is undefined

        # Calculate the normal velocity (velocity along the collision normal)
        normal_velocity = relative_vx * normal_x + relative_vy * normal_y


        # No collision if normal velocity is not directed toward the other object
        if normal_velocity >= 0:
            return

        # Effective mass for collision response
        m1 = self.mass
        m2 = player.mass

        if m1 == 0 or m2 == 0:
            console.print("Mass is zero", style="bold red")

        # Elasticity factor (average elasticity of both objects)
        e = (self.eslasticity + player.eslasticity) / 2

        # Impulse magnitude (using 1D collision formula along the normal)
        impulse = -(1 + e) * normal_velocity / (1 / m1 + 1 / m2)

        # Update velocities along the normal direction
        self.vx += (impulse * normal_x) / m1
        self.vy += (impulse * normal_y) / m1
        player.vx -= (impulse * normal_x) / m2
        player.vy -= (impulse * normal_y) / m2
        
        self.fix_overlap(player, closest_side)

    
    def check_for_collision_with_block(self):
        for player in self.parent.players:
            if player.player_no != self.player_no:
                if self.x < player.x + player.width and self.x + self.width > player.x and self.y < player.y + player.height and self.y + self.height > player.y:
                    # Get closest side of block
                    closest_side = self.get_closest_side(player)
                    self.energy_transfer(player, closest_side)
                    self.angle += self.angular_velocity / 60
                    if closest_side == "top" or closest_side == "bottom":
                        return True
        return False
                

    def get_location_of_block_from_mouse(self):
        x, y = self.parent.get_mouse_pos()
        return math.sqrt((x - self.x-(self.width/2))**2 + (y - self.y-(self.height/2))**2)

        
    

    def grab(self):
        if pg.mouse.get_pressed()[0]:    
            self.parent.is_grabbing = True
            line_length = self.get_location_of_block_from_mouse()
            if line_length < 150 or self.line:
                self.line = True
                self.air_resistance = 0.99
                pg.draw.line(self.parent.screen, (0, 0, 0), (self.x + self.width/2, self.y + self.height/2), self.parent.get_mouse_pos(), 2)
                if line_length > 150:
                    # Rope behavior based on elasticity
                    stretch_x = (self.x + self.width / 2 - self.parent.get_mouse_pos()[0]) / line_length
                    stretch_y = (self.y + self.height / 2 - self.parent.get_mouse_pos()[1]) / line_length
                    force = (line_length - 150) * self.parent.rope_elasticity
                    self.vx -= force * stretch_x
                    self.vy -= force * stretch_y
                    
            else:
                self.air_resistance = 0.995
        else:
            self.parent.is_grabbing = False
            self.line = False
            self.air_resistance = 0.995

import pygame as pg
import sys
import tkinter as tk
from tkinter import ttk
from threading import Thread

class Game:
    def __init__(self):
        pg.init()
        self.winwidth = 1200
        self.winheight = 700
        self.screen = pg.display.set_mode((self.winwidth, self.winheight))
        pg.display.set_caption("Physics")
        self.clock = pg.time.Clock()
        self.done = False
        self.line = False
        self.creating = False
        self.waitforrelease = False
        self.is_grabbing = False
        self.move_up = False

        # Simulation parameters
        self.rope_elasticity = 0.1
        self.gravity = 0.5
        self.friction = 0.8
        self.air_resistance = 0.995
        self.elasticity = 0.8
        self.rigidness = 0.5

        self.players = [Block(375, 0, 50, 50, self, self.elasticity)]
        self.fancy_players = []

    def open_settings_window(self):
        """
        Opens the settings window using tkinter.
        """
        def update_parameter(param_name, value, entry : tk.Entry):
            """
            Updates the game parameter with the slider/input value.
            """
            setattr(self, param_name, float(value))
            entry.insert(0, str(round(getattr(self, param_name), ndigits=3)))

        def create_slider(parent, label, param_name, from_, to_, resolution):
            """
            Creates a labeled slider for adjusting a parameter.
            """
            frame = tk.Frame(parent)
            frame.pack(fill="x", pady=5)

            entry = tk.Entry(frame, width=8)
            tk.Label(frame, text=label, width=20, anchor="w").pack(side="left", padx=5)
            slider = ttk.Scale(
                frame,
                from_=from_,
                to=to_,
                orient="horizontal",
                length=200,
                command=lambda value, name=param_name: update_parameter(name, value, entry),
            )
            slider.set(getattr(self, param_name))
            slider.pack(side="left", padx=5)

            entry.insert(0, str(round(getattr(self, param_name), ndigits=3)))
            entry.pack(side="left", padx=5)

            def update_from_entry(event):
                try:
                    value = float(entry.get())
                    if value > to_:
                        slider.set(to_)
                    update_parameter(param_name, value, entry)
                except ValueError:
                    entry.delete(0, tk.END)
                    entry.insert(0, str(round(getattr(self, param_name), ndigits=3)))

            entry.bind("<Return>", update_from_entry)

        # Create the tkinter window
        settings_window = tk.Tk()
        settings_window.title("Game Settings")

        # Add sliders for each parameter
        create_slider(settings_window, "Rope Elasticity", "rope_elasticity", 0, 1, 0.01)
        create_slider(settings_window, "Gravity", "gravity", 0, 2, 0.01)
        create_slider(settings_window, "Friction", "friction", 0, 1, 0.01)
        create_slider(settings_window, "Air Resistance", "air_resistance", 0, 1, 0.001)
        create_slider(settings_window, "Elasticity", "elasticity", 0, 1, 0.01)
        create_slider(settings_window, "Rigidness", "rigidness", 0, 1, 0.01)

        settings_window.mainloop()

    def get_mouse_pos(self):
        x, y = pg.mouse.get_pos()
        return x, y
    
    def create_delete_block(self):

        # If just deleated a block
        if self.waitforrelease == True and pg.mouse.get_pressed()[2] == False:
            self.waitforrelease = False
        
        # If not just deleated a block
        elif self.waitforrelease == False:
            if pg.mouse.get_pressed()[2] == True and self.creating == False:
                self.start_position = self.get_mouse_pos()

                # Delete block if mouse on block
                for player in self.players:
                    if player.x < self.start_position[0] < player.x + player.width and player.y < self.start_position[1] < player.y + player.height:
                        self.players.remove(player)
                        self.waitforrelease = True
                        return

                self.creating = True
            # Draw block when right mouse button is released

            elif pg.mouse.get_pressed()[2] == True and self.creating == True:
                self.end_position = self.get_mouse_pos()
                pg.draw.rect(self.screen, (0, 255, 255), (min(self.start_position[0], self.end_position[0]), min(self.start_position[1], self.end_position[1]), abs(self.end_position[0] - self.start_position[0]), abs(self.end_position[1] - self.start_position[1])))
            elif pg.mouse.get_pressed()[2] == False and self.creating == True:
                number = len(self.players)
                if abs(self.end_position[0] - self.start_position[0]) == 0 or abs(self.end_position[1] - self.start_position[1]) == 0:
                    self.end_position = (self.start_position[0] + 50, self.start_position[1] + 50)
                    self.players.append(Block(min(self.start_position[0], self.end_position[0]), min(self.start_position[1], self.end_position[1]), abs(self.end_position[0] - self.start_position[0]), abs(self.end_position[1] - self.start_position[1]), self, self.elasticity, number))
                    self.creating = False
    
    def run(self):
        def run_settings_thread():
            """
            Runs the tkinter settings window in a separate thread.
            """
            Thread(target=self.open_settings_window, daemon=True).start()

        while not self.done:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.done = True
                elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    run_settings_thread()

            self.screen.fill((255, 255, 255))

            self.create_delete_block()
            
            # Fixes block overlap slightly. Better option would be to implement a more robust collision resolution system
            if self.move_up == True:
                for player in self.players:
                    player.y -= 0.01
                self.move_up = False
            
            
            block_distances = self.winwidth + self.winheight
            if self.is_grabbing == False:
                closest_block = None
                for player in self.players:
                    if block_distances > player.get_location_of_block_from_mouse():
                        block_distances = player.get_location_of_block_from_mouse()
                        closest_block = player
            for player in self.players:
                player.update()
                player.draw(self.screen)
                if closest_block == player:
                    player.grab()

            pg.display.flip()
            self.clock.tick(60)

        pg.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()
