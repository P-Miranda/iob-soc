# SPDX-FileCopyrightText: 2024 IObundle
#
# SPDX-License-Identifier: MIT

def setup(py_params_dict):
    attributes_dict = {
        "original_name": "iob_gray_counter",
        "name": "iob_gray_counter",
        "version": "0.1",
        "generate_hw": False,
        "ports": [
            {
                "name": "clk_en_rst_s",
                "interface": {
                    "type": "clk_en_rst",
                    "subtype": "slave",
                },
                "descr": "Clock, clock enable and reset",
            },
            # TODO: Remaining ports
        ],
        "blocks": [
            {
                "core_name": "iob_reg_re",
                "instance_name": "iob_reg_re_inst",
            },
        ],
    }

    return attributes_dict
