import pygame as pg
import sys
import math
import os
from rich.console import Console

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

    def get_velocity(self):
        """
        Calculates the average velocity of the Fancy_Block based on its corners.
        """
        corners = [self.nw, self.ne, self.se, self.sw]
        avg_vx = sum(corner.vx for corner in corners) / 4
        avg_vy = sum(corner.vy for corner in corners) / 4
        return avg_vx, avg_vy


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

    def apply_impulse(self, dvx, dvy):
        """
        Applies a change in velocity to the Fancy_Block and its corners.
        """
        for corner in [self.nw, self.ne, self.se, self.sw]:
            corner.vx += dvx
            corner.vy += dvy

    def adjust_position(self, dx, dy):
        """
        Adjusts the position of the Fancy_Block and its corners.
        """
        self.x += dx
        self.y += dy
        for corner in [self.nw, self.ne, self.se, self.sw]:
            corner.x += dx
            corner.y += dy

    
    def handle_collision_response(self, collision_point, collision_normal, other, min_overlap):
        """
        Handles the collision response, ensuring blocks don't accelerate into each other.
        """
        # Calculate relative velocity at the collision point
        self_vx, self_vy = self.get_velocity()
        other_vx, other_vy = other.get_velocity()

        relative_velocity = (other_vx - self_vx) * collision_normal[0] + (other_vy - self_vy) * collision_normal[1]

        if relative_velocity > 0:
            # No collision response if the blocks are separating
            return

        # Calculate the overlap distance (optional)
        overlap_distance = min_overlap or 0

        # Separate the blocks to resolve the overlap
        total_mass = self.mass + other.mass
        self_correction = overlap_distance * (other.mass / total_mass)
        other_correction = overlap_distance * (self.mass / total_mass)
        
        self.adjust_position(-collision_normal[0] * self_correction, -collision_normal[1] * self_correction)
        other.adjust_position(collision_normal[0] * other_correction, collision_normal[1] * other_correction)

        # Calculate the impulse scalar
        restitution = min(self.parent.elasticity, other.parent.elasticity)  # Use the lower elasticity
        impulse = -(1 + restitution) * relative_velocity
        impulse /= (1 / self.mass + 1 / other.mass)

        # Apply impulse to the blocks
        impulse_vector = (impulse * collision_normal[0], impulse * collision_normal[1])
        
        self.apply_impulse(-impulse_vector[0] / self.mass, -impulse_vector[1] / self.mass)
        other.apply_impulse(impulse_vector[0] / other.mass, impulse_vector[1] / other.mass)




    def update_position(self):
        """
        Updates the Fancy_Block's position based on the average position of its sub-blocks.
        """
        self.x = (self.nw.x + self.ne.x + self.sw.x + self.se.x) / 4
        self.y = (self.nw.y + self.ne.y + self.sw.y + self.se.y) / 4

        for block in self.parent.fancy_players:
            if block != self:
                if self.detect_collision(block):
                    pass
        

        
        


        
        

    
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

    def project(self, axis):
            """
            Projects the Fancy_Block onto an axis for the Separating Axis Theorem.
            Returns the min and max projections.
            """
            points = [
                (self.nw.x, self.nw.y),
                (self.ne.x, self.ne.y),
                (self.se.x, self.se.y),
                (self.sw.x, self.sw.y),
            ]
            # Dot product to project points onto the axis
            projections = [(point[0] * axis[0] + point[1] * axis[1]) for point in points]
            return min(projections), max(projections)

    def get_axes(self):
        """
        Returns the axes perpendicular to each edge of the Fancy_Block.
        """
        points = [
            (self.nw.x, self.nw.y),
            (self.ne.x, self.ne.y),
            (self.se.x, self.se.y),
            (self.sw.x, self.sw.y),
        ]
        axes = []
        for i in range(len(points)):
            # Get edge vector
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            edge = (p2[0] - p1[0], p2[1] - p1[1])
            # Get perpendicular vector
            axis = (-edge[1], edge[0])  # Rotate 90 degrees
            # Normalize the axis
            length = (axis[0]**2 + axis[1]**2)**0.5
            axes.append((axis[0] / length, axis[1] / length))
        return axes
    
    def find_collision_point(self, axis, other):
        """
        Finds the collision point and corner along the given axis.
        """
        # Project all corners of both blocks onto the axis
        self_points = [
            (self.nw.x, self.nw.y),
            (self.ne.x, self.ne.y),
            (self.se.x, self.se.y),
            (self.sw.x, self.sw.y),
        ]
        other_points = [
            (other.nw.x, other.nw.y),
            (other.ne.x, other.ne.y),
            (other.se.x, other.se.y),
            (other.sw.x, other.sw.y),
        ]

        # Calculate projections for each corner
        projections = []
        for point in self_points:
            proj = point[0] * axis[0] + point[1] * axis[1]
            projections.append((proj, point))
        for point in other_points:
            proj = point[0] * axis[0] + point[1] * axis[1]
            projections.append((proj, point))

        # Sort projections to find the closest points
        projections.sort(key=lambda x: x[0])

        # Collision point is the overlap between the closest points
        collision_point = projections[0][1]  # The point on the edge of overlap
        collision_corner = projections[0][1]  # This is the corner causing collision

        return collision_point, collision_corner


    def detect_collision(self, other):
        """
        Detects collision between this Fancy_Block and another Fancy_Block using SAT.
        Returns:
        - (collision: bool, collision_point: tuple, collision_corner: tuple or None)
        """
        axes = self.get_axes() + other.get_axes()  # Combine axes from both blocks

        min_overlap = float("inf")
        collision_axis = None
        collision_corner = None

        for axis in axes:
            # Get projections for both blocks
            min_a, max_a = self.project(axis)
            min_b, max_b = other.project(axis)

            # Check for overlap
            if max_a < min_b or max_b < min_a:
                # No overlap on this axis, no collision
                return False, None, None

            # Calculate overlap distance
            overlap = min(max_a, max_b) - max(min_a, min_b)
            if overlap < min_overlap:
                min_overlap = overlap
                collision_axis = axis

        # Find the collision point (if collision detected)
        collision_point = self.find_collision_point(collision_axis, other)

        # Handle collision response
        self.handle_collision_response(collision_point, collision_axis, other, min_overlap)

        return True

    
        






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

    def Seperating_Axis_Theorem(self):
        for idx, player in enumerate(self.fancy_players):
            if idx == 0:
                color = (255, 0, 0)
            else:
                color = (0, 255, 0)
            for side in ["N", "E", "S", "W"]:
                if side == "N":
                    axis = (0, -1)
                    player.project(axis, color)
                elif side == "E":
                    axis = (1, 0)
                    player.project(axis, color)
                elif side == "S":
                    axis = (0, 1)
                    player.project(axis, color)
                elif side == "W":
                    axis = (-1, 0)
                    player.project(axis, color)
        
    
    
    
    
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
            for player in self.fancy_players:
                player.draw(self.screen)


            pg.display.flip()
            self.clock.tick(60)

        pg.quit()
        sys.exit()

if __name__ == "__main__":
    Game().run()
