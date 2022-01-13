_ = 0
X = 1
O = 2

# Define the state of the board, the algorithm will try to find a win for X
board_state = [
    O, O, X,
    _, _, _,
    _, _, X
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


def multicontrolled_or(inputs, out, ancilla_start):
    """ Generate a multi-controlled `or` circuit
    
    Time complexity: O(n) with n = len(inputs)
    """
    if len(inputs) == 1:
        return f"cnot q[{inputs[0]}], q[{out}]\n"
    
    if len(inputs) == 2:
        return f"x q[{inputs[0]}, {inputs[1]}]\ntoffoli q[{inputs[0]}], q[{inputs[1]}], q[{out}]\nx q[{inputs[0]}, {inputs[1]}, {out}]\n"

    result = ""
    inputs_str = ', '.join(str(n) for n in inputs)

    result += f"x q[{inputs_str}]\n"
    toffoli = multicontrolled_toffoli(inputs, out, ancilla_start) # O(n)
    result += toffoli
    result += f"x q[{inputs_str}, {out}]\n"

    return result


def validation(out, ancilla_start):
    """ Generate the validation sub-circuit
    
    Time complexity: O(4n) with n = board_len
    """
    result = ""
    ancilla = ancilla_start

    toffoli = multicontrolled_toffoli(list(range(board_len)), "{out:n}", ancilla_start) # O(n)
    or_inputs = []

    ancilla += board_len - 2

    variable_cells_str = ", ".join([str(i) for i, v in enumerate(board_state) if v == _]) # O(n)
    result += f"x q[{variable_cells_str}]\n"

    for index, value in enumerate(board_state): # O(n)
        if value != _:
            continue

        result += f"x q[{index}]\n"
        result += toffoli.format(out=ancilla)
        result += f"x q[{index}]\n"

        or_inputs.append(ancilla)
        ancilla += 1
    result += f"x q[{variable_cells_str}]\n"

    result += multicontrolled_or(or_inputs, out, or_inputs[0] - len(or_inputs) + 1) # O(n)

    return result


def win_condition(out, ancilla_start):
    """ Generate the win condition sub-circuit
    
    Time complexity: O(9n) with n = board_len
    """
    result = ""
    ancilla = ancilla_start
    or_inputs = []

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
            result += multicontrolled_toffoli(cond, ancilla, ancilla + 1) # O(n)
            or_inputs.append(ancilla)
            ancilla += 1

    result += multicontrolled_or(or_inputs, out, ancilla) # O(n)

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
    win = win_condition(board_len + 2, board_len + 3) # O(9n)

    valid_and_win = valid + "\n" + win
    grovers_bit = f"\ntoffoli q[{board_len + 2}], q[{board_len + 1}], q[{board_len}]\n\n"

    qasm = ""
    qasm += f"h q[0:{board_len}]\nz q[{board_len}]\n"

    # TODO: Get an appropriate number by calculations or heuristics
    qasm += "\n.grover(8)\n"
    qasm += valid_and_win + grovers_bit + reverse_lines(valid_and_win) + "\n" # O(13n)
    qasm += diffuser(board_len, board_len + 1) # O(n)

    # Not measuring is faster
    # qasm += f"\n.measurement\nmeasure_z q[{', '.join([str(index) for index, value in enumerate(board_state) if value == _])}]"

    # TODO: Calculate the actual amount of qubits used
    qasm = f"version 1.0\n\nqubits {26}\n\n" + qasm

    return qasm

print(generate_qasm())
