import os
import numpy as np

from quantuminspire.api import QuantumInspireAPI
from quantuminspire.credentials import get_authentication

QI_URL = os.getenv("API_URL", "https://api.quantum-inspire.com/")

_ = 0
X = 1
O = 2

WINS_3x3 = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
]

project_name = "TicTacToe Bot"
authentication = get_authentication()
qi_api = QuantumInspireAPI(QI_URL, authentication=authentication, project_name=project_name)
qi_backend = qi_api.get_backend_type_by_name('QX single-node simulator')


def execute_qasm(qasm, backend_type, number_of_shots=128, full_state_projection=False):
    """ Helper function which executes the qasm and handles errors"""

    # TODO: Think about making this or the UI async to prevent the window from freezing
    result = qi_api.execute_qasm(
        qasm=qasm,
        backend_type=backend_type,
        number_of_shots=number_of_shots,
        full_state_projection=full_state_projection
    )

    if len(result["raw_text"]) > 0:
        print(result["raw_text"])
        lines = qasm.splitlines()
        log10_linecount = int(np.floor(np.log10(len(lines)))) + 1
        qasm = "\n".join(
            [f"{str(index + 1).rjust(log10_linecount, ' ')} |  {line}" for index, line in enumerate(lines)])
        print(f"\nIn QASM Code\n\n{qasm}")

    return result["historgram"]


def reverse_lines(str):
    """ Helper function which returns the string with the lines in reversed order"""
    return "\n".join(str.splitlines()[::-1])


def multicontrolled_toffoli(inputs, out, ancilla_start):
    """ Helper function which generate a multi-controlled `toffoli` circuit

    Time complexity: O(n) whith n = len(inputs)
    """
    if len(inputs) == 1:
        return ""
    
    if len(inputs) == 2:
        return f"toffoli q[{inputs[0]}], q[{inputs[1]}], q[{out}]\n"

    result = ""
    ancilla = ancilla_start

    result += f"toffoli q[{inputs[0]}], q[{inputs[1]}], q[{ancilla}]\n"

    for q in inputs[2:-1]: # O(n)
        ancilla += 1
        result += f"toffoli q[{q}], q[{ancilla - 1}], q[{ancilla}]\n"
    
    reverse = reverse_lines(result)

    result += f"toffoli q[{inputs[-1]}], q[{ancilla}], q[{out}]\n"
    result += reverse + "\n"

    return result


class QuantumBot:
    "Quantum bot for classical tic tac toe"

    def __init__(self):
        """ Create a new QuantumBot
        
        Args:
            size (int): The width and height of the board
        """
        self.board_state = [_ for i in range(3 ** 2)]
        self.board_len = len(self.board_state)
        self.win_conditions = WINS_3x3
    

    def find_next_move(self, board_state):
        if len(board_state) != self.board_len:
            print("Invalid board state was given")
            return

        self.board_state = board_state

        # Use the code from self.generate_winning_move_qasm
        # TODO: Add all steps

        # execute_qasm(self.generate_winning_move_qasm(), qi_backend)

        # return a number or a board state?


    def move_validation(self, out, ancilla_start):
        """ Generate the move validation sub-circuit
        
        Time complexity: O(4n) with n = board_len

        Args:
            out (int): The qubit used for the final result
            ancilla_start (int): The first qubit to use as ancilla
            subsequent ancilla bits will use the next qubit up. No ancilla bit is left dirty.
        """
        result = ""
        variable_cells = [i for i, v in enumerate(self.board_state) if v == _] # O(n)

        toffoli = multicontrolled_toffoli(variable_cells, out, ancilla_start) # O(n)

        variable_cells_str = ", ".join(str(i) for i in variable_cells) # O(n)
        result += f"x q[{variable_cells_str}]\n"

        for index in variable_cells: # O(n)
            result += f"x q[{index}]\n"
            result += toffoli
            result += f"x q[{index}]\n"

        result += f"x q[{variable_cells_str}]\n"

        return result


    def win_condition(self, out, ancilla_start):
        """ Generate the win condition sub-circuit
        
        Time complexity: O(8n) with n = board_len

        Args:
            out (int): The qubit used for the final result
            ancilla_start (int): The first qubit to use as ancilla
            subsequent ancilla bits will use the next qubit up. No ancilla bit is left dirty.
        """
        result = ""

        for cond in self.win_conditions: # O(8)
            if self.board_state[cond[0]] != O and self.board_state[cond[1]] != O and self.board_state[cond[2]] != O:
                result += multicontrolled_toffoli(cond, out, ancilla_start) # O(n)

        return result


    def winning_move_diffuser(self, out, ancilla_start):
        """ Generate the diffuser sub-circuit for the winning move algorithm
        
        Time complexity: O(n) with n = board_len

        Args:
            out (int): The qubit used for the final result
            ancilla_start (int): The first qubit to use as ancilla
            subsequent ancilla bits will use the next qubit up. No ancilla bit is left dirty.
        """
        result = ""

        result += f"h q[0:{self.board_len - 1}]\n"
        result += f"x q[0:{self.board_len - 1}]\n"
        result += multicontrolled_toffoli(list(range(self.board_len)), out, ancilla_start) # O(n)
        result += f"x q[0:{self.board_len - 1}]\n"
        result += f"h q[0:{self.board_len - 1}]\n"

        return result


    def generate_winning_move_qasm(self):
        """ Generate the qasm code for the winning move algorithm given the current board state

        Time complexity: O(27n)
        """
        valid = self.move_validation(self.board_len + 1, self.board_len + 2) # O(4n)
        win = self.win_condition(self.board_len + 2, self.board_len + 3) # O(8n)

        valid_and_win = valid + "\n" + win
        grovers_bit = f"\ntoffoli q[{self.board_len + 2}], q[{self.board_len + 1}], q[{self.board_len}]\n\n"

        qasm = ""
        qasm += f"h q[0:{self.board_len}]\nz q[{self.board_len}]\n"

        # TODO: Get an appropriate number by calculations or heuristics
        qasm += "\n.grover(8)\n"
        qasm += valid_and_win + grovers_bit + reverse_lines(valid_and_win) + "\n" # O(13n)
        qasm += self.winning_move_diffuser(self.board_len, self.board_len + 1) # O(n)

        # Not measuring is faster, but then the results will have to be filtered afterwards
        qasm += f"\n.measurement\nmeasure_z q[{', '.join([str(index) for index, value in enumerate(self.board_state) if value == _])}]" # O(n)

        # This circuit will always use 17 qubits for a 3x3 board with at least 1 filled square
        # This limit is mostly defined by the multi-controlled toffoli for the diffuser
        qasm = f"version 1.0\n\nqubits {17}\n\n" + qasm

        return qasm
