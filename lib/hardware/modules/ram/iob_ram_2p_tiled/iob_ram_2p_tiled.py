import os

from iob_module import iob_module

from iob_ram_2p import iob_ram_2p


class iob_ram_2p_tiled(iob_module):
    def __init__(self):
        super().__init__()
        self.name = "iob_ram_2p_tiled"
        self.version = "V0.10"
        self.setup_dir = os.path.dirname(__file__)
        self.submodule_list = [
            iob_ram_2p(),
        ]