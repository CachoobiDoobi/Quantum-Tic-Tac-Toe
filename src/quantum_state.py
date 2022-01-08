import os

import numpy as np

from projectq import MainEngine
from projectq.backends import ResourceCounter
from projectq.meta import Dagger
from projectq.ops import H, Ry, TGate, CNOT, SGate, Swap, Measure
from projectq.setups import restrictedgateset

from quantuminspire.api import QuantumInspireAPI
from quantuminspire.credentials import get_authentication
from quantuminspire.projectq.backend_qx import QIBackend

QI_URL = os.getenv("API_URL", "https://api.quantum-inspire.com/")

project_name = "TicTacToe"
authentication = get_authentication()
qi_api = QuantumInspireAPI(QI_URL, authentication=authentication, project_name=project_name)

class QuantumState:
    "Quantum state manager"

    def __init__(self, size=3):
        """ Create a new QuantumState and perform the setup.
        
        Args:
            size (int): The width and height of the board
        """
        self.size = size
        self.command_queue = []
        self.initial_states = [0.5 for _ in range(size ** 2)] # probabilities to be in the |1> state
        self.setup()
    

    def __initialise_qubits(self):
        """Allocate the qubits and place them in the |+> state."""
        self.qubits = self.engine.allocate_qureg(self.size ** 2)
        for i in range(len(self.qubits)):
            Ry(np.pi * self.initial_states[i]) | self.qubits[i]

    
    def setup(self):
        """Initialise a new backend, engine and qubit register."""
        self.qi_backend = QIBackend(quantum_inspire_api=qi_api)
        self.compiler_engines = restrictedgateset.get_engine_list(
            one_qubit_gates=self.qi_backend.one_qubit_gates,
            two_qubit_gates=self.qi_backend.two_qubit_gates,
            other_gates=self.qi_backend.three_qubit_gates
        )

        self.compiler_engines.extend([ResourceCounter()])
        self.engine = MainEngine(backend=self.qi_backend, engine_list=self.compiler_engines)

        self.__initialise_qubits()
    

    def reset(self):
        """Flush the current circuit, deallocate the qubits and perform the setup."""
        self.engine.flush(deallocate_qubits=True)
        self.setup()

    
    def get_index(self, position):
        """ Convert a 2D (x, y) coordinate into a 1D array index.
        
        Args:
            position (int, int): The x and y coordinates in the 2D grid
        """
        x = max(0, min(self.size - 1, position[0]))
        y = max(0, min(self.size - 1, position[1]))
        return y * self.size + x


    def __execute(self):
        self.reset()
        for command in self.command_queue:
            if command["id"] == "move": self.__move(*command["data"])
            elif command["id"] == "entangle": self.__entangle(*command["data"])
            elif command["id"] == "swap": self.__swap(*command["data"])
            elif command["id"] == "measure": self.__measure(*command["data"])
            else: print(f"Unknown command {command['id']}")
        self.engine.flush()

        index = self.qubits[self.command_queue[-1]["data"][0]]

        mresult = self.engine.get_measurement_result(index) # Returns the result of the measurement of qubit `index`
        probabilities = self.qi_backend.get_probabilities(self.qubits) # Returns all possible states with their probabilities

        print(mresult)
        print(probabilities)

        # TODO:
        #   Filter qubit strings based on result of measurement
        #   Filter probabilities array => { "10101110": 0.5, "10101110": 0.3, ... }
        #   Normalise resulting probabilities
        #   Fill initial_states array

        filtered_probs = {} # The filtered dictionary

        """Renormalizing all the probabilites, and storing them in self.intial_states (array)"""

        inv_normalisation = sum(filtered_probs.values())
        for key in filtered_probs:
            filtered_probs[key] = filtered_probs[key] / inv_normalisation

        self.initial_states = []
        for i in range(len(filtered_probs)):
            prob = 0
            for key in filtered_probs:
                prob += int(key[i]) * filtered_probs[key]
            self.initial_states.append(prob)

        # "0100" ~0.25 => [ 0.5, 1, 0.5, 0.5 ]
        # "0000" ~0.25
        # "1100" ~0.25
        # "1000" ~0.25

        # "0100" ~0.5, "1100" ~0.5
        # send [0.5, 1, 1, 1] 
 

        self.command_queue = [] # Clear the command queue

        return self.initial_states


    def measure(self, q, player_id):
        self.command_queue.append({
            "id": "measure",
            "data": [q, player_id]
        })
        self.__execute()
    
    def __measure(self, q, player_id):
        Measure | self.qubits[q]


    def move(self, q, player_id):
        """ Classic move: rotation about the y-axis.

        Args:
            qubits: The qubits
            q (int): Which qubit is rotated (value from 0 to 8)
            player_id (int): Which player did the move (value either 1 or 2)                                    
        """
        self.command_queue.append({
            "id": "move",
            "data": [ q, player_id ]
        })

    def __move(self, q, player_id):
        if player_id == 1:
            Ry(np.pi/2) | self.qubits[q]
        else:
            Ry(-np.pi/2) | self.qubits[q]


    def entangle(self, q1, q2):
        """ Entangle move: entangling two qubits.

        Args:
            qubits: The qubits
            q1, q2 (int): The qubits which need to be entangled (value from 0 to 8)          
            engine: Engine is needed for Dagger(engine)                       
        """
        self.command_queue.append({
            "id": "entangle",
            "data": [ q1, q2 ]
        })

    def __entangle(self, q1, q2):
        CNOT | (self.qubits[q1], self.qubits[q2])

        H | self.qubits[q1]
        with Dagger(self.engine):
            TGate() | self.qubits[q2]
        TGate() | self.qubits[q1]
        H | self.qubits[q2]
        H | self.qubits[q1]

        CNOT | (self.qubits[q1], self.qubits[q2])

        H | self.qubits[q1]
        H | self.qubits[q2]
        with Dagger(self.engine):
            TGate() | self.qubits[q1]
        H | self.qubits[q1]

        CNOT | (self.qubits[q1], self.qubits[q2])

        with Dagger(self.engine):
            SGate() | self.qubits[q1]
        SGate() | self.qubits[q2]


    def swap(self, q1, q2):
        """ Swap move: swapping two qubits.

        Args:
            qubits: The qubits
            q1, q2 (int): The qubits which need to be swapped (value from 0 to 8)                    
        """
        self.command_queue.append({
            "id": "swap",
            "data": [ q1, q2 ]
        })

    def __swap(self, q1, q2):
        Swap | (self.qubits[q1], self.qubits[q2])

qs = QuantumState(2)
qs.measure(1, 1)
