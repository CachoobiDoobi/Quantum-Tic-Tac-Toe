from kivy.lang import Builder
from kivymd.app import MDApp
from Board import Board, Qubit
from quantum_bot import _, X, O, QuantumBot


from kivy.core.text import LabelBase

class TicTacToe(MDApp):
    def build(self):
        # setup theme colors
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "600"

        return Builder.load_file("./UI/UI.kv")



    # global values
    player = 1
    action = "normal"
    first_qubit = None
    board = Board()
    moves = 20
    swap_left = [2,2]

    bot = QuantumBot()
    cboard = [_, _, _, _, _, _, _, _, _]
    computer = False
    turn = 1
    


    def excecute(self, btn, col, row):
        # perform action based on global value
        if self.action == "normal":
            probability = self.board.get_qubit((row, col)).probability

            if (self.player == 1 and probability >= 0.25) or (self.player == 2 and probability <= 0.75):
                self.board.move((row, col), self.player)
                self.first_qubit = None
                self.nextMove()

        elif self.action == "swap":
            if self.first_qubit is not None and self.swap_left[self.player-1] > 0:
                self.board.swap(self.first_qubit, (row, col))
                self.first_qubit = None
                self.swap_left[self.player-1] -= 1
                self.nextMove()
            else:
                self.first_qubit = (row, col)

        elif self.action == "collapse":
            self.first_qubit = None
            self.board.measure((row, col))
            self.nextMove()

        elif self.action == "entangle":
            if self.first_qubit is not None:
                self.board.entangle(self.first_qubit, (row, col))
                self.first_qubit = None
                self.nextMove()
            else:
                self.first_qubit = (row, col)



    def nextMove(self):
        # change the current player
        if self.player == 1:
            self.root.ids.score.text = "O's turn"
            self.player = 2
        else:
            self.root.ids.score.text = "X's turn"
            self.player = 1

        self.root.ids.swap.text = "Swap (" + str(self.swap_left[self.player-1]) + ")"
        self.moves -= 1
        self.root.ids.moves.text = str(self.moves) + " moves left"

        # check win
        if len(self.board.check_win()) == 1:
            self.root.ids.score.text = self.board.check_win().pop() + " wins!"
            for button in self.root.ids.grid.children:
                button.disabled = True
        elif self.moves < 1:
            # collapse if there are no moves left
            qubits = set()
            first = None
            for i in range(3): 
                for j in range(3):
                    if not isinstance(self.board.squares[i, j], str):
                        if first is None: first = (i, j)
                        qubits.add(self.board.squares[i, j])
            self.board.measure(first, qubits)
            


            win = self.board.check_win()
            if ("O" in win and "X" in win) or len(win) is 0:
                self.root.ids.score.text = "It's a tie"
            else:
                self.root.ids.score.text = win.pop() + " wins!"
        

        # array for usable colors
        colors = [[1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 1], [1, 1, 0, 1], [1, 0, 1, 1], [0, 1, 1, 1]]
        colors_index = 0
        qubit_colors = {}


        # go over all the buttons with corresponding qubits
        for button, qubit in zip(self.root.ids.grid.children[::-1], self.board.squares.flatten()):
            if isinstance(qubit, str):
                button.font_name = "Roboto"
                button.text = qubit
                button.disabled = True
                button.text_color = [1, 1, 1, 1]

            else:
                # use the states fond and select the right symbol
                button.font_name = "States"
                if not qubit.entangled:
                    if qubit.probability == 1:
                        button.text = "A"
                    elif qubit.probability == 0:
                        button.text = "B"
                    elif qubit.probability == 0.5:
                        button.text = "C"
                    elif qubit.probability == 0.75:
                        button.text = "D"
                    elif qubit.probability == 0.25:
                        button.text = "E"
                    button.text_color = [1, 1, 1, 1]

                else:
                    # get all the entangled qubits
                    entangled = self.search_entangled(qubit)


                    # setup the colors
                    if str(qubit) in qubit_colors:
                        button.text_color = qubit_colors[str(qubit)]
                    else:
                        new_color = colors[colors_index]
                        colors_index += 1
                        button.text_color = new_color
                        qubit_colors[str(qubit)] = new_color

                        for q in entangled:
                            qubit_colors[str(q)] = new_color


                    # get all the probabilities and set the state symbol
                    probabilities = set()
                    for q in entangled: probabilities.add(q.probability)
                    self.set_text(button, probabilities)
        
        
        self.first_qubit = None



    def cexcecute(self, btn, row, col):
        if not self.check_win(self.cboard):
            # player move
            btn.text = "X"
            btn.disabled = True
            self.cboard[row + col *3] = X

            if not self.check_win(self.cboard) and _ in self.cboard: 
                # quantum computer move
                move = self.bot.find_next_move([X if value == O else O if value == X else _ for value in self.cboard], self.turn)
                self.root.ids.computer_grid.children[::-1][move].text = "O"
                self.root.ids.computer_grid.children[::-1][move].disabled = "True"
                self.cboard[move] = O
                print("board positions: ", self.cboard)
                print("computer move: ", move)
                self.turn += 1

                if self.check_win(self.cboard):
                    self.root.ids.computer_score.text = "Computer has won"
            else:
                if _ not in self.cboard:
                    self.root.ids.computer_score.text = "Tie"
                else:
                    self.root.ids.computer_score.text = "Player has won"

        if self.check_win(self.cboard):
            for button in self.root.ids.computer_grid.children:
                button.disabled = True
            

        
    def check_win(self, board):
        for row in range(3):
            if board[3*row] is board[3*row+1] and board[3*row+1] is board[3*row+2] and board[3*row] is not _: return True

        for column in range(3):
            if board[column] is board[column+3] and board[column+3] is board[column+6] and board[column] is not _: return True

        if board[0] is board[4] and board[4] is board[8] and board[0] is not _: return True
        if board[2] is board[4] and board[4] is board[6] and board[2] is not _: return True
        
        return False

        


    def search_entangled(self, qubit):
        # DFS for getting all the entangled qubits
        queue = set({qubit})
        result = set({qubit})

        while len(queue) is not 0:
            q = queue.pop()
            for qubit in q.entangled:
                if qubit not in result:
                    result.add(qubit)
                    queue.add(qubit)

        return result



    def restart(self):
        # reset all the game elements and go back to main menu
        for button in self.root.ids.grid.children:
            button.disabled = False
            button.font_name = "States"
            button.text = "C"
            button.text_color = [1, 1, 1, 1]

        for button in self.root.ids.computer_grid.children:
            button.disabled = False
            button.text = "_"

        self.root.ids.score.text = "X's turn"
        self.root.ids.moves.text = "20 moves left"
        self.root.ids.computer_score.text = "Player vs Quantum computer"
        self.cboard = [_, _, _, _, _, _, _, _, _]
        self.turn = 1
        self.player = 1
        self.moves = 20
        self.swap_left = [2,2]
        self.board = Board()
        self.root.ids.manager.current = "menu"



    def set_text(self, button, probabilities):
        # switch for displaying the right symbol
        if len(probabilities) is 5:
            button.text = "f"

        elif 1 in probabilities:
            if 0.75 in probabilities:
                if 0.5 in probabilities:
                    if 0.25 in probabilities:
                        button.text = "e"
                    else:
                        button.text = "b"
                elif 0.25 in probabilities:
                    if 0 in probabilities:
                        button.text = "a"
                    else:
                        button.text = "W"
                elif 0 in probabilities:
                    button.text = "R"
                else:
                    button.text = "M"
            elif 0.5 in probabilities:
                if 0.25 in probabilities:
                    if 0 in probabilities:
                        button.text = "c"
                    else:
                        button.text = "Y"
                elif 0 in probabilities:
                    button.text = "Q"
                else:
                    button.text = "K"
                
            elif 0.25 in probabilities:
                if 0 in probabilities:
                    button.text = "S"
                else:
                    button.text = "I"
            elif 0 in probabilities:
                button.text = "F"
            else:
                button.text = "A"
        
        elif 0.75 in probabilities:
            if 0.5 in probabilities:
                if 0.25 in probabilities:
                    if 0 in probabilities:
                        button.text = "d"
                    else:
                        button.text = "X"
                elif 0 in probabilities:
                    button.text = "Z"
                else:
                    button.text = "O"
            elif 0.25 in probabilities:
                if 0 in probabilities:
                    button.text = "V"
                else:
                    button.text = "G"
            elif 0 in probabilities:
                button.text = "J"
            else:
                button.text = "D"
        
        elif 0.5 in probabilities:
            if 0.25 in probabilities:
                if 0 in probabilities:
                    button.text = "T"
                else:
                    button.text = "P"
            elif 0 in probabilities:
                button.text = "L"
            else:
                button.text = "H"

        elif 0.25 in probabilities:
            if 0 in probabilities:
                button.text = "N"
            else:
                button.text = "E"
        else:
            button.text = "B"



    def on_start(self, **kwargs):
        self.restart()

    def start(self):
        if self.computer:
            self.root.ids.manager.current = "computer"
        else:
            self.root.ids.manager.current = "game"

    def checkbox_click(self, instance, value):
        self.computer = value

    def pulse(self):
        self.action = "normal"
        self.reset_actions()
        self.root.ids.pulse.disabled = True

    def swap(self):
        self.action = "swap"
        self.reset_actions()
        self.root.ids.swap.disabled = True

    def entangle(self):
        self.action = "entangle"
        self.reset_actions()
        self.root.ids.entangle.disabled = True

    def collapse(self):
        self.action = "collapse"
        self.reset_actions()
        self.root.ids.collapse.disabled = True

    def reset_actions(self):
        self.root.ids.pulse.disabled = False
        self.root.ids.swap.disabled = False
        self.root.ids.entangle.disabled = False
        self.root.ids.collapse.disabled = False
        self.first_qubit = None



# Start app
LabelBase.register(name='States', fn_regular='./UI/QuantumStates.ttf')
TicTacToe().run()
