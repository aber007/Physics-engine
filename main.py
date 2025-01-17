import pygame as pg
import sys
import math
import os
from rich.console import Console
from pygame.math import Vector2

console = Console()

class Fancy_Block:
    def __init__(self, x, y, width, height, parent=None, elasticity=0.8, player_no=0, rigidness = 0.5):
        self.parent: Game = parent
        self.x = x 
        self.y = y
        self.width = width
        self.height = height
        self.rigidness = rigidness

        self.mass = self.width * self.height
        
        self.ne = Block(x + width, y, 0, 0, self.parent, elasticity, player_no, self)
        self.nw = Block(x, y, 0, 0, self.parent, elasticity, player_no, self)
        self.se = Block(x + width, y + height, 0, 0, self.parent, elasticity, player_no, self)
        self.sw = Block(x, y + height, 0, 0, self.parent, elasticity, player_no, self)
        self.parent.players.append(self.ne)
        self.parent.players.append(self.nw)
        self.parent.players.append(self.se)
        self.parent.players.append(self.sw)

        self.kinetic_energy = 1/2 * self.mass * (self.ne.vx**2 + self.ne.vy**2)
        self.potential_energy = self.mass * self.parent.gravity * self.y

        self.angular_velocity = 0
        self.moment_of_inertia = (1 / 12) * self.mass * (self.width**2 + self.height**2)
        self.angle = 0



    def draw(self, screen):
        # Enforce distance constraints between sub-blocks
        self.rigidness = self.parent.rigidness
        
        self.force_distance_between()
        self.update_position()

        # Update the positions of each block
        self.ne.update(True, self.nw, self.se, self.width, self.height)
        self.nw.update(True, self.ne, self.sw, self.width, self.height)
        self.se.update(True, self.sw, self.ne, self.width, self.height)
        self.sw.update(True, self.se, self.nw, self.width, self.height)


        pg.draw.polygon(screen, (0, 128, 255), [(self.nw.x, self.nw.y), (self.ne.x, self.ne.y), (self.se.x, self.se.y), (self.sw.x, self.sw.y)])




    def update_position(self):
        """
        Updates the Fancy_Block's position based on the average position of its sub-blocks.
        """
        self.x = (self.nw.x + self.ne.x + self.sw.x + self.se.x) / 4
        self.y = (self.nw.y + self.ne.y + self.sw.y + self.se.y) / 4

        
        

    
    def force_distance_between(self):
        """
        Enforces the correct distances between the sub-blocks to maintain the square.
        """
        # Define the pairs of blocks and the expected distances
        pairs = [
            (self.nw, self.ne, self.width),  # Top edge
            (self.nw, self.sw, self.height),  # Left edge
            (self.ne, self.se, self.height),  # Right edge
            (self.sw, self.se, self.width),  # Bottom edge
            (self.nw, self.se, math.sqrt(self.width**2 + self.height**2)),  # Diagonal
            (self.ne, self.sw, math.sqrt(self.width**2 + self.height**2)),  # Diagonal
        ]

        for block1, block2, target_distance in pairs:
            # Calculate the current distance between the blocks
            dx = block2.x - block1.x
            dy = block2.y - block1.y
            current_distance = math.sqrt(dx**2 + dy**2)

            # Skip if the blocks are already at the correct distance
            if current_distance == 0 or current_distance == target_distance:
                continue

            # Calculate the correction needed
            correction = (current_distance - target_distance) / 2
            correction_dx = correction * (dx / current_distance)
            correction_dy = correction * (dy / current_distance)

            # Apply corrections symmetrically to the blocks
            block1.x += correction_dx
            block1.y += correction_dy
            block2.x -= correction_dx
            block2.y -= correction_dy

            # Adjust velocities to match the correction (damping effect)

            block1.vx += correction_dx * self.rigidness
            block1.vy += correction_dy * self.rigidness
            block2.vx -= correction_dx * self.rigidness
            block2.vy -= correction_dy * self.rigidness







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

        self.fancy_parent : Fancy_Block = fancy_parent

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

    def get_hitbox(self):
        def get_top_corner():
            return max(self.fancy_parent.ne.y, self.fancy_parent.nw.y, self.fancy_parent.se.y, self.fancy_parent.sw.y)

        def drawhitbox(x1, y1, x2, y2, screen_width, screen_height):
            # Calculate the slope
            if x1 == x2:  # Vertical line
                return [(x1, 0), (x1, screen_height)]
            elif y1 == y2:  # Horizontal line
                return [(0, y1), (screen_width, y1)]
            
            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - slope * x1
            
            # Calculate intersections with screen edges
            points = []
            # Intersection with left (x=0)
            points.append((0, intercept))
            # Intersection with right (x=screen_width)
            points.append((screen_width, slope * screen_width + intercept))
            # Intersection with top (y=0)
            points.append((-intercept / slope, 0))
            # Intersection with bottom (y=screen_height)
            points.append(((screen_height - intercept) / slope, screen_height))
            
            # Filter points within screen boundaries
            valid_points = [
                (x, y) for x, y in points
                if 0 <= x <= screen_width and 0 <= y <= screen_height
            ]
            
            return valid_points
        
        def get_within_hitbox(x1, y1, x2, y2, current_pos):
            """
            Returns the function of the line passing through two points in slope-intercept form y = mx + c
            or x = k for vertical lines.
            """
            if x1 == x2:  # Vertical line
                return 1000
            elif y1 == y2:  # Horizontal line
                return y1
            else:
                # Calculate slope (m) and y-intercept (c)
                slope = (y2 - y1) / (x2 - x1)
                intercept = y1 - slope * x1
                return float(slope*current_pos + intercept)

        top_corner = get_top_corner()
        eq1 = float(get_within_hitbox(self.fancy_parent.ne.x, self.fancy_parent.ne.y, self.fancy_parent.nw.x, self.fancy_parent.nw.y, self.x))
        eq2 = float(get_within_hitbox(self.fancy_parent.ne.x, self.fancy_parent.ne.y, self.fancy_parent.se.x, self.fancy_parent.se.y, self.x))
        eq3 = float(get_within_hitbox(self.fancy_parent.sw.x, self.fancy_parent.sw.y, self.fancy_parent.nw.x, self.fancy_parent.nw.y, self.x))
        eq4 = float(get_within_hitbox(self.fancy_parent.sw.x, self.fancy_parent.sw.y, self.fancy_parent.se.x, self.fancy_parent.se.y, self.x))
        
        
        def handle_collision():
            print("Collision")
            
        
        for block in self.parent.players:
            if block in [self.fancy_parent.nw, self.fancy_parent.ne, self.fancy_parent.sw, self.fancy_parent.se]:
                continue
            if top_corner == self.fancy_parent.ne.y:
                if (block.y <= eq1 and block.y <= eq2 and block.y >= eq3 and block.y >= eq4 and
                    self.fancy_parent.nw.x <= block.x <= self.fancy_parent.ne.x):
                    handle_collision()
            if top_corner == self.fancy_parent.nw.y:
                if (block.y <= eq1 and block.y <= eq3 and block.y >= eq2 and block.y >= eq4 and
                    self.fancy_parent.nw.x <= block.x <= self.fancy_parent.ne.x):
                    handle_collision()
            if top_corner == self.fancy_parent.se.y:
                if (block.y <= eq2 and block.y <= eq4 and block.y >= eq1 and block.y >= eq3 and
                    self.fancy_parent.sw.x <= block.x <= self.fancy_parent.se.x):
                    handle_collision()
            if top_corner == self.fancy_parent.sw.y:
                if (block.y <= eq3 and block.y <= eq4 and block.y >= eq1 and block.y >= eq2 and
                    self.fancy_parent.sw.x <= block.x <= self.fancy_parent.se.x):
                    handle_collision()


    
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
        if fancy:
            self.get_hitbox()

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
                for player in self.fancy_players:
                    if player.x < self.start_position[0] < player.x + player.width and player.y < self.start_position[1] < player.y + player.height:
                        self.fancy_players.remove(player)
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

                if pg.key.get_pressed()[pg.K_LSHIFT]:
                    self.fancy_players.append(Fancy_Block(min(self.start_position[0], self.end_position[0]), min(self.start_position[1], self.end_position[1]), abs(self.end_position[0] - self.start_position[0]), abs(self.end_position[1] - self.start_position[1]), self, self.elasticity, number))
                else:
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
            for fancy_block in self.fancy_players:
                fancy_block.draw(self.screen)

            pg.display.flip()
            self.clock.tick(60)

        pg.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()
