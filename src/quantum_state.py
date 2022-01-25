import os
import re

import numpy as np

from quantuminspire.api import QuantumInspireAPI
from quantuminspire.credentials import get_authentication

QI_URL = os.getenv("API_URL", "https://api.quantum-inspire.com/")

project_name = "TicTacToe"
authentication = get_authentication()
qi_api = QuantumInspireAPI(QI_URL, authentication=authentication, project_name=project_name)
qi_backend = qi_api.get_backend_type_by_name('QX single-node simulator')


class QuantumState:
    "Quantum state manager"

    def __init__(self, size=3):
        """ Create a new QuantumState and perform the setup.

        Args:
            size (int): The width and height of the board
        """
        self.size = size
        self.qubit_count = self.size ** 2
        self.command_queue = []
        self.initial_states = [0.5 for _ in range(self.qubit_count)]  # probabilities to be in the |1> state
        self.qasm = ""

    def __initialise_qubits(self):
        """Return the qasm code to allocate and initialise the qubits"""
        return f"""qubits {self.qubit_count}
        {{ {' | '.join([f"Ry q[{i}], {np.pi * self.initial_states[i]}" for i in range(self.qubit_count)])} }}
        """

    def __setup(self):
        """Return the qasm setup code."""
        return f"""version 1.0
        {self.__initialise_qubits()}
        """

    def reset(self):
        """Clear the accumulated qasm code."""
        self.qasm = ""

    def get_index(self, position):
        """ Convert a 2D (x, y) coordinate into a 1D array index.

        Args:
            position (int, int): The x and y coordinates in the 2D grid
        """
        x = max(0, min(self.size - 1, position[0]))
        y = max(0, min(self.size - 1, position[1]))
        return y * self.size + x

    def __append_command(self, command):
        """Append a string containing qasm commands to the accumulated qasm code."""
        self.qasm += re.sub(r"^[\t ]+", '', command.strip(), flags=re.M) + '\n\n'

    def __execute(self):
        self.reset()
        self.__append_command(self.__setup())

        for command in self.command_queue:
            next_line = ""
            if command["id"] == "move":
                next_line = self.__move(*command["data"])
            elif command["id"] == "entangle":
                next_line = self.__entangle(*command["data"])
            elif command["id"] == "swap":
                next_line = self.__swap(*command["data"])
            elif command["id"] == "measure":
                next_line = self.__measure(*command["data"])
            else:
                print(f"Unknown command {command['id']}")

            self.__append_command(next_line)

        measured_qubits = self.command_queue[-1]["data"][0]
        self.command_queue = [
            command
            for command in self.command_queue
            if command["id"] == "entangle" and
            not (command["data"][0] in measured_qubits or command["data"][1] in measured_qubits)
        ] # Filter all commands that are do not entangle unmeasured qubits

        result = qi_api.execute_qasm(qasm=self.qasm, backend_type=qi_backend, number_of_shots=512,
                                     full_state_projection=True)

        if len(result["raw_text"]) > 0:  # Error handling, raw_text only contains text when an error has occured
            print(result["raw_text"])
            lines = self.qasm.splitlines()
            log10_linecount = int(np.floor(np.log10(len(lines)))) + 1
            qasm = "\n".join(
                [f"{str(index + 1).rjust(log10_linecount, ' ')} |  {line}" for index, line in enumerate(lines)])
            print(f"\nIn QASM Code\n\n{qasm}")
            return

        filtered_probs = {}
        for key, value in result["histogram"].items():
            filtered_probs[f"{int(key):b}".zfill(self.qubit_count)[::-1]] = value

        """Renormalizing all the probabilites, and storing them in self.intial_states (array)"""

        inv_normalisation = sum(filtered_probs.values())
        for key in filtered_probs:
            filtered_probs[key] = filtered_probs[key] / inv_normalisation

        self.initial_states = []
        for i in range(self.qubit_count):
            prob = 0
            for key in filtered_probs:
                prob += int(key[i]) * filtered_probs[key]
            self.initial_states.append(prob)

        return self.initial_states

    def measure(self, q):
        """ Measure move: collapse an array of qubits

        Args:
            q (int[]): Which qubits are to be measured (values from 0 to 8)
        """
        self.command_queue.append({
            "id": "measure",
            "data": [q]
        })
        return self.__execute()

    def __measure(self, q):
        return f"Measure_z q[{', '.join([str(x) for x in q])}]"

    def move(self, q, player_id):
        """ Classic move: rotation about the y-axis.
        Args:
            qubits: The qubits
            q (int): Which qubit is rotated (value from 0 to 8)
            player_id (int): Which player did the move (value either 1 or 2)
        """
        self.command_queue.append({
            "id": "move",
            "data": [q, player_id]
        })

    def __move(self, q, player_id):
        angle = -np.pi / 4
        if player_id == 1:
            angle = np.pi / 4

        return f"Ry q[{q}], {angle:.10f}"

    def entangle(self, q1, q2):
        """ Entangle move: entangling two qubits.
        Args:
            qubits: The qubits
            q1, q2 (int): The qubits which need to be entangled (value from 0 to 8)
            engine: Engine is needed for Dagger(engine)
        """
        self.command_queue.append({
            "id": "entangle",
            "data": [q1, q2]
        })

    def __entangle(self, q1, q2):
        return f"""
        CNOT q[{q1}], q[{q2}]
        {{ H q[{q1}] | Tdag q[{q2}] }}
        {{ T q[{q1}] | H    q[{q2}] }}
        H q[{q1}]

        CNOT q[{q1}], q[{q2}]
        {{ H q[{q1}] | H q[{q2}] }}
        Tdag q[{q1}]
        H    q[{q1}]
        CNOT q[{q1}], q[{q2}]
        {{ Sdag q[{q1}] | S q[{q2}] }}
        """

    def swap(self, q1, q2):
        """ Swap move: swapping two qubits.
        Args:
            qubits: The qubits
            q1, q2 (int): The qubits which need to be swapped (value from 0 to 8)
        """
        self.command_queue.append({
            "id": "swap",
            "data": [q1, q2]
        })

    def __swap(self, q1, q2):
        return f"swap q[{q1}], q[{q2}]"