import os

from iob_module import iob_module


class iob2axil(iob_module):
    def __init__(self):
        super().__init__()
        self.name = "iob2axil"
        self.version = "V0.10"
        self.setup_dir = os.path.dirname(__file__)