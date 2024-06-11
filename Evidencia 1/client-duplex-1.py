import socket
import agentpy as ap

# Configurar el socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 1107))
print("Connected to the server")

# Definición del agente "Car"
class CarAgent(ap.Agent):
    def setup(self):
        self.pos = (0, 0)  # Posición inicial (x, y)

    def step(self):
        self.pos = (self.pos[0], self.pos[1] + 1)  # Mover el carro una unidad a la derecha

# Definición del modelo
class CarModel(ap.Model):
    def setup(self):
        self.car = CarAgent(self)  # Crear una instancia del agente Car

    def step(self):
        self.car.step()  # Avanzar el agente Car
        position_message = f"Step {self.t}: Car position: {self.car.pos}\n"
        print(position_message.strip())
        s.send(position_message.encode('ascii'))  # Enviar la posición del carro

# Parámetros del modelo
parameters = {
    'steps': 10,  # Número de pasos en la simulación
}

# Crear y ejecutar la simulación
model = CarModel(parameters)
results = model.run()

# Cerrar el socket
s.close()
print("Socket closed")
