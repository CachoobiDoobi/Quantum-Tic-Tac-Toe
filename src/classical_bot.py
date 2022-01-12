import numpy as np

_ = 0
X = 1
O = 2

def boolean_formula(board_state):
    """ Takes a board state with X to move and returns whether or not they have a winning strategy
    """
    win_for_p = lambda state, p: (
            state[0] == state[1] == state[2] == p or
            state[3] == state[4] == state[5] == p or
            state[6] == state[7] == state[8] == p or

            state[0] == state[3] == state[6] == p or
            state[1] == state[4] == state[7] == p or
            state[2] == state[5] == state[8] == p or

            state[0] == state[4] == state[8] == p or
            state[2] == state[4] == state[6] == p
        )

    win_for_x = lambda state: win_for_p(state, X)
    win_for_o = lambda state: win_for_p(state, O)

    if len(list(filter(lambda x: x != _, board_state))) == 0:
        state = board_state
        return win_for_x or not win_for_o 

    for i in range(len(board_state)):
        if board_state[i] != _:
            continue

        state = board_state.copy()
        state[i] = X

        if win_for_x(state):
            return True

    return False

initial_board = [
    O , X , X ,
    _ , O , _ ,
    _ , _ , X
]

def find_response(initial_board, depth):
    if depth == 0:
        return []
    
    results = []
    
    for i in range(len(initial_board)):
        if initial_board[i] != _:
            continue

        board = initial_board.copy()
        board[i] = O
        if not boolean_formula(board):
            results.append([i])

            for j in range(len(board)):
                if board[j] != _:
                    continue
                boardcopy = board.copy()
                boardcopy[j] = X
                results[-1].append([j])
                tmp = find_response(boardcopy, depth - 1)
                if len(tmp) > 0:
                    results[-1][-1].append(tmp)
            

    return results

[3, [[8]], [[4]], [[4]], [[5]]]
print(find_response(initial_board, 2))
# print(boolean_formula(initial_board))