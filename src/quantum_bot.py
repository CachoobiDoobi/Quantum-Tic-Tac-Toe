qasm = ""


setup = """version 1.0

qubits 19
"""

board_init = """
{ x q[1, 2, 8] | h q[3, 5, 6, 7] }
h q[18]
z q[18]
"""

horizontal_win = """
toffoli q[0], q[1], q[9]
toffoli q[2], q[9], q[10]
toffoli q[0], q[1], q[9]

toffoli q[3], q[4], q[9]
toffoli q[5], q[9], q[11]
toffoli q[3], q[4], q[9]

toffoli q[6], q[7], q[9]
toffoli q[8], q[9], q[12]
toffoli q[6], q[7], q[9]

x q[10, 11, 12]
toffoli q[10], q[11], q[13]
toffoli q[12], q[13], q[14]
toffoli q[10], q[11], q[13]
x q[10, 11, 12, 14]

toffoli q[6], q[7], q[9]
toffoli q[8], q[9], q[12]
toffoli q[6], q[7], q[9]

toffoli q[3], q[4], q[9]
toffoli q[5], q[9], q[11]
toffoli q[3], q[4], q[9]

toffoli q[0], q[1], q[9]
toffoli q[2], q[9], q[10]
toffoli q[0], q[1], q[9]
"""

vertical_win = """
toffoli q[0], q[3], q[9]
toffoli q[6], q[9], q[10]
toffoli q[0], q[3], q[9]

toffoli q[1], q[4], q[9]
toffoli q[7], q[9], q[11]
toffoli q[1], q[4], q[9]

toffoli q[2], q[5], q[9]
toffoli q[8], q[9], q[12]
toffoli q[2], q[5], q[9]

x q[10, 11, 12]
toffoli q[10], q[11], q[13]
toffoli q[12], q[13], q[15]
toffoli q[10], q[11], q[13]
x q[10, 11, 12, 15]

toffoli q[2], q[5], q[9]
toffoli q[8], q[9], q[12]
toffoli q[2], q[5], q[9]

toffoli q[1], q[4], q[9]
toffoli q[7], q[9], q[11]
toffoli q[1], q[4], q[9]

toffoli q[0], q[3], q[9]
toffoli q[6], q[9], q[10]
toffoli q[0], q[3], q[9]
"""

diagonal_win = """
toffoli q[0], q[4], q[9]
toffoli q[8], q[9], q[10]
toffoli q[0], q[4], q[9]

toffoli q[2], q[4], q[9]
toffoli q[6], q[9], q[11]
toffoli q[2], q[4], q[9]

x q[10, 11]
toffoli q[10], q[11], q[16]
x q[10, 11, 16]

toffoli q[2], q[4], q[9]
toffoli q[6], q[9], q[11]
toffoli q[2], q[4], q[9]

toffoli q[0], q[4], q[9]
toffoli q[8], q[9], q[10]
toffoli q[0], q[4], q[9]
"""


final_or = """
x q[14, 15, 16]
{ toffoli q[14], q[15], q[17] | h q[18] }
toffoli q[16], q[17], q[18]
{ toffoli q[14], q[15], q[17] | x q[18] }
{ x q[14, 15, 16] | h q[18] }
"""

diffuser = """
h q[0:8]
x q[0:8]

toffoli q[0], q[1], q[9]
toffoli q[2], q[9], q[10]
toffoli q[3], q[10], q[11]
toffoli q[4], q[11], q[12]
toffoli q[5], q[12], q[13]
toffoli q[6], q[13], q[14]
toffoli q[7], q[14], q[15]

toffoli q[8], q[15], q[18]

toffoli q[7], q[14], q[15]
toffoli q[6], q[13], q[14]
toffoli q[5], q[12], q[13]
toffoli q[4], q[11], q[12]
toffoli q[3], q[10], q[11]
toffoli q[2], q[9], q[10]
toffoli q[0], q[1], q[9]

x q[0:8]
h q[0:8]
"""

clause_computation = horizontal_win + vertical_win + diagonal_win

grover = clause_computation + final_or + "\n".join(clause_computation.splitlines()[::-1]) + diffuser
qasm = setup + board_init + clause_computation + final_or + "\n".join(clause_computation.splitlines()[::-1]) + diffuser

print(qasm)

# version 1.0

# qubits 17

# .init
# h q[0:8]
# #z q[16]

# .grover(1)
# # oracle
# toffoli q[0], q[1], q[9]
# toffoli q[2], q[9], q[10]
# toffoli q[0], q[1], q[9]

# toffoli q[3], q[4], q[9]
# toffoli q[5], q[9], q[11]
# toffoli q[3], q[4], q[9]

# toffoli q[6], q[7], q[9]
# toffoli q[8], q[9], q[12]
# toffoli q[6], q[7], q[9]

# # AND
# #toffoli q[10], q[11], q[13]
# #toffoli q[12], q[13], q[16]
# #toffoli q[10], q[11], q[13]

# # NAND
# #x q[10, 11, 12]
# #toffoli q[10], q[11], q[13]
# #toffoli q[12], q[13], q[16]
# #toffoli q[10], q[11], q[13]
# #x q[10, 11, 12]

# # OR
# # x q[10, 11]
# # toffoli q[10], q[11], q[13]
# # x q[12]
# # toffoli q[12], q[13], q[15]
# # x q[15]
# # cz q[15], q[16]
# # z q[16]
# # x q[15]
# # toffoli q[12], q[13], q[15]
# # x q[12]
# # toffoli q[10], q[11], q[13]
# # x q[10, 11]

# toffoli q[10], q[11], q[16]
# z q[16]


# toffoli q[6], q[7], q[9]
# toffoli q[8], q[9], q[12]
# toffoli q[6], q[7], q[9]

# toffoli q[3], q[4], q[9]
# toffoli q[5], q[9], q[11]
# toffoli q[3], q[4], q[9]

# toffoli q[0], q[1], q[9]
# toffoli q[2], q[9], q[10]
# toffoli q[0], q[1], q[9]

# # diffuser
# h q[0:8]
# x q[0:8]

# toffoli q[0], q[1], q[9]
# toffoli q[2], q[9], q[10]
# toffoli q[3], q[10], q[11]
# toffoli q[4], q[11], q[12]
# toffoli q[5], q[12], q[13]
# toffoli q[6], q[13], q[14]
# toffoli q[7], q[14], q[15]

# toffoli q[8], q[15], q[16]

# toffoli q[7], q[14], q[15]
# toffoli q[6], q[13], q[14]
# toffoli q[5], q[12], q[13]
# toffoli q[4], q[11], q[12]
# toffoli q[3], q[10], q[11]
# toffoli q[2], q[9], q[10]
# toffoli q[0], q[1], q[9]

# x q[0:8]
# h q[0:8]




## GROVER 1 x 3 [4096 shots]
# version 1.0

# qubits 11

# x q[0]
# h q[3:5, 10]
# z q[10]

# cnot q[0, 1, 2], q[3, 4, 5]

# .grover(2)
# x q[3, 4, 5]
# toffoli q[0, 1], q[3, 4], q[6, 7]
# x q[6, 7]
# toffoli q[6], q[7], q[8]
# x q[6, 7, 8]
# toffoli q[1, 0], q[4, 3], q[7, 6]
# toffoli q[2], q[5], q[7]
# x q[7, 8]
# toffoli q[7], q[8], q[9]
# x q[7, 8, 9]
# toffoli q[2], q[5], q[7]


# toffoli q[0, 1], q[3, 4], q[6, 7]
# x q[6, 7, 8]
# toffoli q[6], q[7], q[8]
# x q[6, 7]
# toffoli q[1, 0], q[4, 3], q[7, 6]
# x q[3, 4, 5]

# toffoli q[3], q[4], q[6]
# toffoli q[4], q[5], q[7]
# x q[6, 7]
# toffoli q[6], q[7], q[8]
# x q[6, 7, 8]
# toffoli q[4], q[5], q[7]
# toffoli q[3], q[4], q[6]

# toffoli q[8], q[9], q[10]

# toffoli q[3], q[4], q[6]
# toffoli q[4], q[5], q[7]
# x q[6, 7, 8]
# toffoli q[6], q[7], q[8]
# x q[6, 7]
# toffoli q[4], q[5], q[7]
# toffoli q[3], q[4], q[6]


# x q[3, 4, 5]
# toffoli q[0, 1], q[3, 4], q[6, 7]
# x q[6, 7]
# toffoli q[6], q[7], q[8]
# x q[6, 7, 8]
# toffoli q[1, 0], q[4, 3], q[7, 6]
# toffoli q[2], q[5], q[7]
# x q[7, 8]
# toffoli q[7], q[8], q[9]
# x q[7, 8, 9]
# toffoli q[2], q[5], q[7]


# toffoli q[0, 1], q[3, 4], q[6, 7]
# x q[6, 7, 8]
# toffoli q[6], q[7], q[8]
# x q[6, 7]
# toffoli q[1, 0], q[4, 3], q[7, 6]
# x q[3, 4, 5]


# h q[3:5]
# x q[3:5]
# toffoli q[3], q[4], q[6]
# toffoli q[5], q[6], q[10]
# toffoli q[3], q[4], q[6]
# x q[3:5]
# h q[3:5]




# ALLOWED MOVES GROVER
# https://algassert.com/quirk#circuit={%22cols%22:[[1,1,1,1,%22H%22,%22H%22,%22H%22,%22H%22],[1,1,1,1,1,1,1,%22Z%22],[1,1,1,1,%22%E2%80%A2%22,%22%E2%97%A6%22,%22%E2%80%A2%22,1,%22X%22],[1,1,1,1,%22%E2%80%A2%22,%22%E2%80%A2%22,%22%E2%97%A6%22,1,1,%22X%22],[1,1,1,1,1,1,1,%22X%22,%22%E2%97%A6%22,%22%E2%97%A6%22],[1,1,1,1,1,1,1,%22X%22],[1,1,1,1,%22Chance4%22],[1,1,1,1,%22%E2%80%A2%22,%22%E2%80%A2%22,%22%E2%97%A6%22,1,1,%22X%22],[1,1,1,1,%22%E2%80%A2%22,%22%E2%97%A6%22,%22%E2%80%A2%22,1,%22X%22],[1,1,1,1,%22H%22,%22H%22,%22H%22],[1,1,1,1,%22%E2%97%A6%22,%22%E2%97%A6%22,%22%E2%97%A6%22,%22X%22],[1,1,1,1,%22H%22,%22H%22,%22H%22],[1,1,1,1,%22%E2%80%A2%22,%22%E2%97%A6%22,%22%E2%80%A2%22,1,%22X%22],[1,1,1,1,%22%E2%80%A2%22,%22%E2%80%A2%22,%22%E2%97%A6%22,1,1,%22X%22],[1,1,1,1,1,1,1,%22X%22,%22%E2%97%A6%22,%22%E2%97%A6%22],[1,1,1,1,1,1,1,%22X%22],[1,1,1,1,%22Chance3%22],[1,1,1,1,%22%E2%80%A2%22,%22%E2%80%A2%22,%22%E2%97%A6%22,1,1,%22X%22],[1,1,1,1,%22%E2%80%A2%22,%22%E2%97%A6%22,%22%E2%80%A2%22,1,%22X%22]]}
#
# version 1.0

# qubits 9

# .init
# h q[0:2, 3]

# z q[3]

# .grover(1)
# # Validate
# x q[1]
# toffoli q[0], q[1], q[4]
# toffoli q[2], q[4], q[5]
# toffoli q[0], q[1], q[4]
# x q[1]


# x q[2]
# toffoli q[0], q[1], q[4]
# toffoli q[2], q[4], q[6]
# toffoli q[0], q[1], q[4]
# x q[2]


# x q[5, 6]
# toffoli q[5], q[6], q[3]
# x q[3, 5, 6]

# # Uncompute Validate
# x q[2]
# toffoli q[0], q[1], q[4]
# toffoli q[2], q[4], q[6]
# toffoli q[0], q[1], q[4]
# x q[2]

# x q[1]
# toffoli q[0], q[1], q[4]
# toffoli q[2], q[4], q[5]
# toffoli q[0], q[1], q[4]
# x q[1]

# # DIFFUSER
# h q[0:2]
# x q[0:2]
# toffoli q[0], q[1], q[4]
# toffoli q[2], q[4], q[3]
# toffoli q[0], q[1], q[4]
# x q[0:2]
# h q[0:2]

# .measurement
# measure_z q[0:2]