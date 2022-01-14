import numpy as np
from quantum_state import QuantumState


class Board:
    def __init__(self, size=3):
        # initialize board
        self.squares = np.empty((size, size), dtype=Qubit)
        self.qs = QuantumState()

        # create each qubit
        j = 0
        for i in range(size):
            for j in range(size):
                self.squares[i, j] = Qubit((i, j))

    def check_win(self):
        # convert all elements to strings
        squares = self.squares.astype(str)

        # check all rows if all entries are either X or O
        for i in range(squares.shape[0]):
            row = np.unique(squares[i])
            if row.size == 1 and (row[0] == "X" or row[0] == "O"):
                print(row[0] + " wins!")
                break

        # check all columns if all entries are either X or O
        for i in range(self.squares.shape[0]):
            column = np.unique(squares[:, i])
            if column.size == 1 and (column[0] == "X" or column[0] == "O"):
                print(column[0] + " wins!")
                break

        # check diagonal if all entries are either X or O
        diagonal = np.unique(np.diagonal(squares))
        if diagonal.size == 1 and (diagonal[0] == "X" or diagonal[0] == "O"):
            print(diagonal[0] + " wins!")

        # check off-diagonal if all entries are either X or O
        # can do this in a more clever way , right now is for 3x3
        offdiagonal = np.unique(np.array((squares[0][2], squares[1][1], squares[2][0])))
        if offdiagonal.size == 1 and (offdiagonal[0] == "X" or offdiagonal[0] == "O"):
            print(offdiagonal[0] + " wins!")

    def move(self, position: tuple, player):
        # player 1 goes toward 0, player 2 goes toward 1
        if player == 1:
            self.squares[position[0]][position[1]].probability -= 0.25
            self.qs.move(position[0] * 3 + position[1], player)

        elif player == 2:
            self.squares[position[0]][position[1]].probability += 0.25
            self.qs.move(position[0] * 3 + position[1], player)

        else:
            raise ValueError("Not a valid player: should be 1 or 2")

    def get_qubit(self, position):
        return self.squares[position[0], position[1]]

    def get_probability(self, position):
        return self.get_qubit(position).probability

    def get_entagled(self, position):
        return self.get_qubit(position).entagled

    def swap(self, position1, position2):
        temp = self.get_qubit(position1)
        self.squares[position1[0], position1[1]] = self.get_qubit(position2)
        self.squares[position1[0], position1[1]].position = position2
        self.squares[position2[0], position2[1]] = temp
        self.squares[position2[0], position2[1]].position = position1

        self.qs.swap(position1[0] * 3 + position1[1], position2[0] * 3 + position2[1])

    def entangle(self, position1, position2):
        q1 = self.get_qubit(position1)
        q2 = self.get_qubit(position2)
        q1.entangled.add(q2)
        q2.entangled.add(q1)

        self.qs.entangle(position1[0] * 3 + position1[1], position2[0] * 3 + position2[1])

    def measure(self, position1, to_measure=set()):
        q1 = self.get_qubit(position1)
        to_measure.add(q1)
        positions = []
        positions.append(q1.position[0] * 3 + q1.position[1])
        queue = set()
        queue.update(q1.entangled)
        while len(queue) != 0:
            qx = queue.pop()
            if qx not in to_measure:
                to_measure.add(qx)
                positions.append(qx.position[0] * 3 + qx.position[1])
                queue.update(qx.entangled)

        # do the measurement
        result = self.qs.measure(positions)
        print(result)
        # convert results to board X and Os
        for qubit in to_measure:
            idx = qubit.position[0] * 3 + qubit.position[1]
            if result[idx] == 1:
                self.squares[qubit.position[0], qubit.position[1]] = "O"
            elif result[idx] == 0:
                self.squares[qubit.position[0], qubit.position[1]] = "X"

    def show_board(self):
        board = [[], [], []]
        for i in range(self.squares.shape[0]):
            for j in range(self.squares.shape[1]):
                if isinstance(self.squares[i, j], Qubit):
                    board[i].append(str(self.squares[i, j].probability))
                else:
                    board[i].append(str(self.squares[i, j]))
        print('   |   |')

        print(' ' + board[0][0] + ' | ' + board[0][1] + ' | ' + board[0][2])

        print('   |   |')

        print('-----------')

        print('   |   |')

        print(' ' + board[1][0] + ' | ' + board[1][1] + ' | ' + board[1][2])

        print('   |   |')

        print('-----------')

        print('   |   |')

        print(' ' + board[2][0] + ' | ' + board[2][1] + ' | ' + board[2][2])

        print('   |   |')


class Qubit:
    def __init__(self, position: tuple, probability=0.5, entangled=None):
        if entangled is None:
            entangled = set()
        self.position = position
        self.probability = probability
        self.entangled = entangled

    def set_position(self, position):
        self.position = position


# Some function calls
# Board = Board()
# Board.move((0, 0), 2)
# Board.measure((0, 0))
# Board.measure((0, 1))
# Board.measure((2, 2))

# Board.show_board()