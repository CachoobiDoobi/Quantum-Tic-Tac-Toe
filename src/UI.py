from random import random
from tkinter import DISABLED
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivy.clock import Clock
from Board import Board

from kivy.core.text import LabelBase

class TicTacToe(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "600"
        # Window.borderless = True

        self.board = Board()
        self.Computer = False

        return Builder.load_file("./UI/UI.kv")

    # player 1 is 'X', player 2 is 'O'
    player = 1

    action = "normal"
    first_qubit = None

    def excecute(self, btn, col, row):

        if self.action == "normal":
            
            probability = self.board.get_qubit((row, col)).probability

            if (self.player == 1 and probability >= 0.25) or (self.player == 2 and probability <= 0.75):
                self.board.move((row, col), self.player)
                self.first_qubit = None
                self.nextMove()

        elif self.action == "swap":
            if self.first_qubit is not None:
                self.board.swap(self.first_qubit, (row, col))
                self.first_qubit = None
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

    def nextMove(self):
        if self.player == 1:
            self.root.ids.score.text = "O's turn"
            self.player = 2
        else:
            self.root.ids.score.text = "X's turn"
            self.player = 1

        
        # dict for entangled colors
        qubits = {}

        for button, qubit in zip(self.root.ids.grid.children[::-1], self.board.squares.flatten()):
            if isinstance(qubit, str):
                button.font_name = "Roboto"
                button.text = qubit
                button.disabled = True
                button.text_color = [1, 1, 1, 1]
            else:
                
                button.font_name = "States"
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


                if qubit.entangled:

                    if str(qubit) in qubits:
                        button.text_color = qubits[str(qubit)]
                    else:
                        new_color = [random(), random(), random(), 1]
                        button.text_color = new_color
                        qubits[str(qubit)] = new_color

                        # are we doing more than 1 entangled qubit?
                        for entangled in qubit.entangled:
                            qubits[str(entangled)] = new_color

                    if qubit.probability == 1:
                        if next(iter(qubit.entangled)).probability == 1: button.text = "A"
                        if next(iter(qubit.entangled)).probability == 0: button.text = "F" 
                        if next(iter(qubit.entangled)).probability == 0.25: button.text = "I" 
                        if next(iter(qubit.entangled)).probability == 0.5: button.text = "L" 
                        if next(iter(qubit.entangled)).probability == 0.75: button.text = "N" 
                        
                    elif qubit.probability == 0:
                        if next(iter(qubit.entangled)).probability == 0: button.text = "B" 
                        if next(iter(qubit.entangled)).probability == 1: button.text = "F"
                        if next(iter(qubit.entangled)).probability == 0.25: button.text = "O" 
                        if next(iter(qubit.entangled)).probability == 0.5: button.text = "M" 
                        if next(iter(qubit.entangled)).probability == 0.75: button.text = "J" 

                    elif qubit.probability == 0.5:
                        if next(iter(qubit.entangled)).probability == 0: button.text = "M" 
                        if next(iter(qubit.entangled)).probability == 1: button.text = "L"
                        if next(iter(qubit.entangled)).probability == 0.25: button.text = "O" # forgot this one
                        if next(iter(qubit.entangled)).probability == 0.5: button.text = "H" 
                        if next(iter(qubit.entangled)).probability == 0.75: button.text = "J" # and this one

                    elif qubit.probability == 0.75:
                        if next(iter(qubit.entangled)).probability == 0: button.text = "J" 
                        if next(iter(qubit.entangled)).probability == 1: button.text = "N"
                        if next(iter(qubit.entangled)).probability == 0.25: button.text = "K" 
                        if next(iter(qubit.entangled)).probability == 0.5: button.text = "M" # same
                        if next(iter(qubit.entangled)).probability == 0.75: button.text = "D" # could also have one

                    elif qubit.probability == 0.25:
                        if next(iter(qubit.entangled)).probability == 0: button.text = "O" 
                        if next(iter(qubit.entangled)).probability == 1: button.text = "I"
                        if next(iter(qubit.entangled)).probability == 0.25: button.text = "E" # also
                        if next(iter(qubit.entangled)).probability == 0.5: button.text = "M" # doesn't exist
                        if next(iter(qubit.entangled)).probability == 0.75: button.text = "G" # K and G are the same


        self.board.check_win()  
        self.root.ids.score.text = "X's turn"
                    
                

        self.first_qubit = None


    
    def checkbox_click(self, instance, value):
        self.Computer = value

    def restart(self):
        self.player = 1

        for button in self.root.ids.grid.children:
            button.disabled = False
            button.font_name = "States"
            button.text = "C"
            button.text_color = [1, 1, 1, 1]

        self.board = Board()

        self.root.ids.manager.current = "menu"


LabelBase.register(name='States', fn_regular='./UI/QuantumStates.ttf')
Clock.max_iteration = 1000

TicTacToe().run()
