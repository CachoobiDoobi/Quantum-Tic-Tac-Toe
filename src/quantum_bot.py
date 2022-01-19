import os
import numpy as np

from math import log2

from quantuminspire.api import QuantumInspireAPI
from quantuminspire.credentials import get_authentication
from quantum_state import QuantumState

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

    return result["histogram"]


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
    

    def find_next_move(self, board_state, turn_number=9):
        """ Returns the best move for the AI to make

        Args:
            board_state: The state of the board
            turn_number (int): Turn counter starting from 1
        """
        if len(board_state) != self.board_len:
            print("Invalid board state was given")
            return

        win_threshold = 0.4
        self.board_state = board_state

        if turn_number >= 3:
            # Check if we can win
            results = self.generate_winning_move()
            best_move = max(zip(results.values(), results.keys()))
            if best_move[0] > win_threshold:
                return int(log2(int(best_move[1])))

            # Check if the opponent can win, block them
            self.board_state = [X if value == O else O if value == X else _ for value in board_state]
            results = self.generate_winning_move()
            best_move = max(zip(results.values(), results.keys()))
            if best_move[0] > win_threshold:
                return int(log2(int(best_move[1])))

        board_mask = int("".join("0" if value == _ else "1" for value in board_state[::-1]), 2)
        results = self.generate_non_winning_move()

        best_move = int(list(results.keys())[0])
        best_move &= 2 ** 9 - 1 # We only need the lowest 9 bits
        best_move ^= board_mask # Xor the old board state away

        return int(log2(best_move))


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


    def generate_winning_move(self):
        """ Generate the qasm code for the winning move algorithm given the current board state

        Time complexity: O(27n)
        """
        valid = self.move_validation(self.board_len + 1, self.board_len + 2) # O(4n)
        win = self.win_condition(self.board_len + 2, self.board_len + 3) # O(8n)

        valid_and_win = valid + "\n" + win
        grovers_bit = f"\ntoffoli q[{self.board_len + 2}], q[{self.board_len + 1}], q[{self.board_len}]\n\n"

        qasm = ""
        qasm += f"h q[0:{self.board_len}]\nz q[{self.board_len}]\n"

        variable_cells = [str(index) for index, value in enumerate(self.board_state) if value == _] # O(n)
        # TODO: Get an appropriate number by calculations or heuristics
        qasm += f"\n.grover({len(variable_cells)})\n"
        qasm += valid_and_win + grovers_bit + reverse_lines(valid_and_win) + "\n" # O(13n)
        qasm += self.winning_move_diffuser(self.board_len, self.board_len + 1) # O(n)

        # Not measuring is faster, but then the results will have to be filtered afterwards
        qasm += f"\n.measurement\nmeasure_z q[{', '.join(variable_cells)}]"

        # This circuit will always use 17 qubits for a 3x3 board with at least 1 filled square
        # This limit is mostly defined by the multi-controlled toffoli for the diffuser
        qasm = f"version 1.0\n\nqubits {17}\n\n" + qasm

        result = execute_qasm(qasm=qasm, backend_type=qi_backend, number_of_shots=32,
                                     full_state_projection=False)

        return result


    def generate_non_winning_move(self):
        """  Check if the central square is free, and then take it if it is, otherwise take corners, if those are taken take a random free square """
        board = []
        for x in self.board_state:
            if x != _:
                board.append(1)
            else:
                board.append(0)

        qasm = ""
        qasm += f"version 1.0\n\nqubits {21}\n\n"

        qasm += f"""\n{{ {' | '.join([f"Ry q[{i}], {np.pi * board[i]}" for i in range(self.board_len)])}}}\n\n"""
        qasm += """X q[14]\n"""

        # Encode q[4] in q[9]
        qasm += """CNOT q[4], q[9]\n"""
        # Invert q[9]. If the center qubit was 0, q[9] is now 1 and vice-versa
        qasm += """X q[9]\n"""
        # If q[4] was 0 (empty), then q[9] is now 1 and the CNOT transforms q[4] into a 1 --> move is made
        qasm += """CNOT q[9], q[4]\n"""
        qasm += """Toffoli q[9], q[4], q[14]\n"""

        # If move was made, q[9] is 1, otherwise it is 0
        qasm += """CNOT q[0], q[10]\n"""
        qasm += """X q[10]\n"""
        qasm += """Toffoli q[14], q[10], q[0]\n"""
        qasm += """Toffoli q[10], q[0], q[14]\n"""

        # If move was made, q[10] = 1
        qasm += """CNOT q[2], q[11]\n"""
        qasm += """X q[11]\n"""
        qasm += """Toffoli q[14], q[11], q[2]\n"""
        qasm += """Toffoli q[11], q[2], q[14]\n"""

        # If move was made, q[11] = 1
        qasm += """CNOT q[6], q[12]\n"""
        qasm += """X q[12]\n"""
        qasm += """Toffoli q[14], q[12], q[6]\n"""
        qasm += """Toffoli q[12], q[6], q[14]\n"""

        # If move was made, q[12] = 1
        qasm += """CNOT q[8], q[13]\n"""
        qasm += """X q[13]\n"""
        qasm += """Toffoli q[14], q[13], q[8]\n"""
        qasm += """Toffoli q[13], q[8], q[14]\n"""

        # need to add case for corner and center filled
        qasm += """H q[9,10]\n"""
        qasm += """Measure_z q[9,10]\n"""

        # ============ Random move ========================

        # UP, q15 ununcomputable
        # check combination q9 q10 (0,0)
        qasm += """.logicup(1)\n"""
        qasm += """X q[9,10]\n"""
        qasm += """Toffoli q[9], q[10], q[15]\n"""
        # if valid, check if q1 is 1, if q1 is 1, flip q10
        qasm += """Toffoli q[15], q[1], q[10]\n"""
        # check if combination is still valid
        qasm += """Toffoli q[9], q[10], q[20]\n"""
        # if combination still valid, flip q1
        qasm += """Toffoli q[20], q[14], q[1]\n"""

        qasm += """Toffoli q[1], q[20], q[14]\n"""
        qasm += """Toffoli q[9], q[10], q[20]\n"""
        qasm += """X q[9,10]\n"""

        # LEFT, q16 ununcomputable

        # check combination q9 q10 (0,1)
        qasm += """X q[9]\n"""
        qasm += """Toffoli q[9], q[10], q[16]\n"""
        # if valid, check if q3 is 1, if q3 is 1, flip q9
        qasm += """Toffoli q[16], q[3], q[9]\n"""

        # check if combination is still valid
        qasm += """Toffoli q[9], q[10], q[20]\n"""
        # if combination still valid, flip q3
        qasm += """ Toffoli q[20], q[14], q[3]\n"""
        qasm += """ .uncomputeleft(1)\n"""
        qasm += """Toffoli q[3], q[20], q[14]\n """
        qasm += """Toffoli q[9], q[10], q[20]\n """
        qasm += """X q[9]\n"""
        # right, q17 ununcomputable

        qasm += """.logicright(1)\n"""
        # check combination q9 q10 (1,1)

        qasm += """ Toffoli q[9], q[10], q[17] \n"""
        # if valid, check if q5 is 1, if q5 is 1, flip q10

        qasm += """ Toffoli q[17], q[5], q[10]\n"""
        # check if combination is still valid
        qasm += """ Toffoli q[9], q[10], q[20]\n"""
        # if combination still valid, flip q5
        qasm += """  Toffoli q[20], q[14], q[5]\n"""
        qasm += """ .uncomputeright(1)\n"""
        qasm += """  Toffoli q[5], q[20], q[14]\n"""
        qasm += """Toffoli q[9], q[10], q[20]\n """
        # DOWN, q18 ununcomputable

        qasm += """.logicdown(1)\n"""
        # check combination q9 q10 (1,0)
        qasm += """X q[10] \n"""
        qasm += """Toffoli q[9], q[10], q[18] \n"""
        # if valid, check if q3 is 1, if q3 is 1, flip q9

        qasm += """ Toffoli q[18], q[7], q[9]\n"""
        # check if combination is still valid

        qasm += """ Toffoli q[9], q[10], q[20]\n"""
        # if combination still valid, flip q3
        qasm += """  Toffoli q[20], q[14], q[7]\n"""
        qasm += """.uncomputedown(1)\n """
        qasm += """Toffoli q[7], q[20], q[14]\n """
        qasm += """Toffoli q[9], q[10], q[20]\n """
        qasm += """ X q[10]\n """
        # ==== In the worst case, we need the first three circuits again ====

        # UP, q15 ununcomputable
        qasm += """ .logicUP(1)\n"""
        # check combination q9 q10 (0,0)
        qasm += """  X q[9,10] \n"""
        qasm += """ Toffoli q[9], q[10], q[15]\n"""
        # if valid, check if q1 is 1, if q1 is 1, flip q10
        qasm += """ Toffoli q[15], q[1], q[10]\n"""
        # check if combination is still valid
        qasm += """Toffoli q[9], q[10], q[20]\n """
        # if combination still valid, flip q1
        qasm += """ Toffoli q[20], q[14], q[1]\n"""
        qasm += """ .uncomputeUP(1)\n"""
        qasm += """Toffoli q[1], q[20], q[14]\n"""
        qasm += """ Toffoli q[9], q[10], q[20]\n"""
        qasm += """ X q[9,10]\n """

        # LEFT, q16 ununcomputable
        qasm += """ .logicleft(1)\n"""
        # check combination q9 q10 (0,1)
        qasm += """   X q[9]\n"""
        qasm += """ Toffoli q[9], q[10], q[16]\n"""
        # if valid, check if q3 is 1, if q3 is 1, flip q9

        qasm += """Toffoli q[16], q[3], q[9]\n """
        # check if combination is still valid

        qasm += """ Toffoli q[9], q[10], q[20]\n"""
        # if combination still valid, flip q3

        qasm += """ Toffoli q[20], q[14], q[3] \n"""

        qasm += """ .uncomputeleft(1)\n"""
        qasm += """Toffoli q[3], q[20], q[14]\n"""
        qasm += """ Toffoli q[9], q[10], q[20]\n"""
        qasm += """X q[9]\n"""
        # right, q17 ununcomputable
        qasm += """.logicright(1)\n"""
        # check combination q9 q10 (1,1)
        qasm += """Toffoli q[9], q[10], q[17]\n"""
        # if valid, check if q5 is 1, if q5 is 1, flip q10
        qasm += """Toffoli q[17], q[5], q[10]\n"""
        # check if combination is still valid
        qasm += """Toffoli q[9], q[10], q[20]\n"""
        # if combination still valid, flip q5
        qasm += """Toffoli q[20], q[14], q[5]\n"""

        qasm += """.uncomputeright(1)\n"""
        qasm += """Toffoli q[5], q[20], q[14]\n"""
        qasm += """Toffoli q[9], q[10], q[20]\n"""

        result = execute_qasm(qasm=qasm, backend_type=qi_backend, number_of_shots=128,
                                     full_state_projection=True)

        return result


        
if __name__ == "__main__":        
    QuantumBot = QuantumBot()
    QuantumBot.board_state =[
        O, _, X,
        _, _, O,
        X, O, _
    ]
    result = QuantumBot.generate_non_winning_move()
    print(result)
