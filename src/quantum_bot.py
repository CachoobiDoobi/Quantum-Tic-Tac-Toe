_ = 0
X = 1
O = 2

# Define the state of the board, the algorithm will try to find a win for X
board_state = [
    O, _, X,
    _, _, O,
    X, _, _
]
board_len = len(board_state)


def reverse_lines(str):
    return "\n".join(str.splitlines()[::-1])


def multicontrolled_toffoli(inputs, out, ancilla_start):
    """ Generate a multi-controlled `toffoli` circuit

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


def validation(out, ancilla_start):
    """ Generate the validation sub-circuit
    
    Time complexity: O(4n) with n = board_len
    """
    result = ""
    variable_cells = [i for i, v in enumerate(board_state) if v == _] # O(n)

    toffoli = multicontrolled_toffoli(variable_cells, out, ancilla_start) # O(n)

    variable_cells_str = ", ".join(str(i) for i in variable_cells) # O(n)
    result += f"x q[{variable_cells_str}]\n"

    for index in variable_cells: # O(n)
        result += f"x q[{index}]\n"
        result += toffoli
        result += f"x q[{index}]\n"

    result += f"x q[{variable_cells_str}]\n"

    return result


def win_condition(out, ancilla_start):
    """ Generate the win condition sub-circuit
    
    Time complexity: O(8n) with n = board_len
    """
    result = ""

    conditions = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6]
    ]

    for cond in conditions: # O(8)
        if board_state[cond[0]] != O and board_state[cond[1]] != O and board_state[cond[2]] != O:
            result += multicontrolled_toffoli(cond, out, ancilla_start) # O(n)

    return result


def diffuser(out, ancilla_start):
    """ Generate the diffuser sub-circuit
    
    Time complexity: O(n) with n = board_len
    """
    result = ""

    result += f"h q[0:{board_len - 1}]\n"
    result += f"x q[0:{board_len - 1}]\n"
    result += multicontrolled_toffoli(list(range(board_len)), out, ancilla_start) # O(n)
    result += f"x q[0:{board_len - 1}]\n"
    result += f"h q[0:{board_len - 1}]\n"

    return result


def generate_qasm():
    """ Generate the qasm code for the board state defined by board_state

    Time complexity: O(27n)
    """
    valid = validation(board_len + 1, board_len + 2) # O(4n)
    win = win_condition(board_len + 2, board_len + 3) # O(8n)

    valid_and_win = valid + "\n" + win
    grovers_bit = f"\ntoffoli q[{board_len + 2}], q[{board_len + 1}], q[{board_len}]\n\n"

    qasm = ""
    qasm += f"h q[0:{board_len}]\nz q[{board_len}]\n"

    # TODO: Get an appropriate number by calculations or heuristics
    qasm += "\n.grover(8)\n"
    qasm += valid_and_win + grovers_bit + reverse_lines(valid_and_win) + "\n" # O(13n)
    qasm += diffuser(board_len, board_len + 1) # O(n)

    # Not measuring is faster, but then the results will have to be filtered afterwards
    qasm += f"\n.measurement\nmeasure_z q[{', '.join([str(index) for index, value in enumerate(board_state) if value == _])}]" # O(n)

    # The circuit will always use 17 qubits
    # This limit is mostly defined by the multi-controlled toffoli for the diffuser
    qasm = f"version 1.0\n\nqubits {17}\n\n" + qasm

    return qasm

print(generate_qasm())
