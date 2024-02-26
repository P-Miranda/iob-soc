import os

from iob_module import iob_module

from iob_reg import iob_reg


class iob_piso_reg(iob_module):
    def __init__(self):
        super().__init__()
        self.name = "iob_piso_reg"
        self.version = "V0.10"
        self.setup_dir = os.path.dirname(__file__)
        self.submodule_list = [
            iob_reg(),
        ]