# Natalia Sofía Salgado García			A01571008
# Luis Fernando Manzanares Sánchez		A01283738
# Emiliano Salinas Del Bosque			A01570972
# Alejandro Guevara Olivares			A00834438

import socket
import agentpy as ap
import numpy as np
import random
import time
#import matplotlib.pyplot as plt
#import IPython.display

# Configurar el socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 1107))
print("Connected to the server")

# Define the Message class
class Message:
    def __init__(self, sender, performative, content=None):
        self.sender = sender
        self.performative = performative
        self.content = content

# Define the TrafficLight agent class
class TrafficLight(ap.Agent):
    def setup(self):
        self.state = 1  # 0: Red, 1: Green, 2: Yellow
        self.pedestrian_request = False
        self.pedestrian_request_timer = 0
        self.red_timer = 0
        self.red_duration = self.model.p.red_duration
        self.request_delay = self.model.p.request_delay
        self.timer = 0

    def update_color_smart(self):
        if self.pedestrian_request:
            self.pedestrian_request_timer += 1
            if self.pedestrian_request_timer >= self.request_delay:
                self.state = 2  # Turn yellow
                if self.pedestrian_request_timer >= self.request_delay * 3/2:
                    self.state = 0  # Turn red
                    self.model.cars_crossed_per_light.append(self.model.cars_counter)  # Record the number of cars crossed during the green light
                    self.model.cars_counter = 0
                    self.red_timer = self.red_duration
                    self.pedestrian_request = False  # Reset the request
                    self.pedestrian_request_timer = 0
        elif self.red_timer > 0:
            self.model.total_red_light += 1  # Count the total time the light is red
            self.red_timer -= 1
            if self.red_timer == 0:  # Red timer ran out
                if not any(isinstance(agent, Pedestrian) for agent in self.model.place.agents):  # No pedestrians waiting
                    self.state = 1  # Change to green
                    # Reset delay for all vehicles
                    for agent in self.model.place.agents:
                        if isinstance(agent, Vehicle):
                            agent.delay_timer = agent.light_green_delay
        else:
            self.state = 1  # Default to green

    def update_color_normal(self):
        green_duration = 20
        if self.state == 1:  # Green
            if self.timer >= green_duration:
                self.state = 2  # Switch to yellow
                self.timer = 0
        elif self.state == 2:  # Yellow
            if self.timer >= self.model.p.request_delay / 2:
                self.state = 0  # Switch to red
                self.model.cars_crossed_per_light.append(self.model.cars_counter)  # Record the number of cars crossed during the green light
                self.model.cars_counter = 0
                self.timer = 0
                self.red_timer = self.model.p.red_duration
        elif self.state == 0:  # Red
            self.red_timer -= 1
            self.model.total_red_light += 1  # Count the total time the light is red
            if self.timer >= self.model.p.red_duration:
                self.state = 1  # Switch to green
                # Reset delay for all vehicles
                for agent in self.model.place.agents:
                    if isinstance(agent, Vehicle):
                        agent.delay_timer = agent.light_green_delay
                self.timer = 0

        self.timer += 1

    def handle_message(self, message):
        if message.performative == "REQUEST":
            if not self.pedestrian_request and self.red_timer == 0:
                self.pedestrian_request = True
                self.pedestrian_request_timer = 0

    def get_state_string(self):
        if self.state == 0:
            return "red"
        elif self.state == 1:
            return "green"
        elif self.state == 2:
            return "yellow"

# Define the Pedestrian agent class
class Pedestrian(ap.Agent):
    def setup(self):
        self.state = 4

    def move(self):
        traffic_light = self.model.traffic_light.state[0]

        pos = self.model.place.positions[self]
        new_pos = (pos[0], pos[1] - 1)

        if pos[1] == self.model.p.width - 1:
            self.model.place.move_by(self, (0, -1))

        # Send a request to the traffic light if near the crossing if smart crossing is enabled
        if self.model.p.smart_crossing:
            # Request red light if near the crossing and the light is green
            if pos[1] == self.model.p.width - 2 and traffic_light == 1:
                message = Message(self, "REQUEST")
                self.model.traffic_light[0].handle_message(message)

        if traffic_light == 0 and new_pos not in self.model.place.positions.values():
            # Calculate the time needed for the pedestrian to cross
            cells_to_cross = pos[1]  # Number of cells to cross to reach the leftmost column
            time_to_cross = cells_to_cross  # Each step moves the pedestrian one cell

            if self.model.traffic_light[0].red_timer < time_to_cross:
                return  # Wait for the next step

            self.model.place.move_by(self, (0, -1))

class RandomPedestrian(ap.Agent):
    next_id = 0
    def setup(self):
        self.id = RandomPedestrian.next_id
        RandomPedestrian.next_id += 1
        self.state = 4
# Define the Vehicle agent class
    def move(self):
        pos = self.model.place.positions[self]
        new_pos = (pos[0], pos[1] - 1)
        if pos[1] == 0:  # Reached the leftmost column
            self.model.place.remove_agents(self)
            return
        
        if new_pos not in self.model.place.positions.values():
            self.model.place.move_by(self, (0, -1))

# Define the Vehicle agent class
class Vehicle(ap.Agent):
    next_id = 0
    def setup(self):
        self.id = Vehicle.next_id
        Vehicle.next_id += 1
        self.state = 3
        self.reached_top = False
        self.time_on_top = 0
        self.just_added = True  # Flag to indicate if the vehicle was just added
        self.light_green_delay = 2  # Delay steps after the light turns green
        self.delay_timer = 0  # Timer to track the delay
        self.velocity = 0  # Initial velocity
        self.max_velocity = 5  # Maximum velocity
        self.acceleration = 1  # Acceleration rate
        self.deceleration = -1  # Deceleration rate
        self.remove = False  # Flag to indicate if the vehicle should be removed

    def move(self):
        if self.just_added:
            self.just_added = False  # Skip movement if just added
            return

        traffic_light = self.model.traffic_light.state[0]
        red_light_timer = self.model.traffic_light.red_timer
        pos = self.model.place.positions[self]
        new_pos = (pos[0] - self.velocity, pos[1])

        if red_light_timer == 1:
            self.velocity = 1

        if pos[0] == 0 or (pos[0] == 1 and traffic_light == 0):
            self.remove = True
            return

        if traffic_light == 0:  # Red light
            if pos[0] > 2 and (pos[0] - 1, pos[1]) not in self.model.place.positions.values():
                self.model.place.move_by(self, (-1, 0))
            self.velocity = 0
            return
        elif traffic_light == 1:  # Green light
            if self.delay_timer > 0:
                self.delay_timer -= 1
                return
            if self.velocity < self.max_velocity:
                self.velocity += self.acceleration  # Speed up
        elif traffic_light == 2:  # Yellow light
            if self.velocity > 1:
                self.velocity += self.deceleration  # Slow down, but ensure it doesn't drop below 1
            if self.velocity < 1:
                self.velocity = 1  # Ensure minimum velocity is 1 during yellow light

        # Check for RandomPedestrians in the same column
        if any(isinstance(agent, RandomPedestrian) and self.model.place.positions[agent][1] == pos[1] for agent in self.model.place.agents):
            self.velocity = 0  # Stop the vehicle

        # Ensure vehicles do not collide
        if new_pos[0] >= 0 and new_pos not in self.model.place.positions.values():
            self.model.place.move_by(self, (-self.velocity, 0))
        elif new_pos[0] <= 0:  # If the vehicle reaches or exceeds the top row
            new_pos = (0, pos[1])
            if new_pos not in self.model.place.positions.values():  # Only move if the cell is empty
                self.model.place.move_by(self, (-pos[0], 0))  # Move to the top row
                self.reached_top = True
            else:
                self.velocity = 0  # Stop if the cell is occupied

# Define the CrossingModel model class
class CrossingModel(ap.Model):
    def setup(self):
        self.track_empty = True
        self.place = ap.Grid(self, (self.p.height, self.p.width), track_empty=True)
        self.traffic_light = ap.AgentList(self, 1, TrafficLight)  # Create a list with one TrafficLight agent
        self.place.add_agents(self.traffic_light, positions=[(1, self.p.width - 2)], empty=True)
        self.cars_crossed = 0
        self.cars_counter = 0
        self.cars_crossed_per_light = []
        self.pedestrians_crossed = 0
        self.total_red_light = 0

    def step(self):
        # Update the traffic light color
        if self.p.smart_crossing: # Use smart crossing
            self.traffic_light.update_color_smart()
        else:
            self.traffic_light.update_color_normal()

        self.add_vehicle()
        self.add_pedestrian()
        self.add_random_pedestrian()

        # Move existing vehicles and pedestrians
        agents_to_remove = []
        for agent in self.place.agents:
            if isinstance(agent, Vehicle):
                agent.move()
                pos = self.place.positions[agent]
                # Remove the vehicle only if it has reached the top row and stayed there for one time step
                if agent.remove == True:
                    self.cars_crossed += 1
                    self.cars_counter += 1
                    agents_to_remove.append(agent)
            elif isinstance(agent, Pedestrian) or isinstance(agent, RandomPedestrian):
                agent.move()
                pos = self.place.positions[agent]
                # Remove the pedestrian if they reach the leftmost column
                if pos[1] == 0:
                    self.pedestrians_crossed += 1
                    agents_to_remove.append(agent)

        # Remove agents outside of the iteration
        for agent in agents_to_remove:
            self.place.remove_agents(agent)

        positions = [self.place.positions[agent] for agent in self.place.agents if isinstance(agent, Vehicle)]
        if len(positions) != len(set(positions)):
            duplicate_positions = [pos for pos in positions if positions.count(pos) > 1]
            print(f"Overlapping positions detected at step {self.t}: {duplicate_positions}")
            for pos in duplicate_positions:
                agents_at_pos = [agent for agent, agent_pos in self.place.positions.items() if agent_pos == pos]
                for agent in agents_at_pos:
                    print(f"Agent {agent} velocity: {agent.velocity}")
                print(f"Agents at {pos}: {agents_at_pos}")

        # Enviar las posiciones de todos los agentes a Unity
        positions = {}
        for agent in self.place.agents:
            agent_type = type(agent).__name__
            if agent_type not in positions:
                positions[agent_type] = []
            if isinstance(agent, Vehicle) or isinstance(agent, RandomPedestrian):
                positions[agent_type].append({'id': agent.id, 'position': self.place.positions[agent]})
            elif isinstance(agent, TrafficLight):
                positions[agent_type].append({'state': self.traffic_light[0].get_state_string()})
            else:
                positions[agent_type].append(self.place.positions[agent])
        self.positions_history.append(positions)

    def add_vehicle(self):
        # Find all columns in the bottom row
        bottom_row = self.p.height - 1
        all_columns = list(range(2, self.p.width - 2))

        # Get the positions of all vehicles
        vehicle_positions = [pos for agent, pos in self.place.positions.items() if isinstance(agent, Vehicle)]
        occupied_columns = [pos[1] for pos in vehicle_positions if pos[0] == bottom_row]
        available_columns = [col for col in all_columns if col not in occupied_columns]

        # If there are no available columns, do not add a vehicle
        if not available_columns:
            return

        column = random.choice(available_columns)
        vehicle = Vehicle(self)
        self.place.add_agents([vehicle], positions=[(bottom_row, column)], empty=True)
        # print(f"Added vehicle at position: {(bottom_row, column)}")

    def add_pedestrian(self):
        if random.random() < self.p.pedestrian_probability:
            if not any(isinstance(agent, Pedestrian) for agent in self.place.agents):
                pedestrian = Pedestrian(self)
                self.place.add_agents([pedestrian], positions=[(0, self.p.width - 1)], empty=True)
                # print("Pedestrian added at time-step", self.t)

    def add_random_pedestrian(self):
        if random.random() < self.p.random_pedestrian_prob:
            new_random_pedestrian = RandomPedestrian(self)
            self.place.add_agents([new_random_pedestrian], positions=[(random.randint(2, self.p.height - 1), self.p.width - 1)], empty=True)
            #print("Random pedestrian added at time-step", self.t)

    def send_positions_to_unity(self):
        try:
            for step, positions in enumerate(self.positions_history):
                for agent_type, agent_positions in positions.items():
                    for position in agent_positions:
                        if agent_type == "TrafficLight":  # Enviar estado del semáforo
                            message = f"Step {step}: {{'{agent_type}': {{'state': '{position['state']}'}}}}\n"
                        elif agent_type == "Pedestrian":  # Enviar estado del semáforo
                            message = f"Step {step}: {{'{agent_type}': {position}}}\n"
                        elif isinstance(position, dict):  # Caso para vehículos y peatones con identificadores
                            message = f"Step {step}: {{'{agent_type}': {{'id': {position['id']}, 'position': {position['position']}}}}}\n"
                        s.sendall(message.encode('ascii'))
                time.sleep(1)  # Añade un pequeño delay para asegurar la recepción por parte de Unity
        except Exception as e:
            print(f"Error sending positions to Unity: {e}")

def animation_plot(model, ax):
    attr_grid = model.place.attr_grid('state')
    sidewalk = np.zeros(model.place.shape, dtype=int)
    street = np.zeros(model.place.shape, dtype=int)
    color_dict = {0: '#FF0000', 1: '#00FF00', 2: '#FFFF00', 3: '#FF00FF', 4: '#00FFFF', None: 'none'}

    # Custom coloring of non-agent cells
    for i in range(model.p.height):
        for j in range(model.p.width):
            if j <= 1 or j >= model.p.width - 2:  # Sidewalk on left and right sides
                sidewalk[i][j] = 1  # Mark sidewalk cells as 1
            else:
                street[i][j] = 1

    ax.imshow(street, cmap='Greys', alpha=1)
    ax.imshow(sidewalk, cmap='Greys', alpha=0.3)
    ap.gridplot(attr_grid, ax=ax, color_dict=color_dict, convert=True)
    ax.set_title(f"Crossing model \n Time-step: {model.t}")

def metrics(model):
    if model.cars_crossed_per_light == []:
            model.cars_crossed_per_light.append(model.cars_crossed)
    return {
        'Total red light time': model.total_red_light,
        'Total cars crossed': model.cars_crossed,
        'Total pedestrians crossed': model.pedestrians_crossed,
        'Cars crossed per green light': model.cars_crossed_per_light
    }

# Model parameters
parameters = {
    'steps': 300,
    'height': 30,
    'width': 9,
    'pedestrian_probability': 0.1,
    'random_pedestrian_prob': 0.1,
    'request_delay': 4,
    'red_duration': 7,
    'smart_crossing': True,
}

# Create the model
model = CrossingModel(parameters)
model.positions_history = []  # Lista para almacenar las posiciones en cada paso
results = model.run()

# Envía todas las posiciones al servidor Unity al final de la simulación
model.send_positions_to_unity()

# Set up the animation
#fig, ax = plt.subplots()
#animation = ap.animate(model, fig, ax, animation_plot)

# Display the animation
#IPython.display.HTML(animation.to_jshtml())

# Cerrar el socket
s.close()
print("Socket closed")