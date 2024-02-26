import os

from iob_module import iob_module


class iob_ram_sp(iob_module):
    def __init__(self):
        super().__init__()
        self.name = "iob_ram_sp"
        self.version = "V0.10"
        self.setup_dir = os.path.dirname(__file__)