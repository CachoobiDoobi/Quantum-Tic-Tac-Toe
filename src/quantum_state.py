import os

from projectq import MainEngine
from projectq.backends import ResourceCounter
from projectq.ops import H, All
from projectq.setups import restrictedgateset

from quantuminspire.api import QuantumInspireAPI
from quantuminspire.credentials import get_authentication
from quantuminspire.projectq.backend_qx import QIBackend

QI_URL = os.getenv('API_URL', 'https://api.quantum-inspire.com/')

project_name = 'TicTacToe'
authentication = get_authentication()
qi_api = QuantumInspireAPI(QI_URL, authentication=authentication, project_name=project_name)

class QuantumState:
    'Quantum state manager'

    def __init__(self, size=3):
        """Create a new QuantumState and perform the setup."""
        self.size = size
        self.setup()
    

    def __initialise_qubits(self):
        """Allocate the qubits and place them in the |+> state."""
        self.qubits = self.engine.allocate_qureg(self.size ** 2)
        All(H) | self.qubits

    
    def setup(self):
        """Initialise a new backend, engine and qubit register."""
        self.qi_backend = QIBackend(quantum_inspire_api=qi_api)
        self.compiler_engines = restrictedgateset.get_engine_list(
            one_qubit_gates=self.qi_backend.one_qubit_gates,
            two_qubit_gates=self.qi_backend.two_qubit_gates,
            other_gates=self.qi_backend.three_qubit_gates
        )

        self.compiler_engines.extend([ResourceCounter()])
        self.engine = MainEngine(backend=self.qi_backend, engine_list=self.compiler_engines)

        self.__initialise_qubits()
    

    def reset(self):
        """Flush the current circuit, deallocate the qubits and perform the setup."""
        self.engine.flush(deallocate_qubits=True)
        self.setup()

    
    def get_index(self, position):
        """Convert a 2D (x, y) coordinate into a 1D array index."""
        return max(0, min(self.size ** 2 - 1, position[1] * self.size + position[0]))
