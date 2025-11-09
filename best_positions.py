
import pandas as pd
import numpy as np
import random
import copy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
from pandas._config.config import pp_options_list
import os
import scipy.ndimage

class object:
    def __init__(self, shape, position=(0,0)):
        self.shape = shape
        self.position = position

    def rotate(self):
        self.shape = (self.shape[1], self.shape[0])
        return self

    def get_shape(self):
        return self.shape

class plate:
    def __init__(self, shape, resolution=1000):
        # shape is a tuple of width and height
        self.shape = shape
        self.resolution = resolution
        self.plate = np.zeros((int(self.shape[0]*self.resolution), int(self.shape[1]*self.resolution)), dtype=int)
        self.objects = [] # has only the object coords. objects are recognized by position

    def check_if_object_fits(self, object, position):
        # Calculate the area where the object will be placed
        x_start = int(position[0] * self.resolution)
        y_start = int(position[1] * self.resolution)
        x_end = int(x_start + object.get_shape()[0] * self.resolution)
        y_end = int(y_start + object.get_shape()[1] * self.resolution)
        
        # Check if the position is within plate bounds
        if x_start < 0 or y_start < 0:
            return False
        if x_end > self.plate.shape[0] or y_end > self.plate.shape[1]:
            return False
        
        # Check if the area is already occupied (any value is 1)
        area = self.plate[x_start:x_end, y_start:y_end]
        return np.all(area == 0)
    
    def place_object(self, object, position):
        # position is a tuple of x and y coordinates

        if not self.check_if_object_fits(object, position):
            return False

        # Calculate the area where the object will be placed
        x_start = int(position[0] * self.resolution)
        y_start = int(position[1] * self.resolution)
        x_end = int(x_start + object.get_shape()[0] * self.resolution)
        y_end = int(y_start + object.get_shape()[1] * self.resolution)
        
        # Place the object using NumPy array slicing
        self.plate[x_start:x_end, y_start:y_end] = 1
        # Update object position to match the placement
        object.position = position
        self.objects.append(object)
        return True

    def get_plate(self):
        return self.plate
    
    def print_plate(self):
        df = pd.DataFrame(self.plate)
        print(df.to_string(index=False, header=False))
    
    def show_plot(self, fig, ax, gen=None): 
        """Update an existing matplotlib plot and save it to a file silently."""
        
        # 1. Clear the contents of the existing axis
        ax.clear() 

        # --- Setup (remains the same) ---
        plate_height = self.shape[0] 
        plate_width = self.shape[1] if len(self.shape) > 1 else self.shape[0]

        ax.set_xlim(-0.5, plate_width + 0.5)
        ax.set_ylim(-0.5, plate_height + 0.5)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, which='both')
        ax.set_xlabel('Width (X)', fontsize=12)
        ax.set_ylabel('Height (Y)', fontsize=12)
        ax.set_title(f'Plate Layout ({plate_width} × {plate_height}) - {len(self.objects)} objects placed{f" - generation {gen}" if gen else ""}', 
                    fontsize=14, fontweight='bold')
        
        # Draw the plate boundary
        plate_rect = patches.Rectangle((0, 0), plate_width, plate_height, 
                                    linewidth=3, edgecolor='black', 
                                    facecolor='lightgray', alpha=0.15, zorder=0)
        ax.add_patch(plate_rect)
        
        # --- Drawing Logic (remains the same) ---
        if len(self.objects) > 0:
            colors = plt.cm.Set3(np.linspace(0, 1, len(self.objects)))
        else:
            colors = []
            ax.text(plate_width/2, plate_height/2, 'No objects placed', 
                    ha='center', va='center', fontsize=14, style='italic', alpha=0.5)
        
        # ... (rest of the object drawing loop) ...
        for i, obj in enumerate(self.objects):
            pos = obj.position
            shape = obj.get_shape()
            plot_x = pos[1] 
            plot_y = pos[0] 
            obj_width = shape[1] 
            obj_height = shape[0]
            
            # Draw rectangle for the object
            obj_rect = patches.Rectangle((plot_x, plot_y), obj_width, obj_height,
                                        linewidth=2.5, edgecolor='black',
                                        facecolor=colors[i % len(colors)],
                                        alpha=0.7, zorder=2,
                                        label=f'Obj {i+1}: {shape[0]}×{shape[1]}')
            ax.add_patch(obj_rect)
            
            # Add text label
            center_x = plot_x + obj_width / 2
            center_y = plot_y + obj_height / 2
            ax.text(center_x, center_y, f'{shape[0]}×{shape[1]}', 
                    ha='center', va='center', fontsize=10, fontweight='bold',
                    color='black', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor='black', alpha=0.8, linewidth=1))
            
        # Add legend
        if len(self.objects) > 0 and len(self.objects) < 10:
            ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9, 
                    framealpha=0.9, title='Objects')
            
        # Set major/minor ticks
        ax.set_xticks(np.arange(0, plate_width + 1, max(1, plate_width // 10)))
        ax.set_yticks(np.arange(0, plate_height + 1, max(1, plate_height // 10)))
        ax.set_xticks(np.arange(0, plate_width + 1, 1), minor=True)
        ax.set_yticks(np.arange(0, plate_height + 1, 1), minor=True)
        
        # Invert y-axis
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        # --- SAVE THE FIGURE ---
        filename = f"plate_layout_gen_{gen:04d}.png" if gen is not None else "plate_layout_final.png"
        fig.savefig(filename, dpi=100, bbox_inches='tight') # Saves the plot to file!
        # -----------------------

        # Remove all interactive drawing/pausing commands (they are unnecessary with 'Agg')
        # fig.canvas.draw()
        # fig.canvas.flush_events() 
        # plt.pause(0.001)

    # Now every time you call show_plot, a file is saved, but no window opens.
    
    def reset(self):
        """Reset the plate to empty state"""
        self.plate = np.zeros((self.shape[0]*self.resolution, self.shape[1]*self.resolution), dtype=int)
        self.objects = []
    
    def get_unusable_area(self, min_object_shape):
        """Calculate unusable area (areas too small to fit the minimum object size)"""
        # This is a simplified version - counts empty spaces that are too small
        # For a more accurate calculation, we'd need to check all possible placements
        total_area = self.plate.size
        used_area = np.sum(self.plate == 1)
        empty_area = total_area - used_area
        
        # Calculate minimum object area in resolution units
        min_area = min_object_shape[0] * min_object_shape[1] * self.resolution * self.resolution
        
        # Simplified: unusable area is empty area that's less than min_area
        # This is an approximation - in reality we'd need to check each empty region
        return empty_area  # For now, return all empty area as potentially unusable
    
    def copy_plate(self):
        """Create a deep copy of the plate"""
        new_plate = plate(self.shape, self.resolution)
        new_plate.plate = self.plate.copy()
        new_plate.objects = copy.deepcopy(self.objects)
        return new_plate



def try_fit(plate_shape, objects_to_place, resolution=1, generations=50, individual_per_generation=100, w1=1, w2=2, mutation_rate=0.1, crossover_rate=0.7):
    """
    Genetic algorithm to find optimal placement of objects on a plate.
    
    Args:
        plate_shape: Tuple (width, height) of the plate
        objects_to_place: List of object shapes (tuples) to place on the plate
        resolution: Resolution for the plate grid (each unit in plate_shape is divided into resolution cells)
        generations: Number of generations to evolve
        individual_per_generation: Number of individuals per generation
        w1: Weight for shapes placed term
        w2: Weight for unusable area term
        mutation_rate: Probability of mutation
        crossover_rate: Probability of crossover
    """
    # Check for excessive memory usage
    array_size = plate_shape[0] * resolution * plate_shape[1] * resolution
    memory_mb = (array_size * 4) / (1024 * 1024)  # int32 = 4 bytes
    if memory_mb > 100:  # Warn if single array would be > 100 MB
        raise ValueError(f"Resolution {resolution} with plate_shape {plate_shape} would create an array of {array_size:,} elements ({memory_mb:.1f} MB). This is too large and will cause memory errors. Please use resolution=1 for most cases, or reduce the plate size.")
    
    if resolution > 100:
        print(f"Warning: High resolution ({resolution}) will create large arrays. Consider using resolution=1 for testing.")
    
    def create_individual(objects_to_place, plate_shape, resolution):
        """Create a random individual (configuration of objects)"""
        p = plate(plate_shape, resolution)
        placements = []
        
        # Shuffle objects to try placing them in random order
        shuffled_objects = objects_to_place.copy()
        random.shuffle(shuffled_objects)
        tried = 80
        while tried > 0:
            place = (random.random()*plate_shape[0], random.random()*plate_shape[1])
            obj = object(objects_to_place[0])
            rotated = 0
            if p.check_if_object_fits(obj, place):
                p.place_object(obj, place)
                placements.append((objects_to_place[0], rotated, place))
            elif p.check_if_object_fits(obj.rotate(), place):
                p.place_object(obj.rotate(), place)
                rotated = 1
                placements.append((objects_to_place[0], rotated, place))
            else:
                tried -= 1
            
        
        return placements, p
        # placements.append((obj_shape, rotated, (x, y)))
    def create_side_by_side_individual(objects_to_place, plate_shape, resolution, strategy_index, max_random_tries=40):
        """
        Creates an individual by greedily placing multiple instances of the available shapes
        side-by-side, using deterministic placement, and falling back to random tries when blocked.

        :param objects_to_place: A list of available prototype Object instances (the shapes).
        :param plate_shape: Tuple (height, width).
        :param resolution: Plate resolution multiplier.
        :param strategy_index: Determines initial object orientation (0=original, 1=rotated).
        :param max_random_tries: Max attempts to place randomly after deterministic placement fails.
        :return: A list of successful placements and the final Plate instance.
        """
        
        plate_instance = plate(plate_shape, resolution)
        placements = []
        
        current_x = 0  # X-coordinate (width, horizontal)
        current_y = 0  # Y-coordinate (height, vertical)
        max_height_in_row = 0
        
        orientation_strategy = strategy_index % 2
        
        random_tries_count = 0
        total_objects_placed = 0

        while True:
            
            # --- 1. DETERMINE OBJECT TO PLACE ---
            prototype_obj = object(random.choice(objects_to_place))
            original_shape = prototype_obj.get_shape() # Capture the original, unrotated shape
            
            current_obj = object(copy.deepcopy(original_shape)) # Use the shape tuple for construction
            
            rotated_status = 0
            orientation_strategy = strategy_index % 2
            
            # Apply the rotation based on the strategy
            if orientation_strategy == 1:
                current_obj.rotate() 
                rotated_status = 1 # Mark as rotated 

            obj_height, obj_width = current_obj.get_shape()

            
            # --- 2. CALCULATE PLACEMENT POSITION (Side-by-Side/Nesting Logic) ---

            # Check for row overflow
            if (current_x + obj_width) > plate_shape[1]:
                # Move to the next "row"
                current_x = 0
                current_y += max_height_in_row
                max_height_in_row = 0
            
            # Check for plate height overflow (cannot place even starting a new row)
            if (current_y + obj_height) > plate_shape[0]:
                # Deterministic placement is blocked! Fall through to random tries.
                position = None 
            else:
                # Deterministic placement position: Top-Left corner of the next available slot
                position = (current_y, current_x) # (Y, X) coordinate order


            # --- 3. ATTEMPT PLACEMENT ---
            
            placement_successful = False
            
            if position is not None and plate_instance.check_if_object_fits(current_obj, position):
                # Deterministic placement succeeded
                plate_instance.place_object(current_obj, position)
                
                # Update position trackers for the next object
                current_x += obj_width
                max_height_in_row = max(max_height_in_row, obj_height)
                
                placement_successful = True
                random_tries_count = 0 # Reset random counter on success
                total_objects_placed += 1
                
            else:
                # --- 4. DETERMINE BLOCKAGE AND FALLBACK ---
                
                if random_tries_count >= max_random_tries:
                    # If random tries max out, the plate is likely full or impossible to fill further
                    # 
                    print(f"Blocked! Exceeded {max_random_tries} random tries. Stopping packing.")
                    break
                    
                # Deterministic placement failed (either due to overflow or collision/misalignment)
                random_tries_count += 1
                
                # Try a random position instead (within bounds)
                # Find max valid Y and X coordinates for this object
                max_y = plate_shape[0] - obj_height
                max_x = plate_shape[1] - obj_width
                
                if max_y >= 0 and max_x >= 0:
                    random_y = random.uniform(0, max_y)
                    random_x = random.uniform(0, max_x)
                    random_position = (random_y, random_x)
                    
                    if plate_instance.place_object(current_obj, random_position):
                        placement_successful = True
                        random_tries_count = 0 # Reset random counter on success
                        total_objects_placed += 1
                    # If random placement fails, loop continues and random_tries_count increments
                
                # Reset deterministic trackers if we failed to place randomly as well
                if not placement_successful:
                    current_x = 0 # Force attempt to start a new row next time
                    current_y += max_height_in_row if max_height_in_row > 0 else 1 # Move down slightly
                    max_height_in_row = 0
                    
            if placement_successful:
                # 🚨 FIX HERE: Append the standardized 3-element tuple
                placements.append((original_shape, rotated_status, current_obj.position))
                
        # Final check: If no objects were placed at all, it's a failed individual.
        if total_objects_placed == 0:
            print("Warning: Failed to place any objects during initialization.")

        return placements, plate_instance
    def calculate_fitness(placements, plate_instance, objects_to_place, plate_shape, resolution, w1, w2):
        """Calculate fitness: w1 × (shapes placed / max possible) - w2 × (unusable area / total area)"""
        
        shapes_placed = len(placements)
        max_possible = len(objects_to_place)
        
        # Calculate total area
        total_area = plate_shape[0] * plate_shape[1] * resolution * resolution
        
        # Calculate unusable area by checking each cell
        unusable_area = calculate_unusable_area(plate_instance, objects_to_place, plate_shape, resolution)
        
        # Calculate fitness
        if max_possible == 0:
            shapes_ratio = 0
        else:
            shapes_ratio = shapes_placed / max_possible
        
        unusable_ratio = unusable_area / total_area if total_area > 0 else 0
        
        fitness = w1 * shapes_ratio - w2 * unusable_ratio
        return fitness
    
    def calculate_unusable_area(plate_instance, objects_to_place, plate_shape, resolution):
        """Improved: scan for contiguous empty regions, count those too small/irregular to fit any shape."""
        # 1 = occupied, 0 = empty in plate grid
        plate_grid = plate_instance.get_plate()
        min_shape = objects_to_place[0]
        min_w, min_h = min_shape  # dimensions in units
        min_w_pix = int(min_w * resolution)
        min_h_pix = int(min_h * resolution)

        # Label contiguous empty regions using connected-component analysis
        empty_mask = (plate_grid == 0)
        labeled_regions, num_fragments = scipy.ndimage.label(empty_mask)
        unusable_area = 0

        # For each empty region (fragment), evaluate if any placement of the shape fits
        for label in range(1, num_fragments+1):
            fragment_mask = (labeled_regions == label)
            coords = np.argwhere(fragment_mask)
            if coords.size == 0:
                continue
            min_x, min_y = coords.min(axis=0)
            max_x, max_y = coords.max(axis=0)
            frag_w = max_x - min_x + 1
            frag_h = max_y - min_y + 1
            frag_area = fragment_mask.sum()

            # Check if any shape (any rotation) fits: fits if fragment's width >= min_w_pix and height >= min_h_pix (or reversed for rotation)
            fits_normal = (frag_w >= min_w_pix and frag_h >= min_h_pix)
            fits_rotated = (frag_w >= min_h_pix and frag_h >= min_w_pix)
            if not (fits_normal or fits_rotated):
                unusable_area += frag_area  # fragment is too small for any shape in any orientation
        return unusable_area
    
    def crossover(parent1, parent2, plate_shape, resolution):
        """Crossover two parents to create two children"""
        # Take placements from both parents, avoiding overlaps
        child1_placements = []
        child2_placements = []
        
        p1 = plate(plate_shape, resolution)
        p2 = plate(plate_shape, resolution)
        
        # Alternate between parents for child1
        for placement in parent1:
            # 🚨 This line is now correct if the inputs are standardized:
            obj_shape_proto, rotated, pos = placement 
            
            # Determine the orientation for the object instance
            orientation = (obj_shape_proto[1], obj_shape_proto[0]) if rotated else obj_shape_proto
            obj = object(orientation, pos)
            
            if p1.place_object(obj, pos):
                child1_placements.append(placement)
        
        for placement in parent2:
            obj_shape, rotated, pos = placement
            orientation = (obj_shape[1], obj_shape[0]) if rotated else obj_shape
            obj = object(orientation, pos)
            if p1.place_object(obj, pos):
                child1_placements.append(placement)
        
        # Alternate between parents for child2 (reverse order)
        for placement in parent2:
            obj_shape, rotated, pos = placement
            orientation = (obj_shape[1], obj_shape[0]) if rotated else obj_shape
            obj = object(orientation, pos)
            if p2.place_object(obj, pos):
                child2_placements.append(placement)
        
        for placement in parent1:
            obj_shape, rotated, pos = placement
            orientation = (obj_shape[1], obj_shape[0]) if rotated else obj_shape
            obj = object(orientation, pos)
            if p2.place_object(obj, pos):
                child2_placements.append(placement)
        
        return child1_placements, child2_placements
    
    def mutate(placements, objects_to_place, plate_shape, resolution, mutation_rate):
        """Mutate an individual"""
        mutated = plate(plate_shape, resolution)
        new_placements = []
        
        # First, try to keep existing placements (with some probability of removal/movement)
        for placement in placements:
            if random.random() < mutation_rate / 2:
                # Remove this placement (mutation by removal)
                continue
            
            obj_shape_proto, rotated_status, pos = placement
            orientation = (obj_shape_proto[1], obj_shape_proto[0]) if rotated_status else obj_shape_proto
            
            # Try to place at original position
            obj = object(orientation, pos)
            if mutated.place_object(obj, pos):
                new_placements.append(placement)
            elif random.random() < mutation_rate:
                # Try random new position
                max_x = plate_shape[0] - orientation[0]
                max_y = plate_shape[1] - orientation[1]
                
                if max_x >= 0 and max_y >= 0:
                    for _ in range(10):
                        x = random.random()*max_x
                        y = random.random()*max_y
                        obj = object(orientation, (x, y))
                        if mutated.place_object(obj, (x, y)):
                            # 🚨 FIX HERE: Append the original shape, rotated status, and new position
                            new_placements.append((obj_shape_proto, rotated_status, (x, y)))
                            break
        
        # Try to add more objects (allows duplicates)
        # Try adding a few random objects from objects_to_place
        objects_to_try = objects_to_place.copy()
        random.shuffle(objects_to_try)
        
        # Try to add up to a few objects
        max_add_attempts = min(5, len(objects_to_try))
        for obj_shape in objects_to_try[:max_add_attempts]:
            if random.random() < mutation_rate:
                # Try to add this object
                orientations = [obj_shape, (obj_shape[1], obj_shape[0])]
                random.shuffle(orientations)
                
                for orientation in orientations:
                    max_x = plate_shape[0] - orientation[0]
                    max_y = plate_shape[1] - orientation[1]
                    
                    if max_x < 0 or max_y < 0:
                        continue
                    
                    for _ in range(20):
                        x = random.random()*max_x
                        y = random.random()*max_y
                        obj = object(orientation, (x, y))
                        if mutated.place_object(obj, (x, y)):
                            rotated = 1 if orientation == (obj_shape[1], obj_shape[0]) else 0
                            # 🚨 FIX HERE: Append the original shape, new rotated status, and position
                            new_placements.append((obj_shape_proto, rotated_status, (x, y)))
                            break
                    else:
                        continue
                    break  # Successfully placed, move to next object
        
        return new_placements, mutated
    
    def tournament_selection(population_with_fitness, tournament_size=5):
        """Select an individual using tournament selection"""
        tournament = random.sample(population_with_fitness, min(tournament_size, len(population_with_fitness)))
        return max(tournament, key=lambda x: x[2])  # Return individual with highest fitness (index 2 is fitness)
    
    # Initialize population

    plt.ion() 
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    print(f"Initializing population of {individual_per_generation} individuals...")
    population = []
    
    # --- PHASE 1: RANDOM INITIALIZATION (The bulk) ---
    num_random = individual_per_generation - 20
    for i in range(num_random):
        placements, plate_instance = create_individual(objects_to_place, plate_shape, resolution)
        # print(len(placements))
        fitness = calculate_fitness(placements, plate_instance, objects_to_place, plate_shape, resolution, w1, w2)
        population.append((placements, plate_instance, fitness))
        if (i + 1) % 20 == 0:
             # Use the correct total number for accurate printing
            print(f"Created {i + 1}/{num_random} random individuals")
            
    # --- PHASE 2: DETERMINISTIC INITIALIZATION (The last 20) ---
    print("\nCreating 20 deterministic individuals (edge cases)...")
    num_deterministic = 20
    
    # Example deterministic strategies (you might define more):
    # Strategy 0: Place objects in original orientation (Horizontal focus)
    # Strategy 1: Place objects in rotated orientation (Vertical focus)
    # Strategy 2: Place objects in original orientation starting from a different corner (e.g., bottom-left)
    # Strategy 3: Place objects in rotated orientation starting from a different corner (e.g., bottom-left)
    
    # We will loop through a few different strategies for diversity
    
    for i in range(num_deterministic):
        # Use modulo to cycle through a few different placement strategies
        strategy_index = i % 4
        
        placements, plate_instance = create_side_by_side_individual(objects_to_place, plate_shape, resolution, strategy_index)
        # Recalculate fitness based on the new placements
        fitness = calculate_fitness(placements, plate_instance, objects_to_place, plate_shape, resolution, w1, w2)
        population.append((placements, plate_instance, fitness))

        print(f"Created {i + 1}/{num_deterministic} deterministic individuals (Strategy {strategy_index})")

    print(f"\nPopulation initialization complete. Total individuals: {len(population)}")
    
    # Evolution loop
    next = False
    for generation in range(generations):
        # Sort by fitness (descending)
        population.sort(key=lambda x: x[2], reverse=True)
        best_fitness = population[0][2]
        best_placements = population[0][0]
        best_plate = population[0][1]
        
        print(f"Generation {generation + 1}/{generations} - Best fitness: {best_fitness:.4f}, Shapes placed: {len(best_placements)}")
        
        # Create new population
        new_population = []
        
        # Keep top 10% (elitism)
        elite_size = max(1, individual_per_generation // 10)
        new_population.extend(population[:elite_size])
        
        # Generate rest of population through crossover and mutation
        while len(new_population) < individual_per_generation:
            if random.random() < crossover_rate and len(population) >= 2:
                # Crossover
                parent1 = tournament_selection(population)
                parent2 = tournament_selection(population)
                child1_placements, child2_placements = crossover(parent1[0], parent2[0], plate_shape, resolution)
                
                # Create plate instances for children
                p1 = plate(plate_shape, resolution)
                p2 = plate(plate_shape, resolution)
                for placement in child1_placements:
                    obj_shape, rotated, pos = placement
                    orientation = (obj_shape[1], obj_shape[0]) if rotated else obj_shape
                    p1.place_object(object(orientation, pos), pos)
                for placement in child2_placements:
                    obj_shape, rotated, pos = placement
                    orientation = (obj_shape[1], obj_shape[0]) if rotated else obj_shape
                    p2.place_object(object(orientation, pos), pos)
                
                # Mutate children
                child1_placements, p1 = mutate(child1_placements, objects_to_place, plate_shape, resolution, mutation_rate)
                child2_placements, p2 = mutate(child2_placements, objects_to_place, plate_shape, resolution, mutation_rate)
                
                fitness1 = calculate_fitness(child1_placements, p1, objects_to_place, plate_shape, resolution, w1, w2)
                fitness2 = calculate_fitness(child2_placements, p2, objects_to_place, plate_shape, resolution, w1, w2)
                
                new_population.append((child1_placements, p1, fitness1))
                if len(new_population) < individual_per_generation:
                    new_population.append((child2_placements, p2, fitness2))
            else:
                # Mutation only
                parent = tournament_selection(population)
                mutated_placements, mutated_plate = mutate(parent[0], objects_to_place, plate_shape, resolution, mutation_rate)
                fitness = calculate_fitness(mutated_placements, mutated_plate, objects_to_place, plate_shape, resolution, w1, w2)
                new_population.append((mutated_placements, mutated_plate, fitness))
        
        population = new_population[:individual_per_generation]
        popu = population.copy()
        popu.sort(key=lambda x: x[2], reverse=True)
        # if generation%10 == 0:
        popu[0][1].show_plot(fig, ax, generation+1)
        if next:
            os.rename("best.png", "best_old.png")
        fig.savefig("best.png", dpi=300, bbox_inches='tight')
    
    # Return best solution
    population.sort(key=lambda x: x[2], reverse=True)
    best_placements, best_plate, best_fitness = population[0]
    best_plate.show_plot(fig, ax, "Final")
    plt.ioff()
    
    # Add a final blocking show to keep the plot open until the user closes it.
    # Without this, the plot will disappear as soon as the script ends.
    plt.show()
    
    print(f"\nFinal solution:")
    print(f"Fitness: {best_fitness:.4f}")
    print(f"Shapes placed: {len(best_placements)}/{len(objects_to_place)}")
    
    return best_plate, best_placements, best_fitness


obj = [(42, 9.5)]

best_plate, best_placements, best_fitness = try_fit((122, 244), obj, resolution=10, generations=500, individual_per_generation=200, mutation_rate=0.4)
