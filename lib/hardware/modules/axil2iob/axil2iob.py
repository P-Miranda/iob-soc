import os

from iob_module import iob_module

from iob_reg_e import iob_reg_e


class axil2iob(iob_module):
    def __init__(self):
        super().__init__()
        self.name = "axil2iob"
        self.version = "V0.10"
        self.setup_dir = os.path.dirname(__file__)
        self.submodule_list = [
            iob_reg_e(),
        ]