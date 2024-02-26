import os

from iob_module import iob_module

from iob_reg_r import iob_reg_r
from iob_reg import iob_reg
from iob_counter import iob_counter
from iob_asym_converter import iob_asym_converter
from iob_ram_2p import iob_ram_2p
from iob_utils import iob_utils


class iob_fifo_sync(iob_module):
    def __init__(self):
        super().__init__()
        self.name = "iob_fifo_sync"
        self.version = "V0.10"
        self.setup_dir = os.path.dirname(__file__)
        self.submodule_list = [
            iob_reg_r(),
            iob_reg(),
            iob_counter(),
            iob_asym_converter(),
            iob_utils(),
            (iob_ram_2p(), {"purpose": "simulation"}),
        ]