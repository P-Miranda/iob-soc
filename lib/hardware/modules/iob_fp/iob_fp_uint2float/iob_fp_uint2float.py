import os

from iob_module import iob_module

from iob_fp_dq import iob_fp_dq


class iob_fp_uint2float(iob_module):
    def __init__(self):
        self.name = "iob_fp_uint2float"
        self.version = "V0.10"
        self.setup_dir = os.path.dirname(__file__)
        self.submodules_list = [iob_fp_dq]
