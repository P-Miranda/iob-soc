def setup(py_params_dict):
    attributes_dict = {
        "original_name": "iob_mul_addshift",
        "name": "iob_mul_addshift",
        "version": "0.1",
        "generate_hw": False,
        "ports": [
            {
                "name": "clk_en_rst",
                "interface": {
                    "type": "clk_en_rst",
                    "subtype": "slave",
                },
                "descr": "Clock, clock enable and reset",
            },
            {
                "name": "status",
                "descr": "",
                "signals": [
                    {
                        "name": "rst",
                        "direction": "input",
                        "width": 1,
                        "descr": "Synchronous reset",
                    },
                    {
                        "name": "start",
                        "direction": "input",
                        "width": 1,
                        "descr": "Start signal",
                    },
                    {
                        "name": "done",
                        "direction": "output",
                        "width": 1,
                        "descr": "Done signal",
                    },
                ],
            },
            {
                "name": "mul",
                "descr": "Multiplication interface",
                "signals": [
                    {
                        "name": "multiplicand",
                        "direction": "input",
                        "width": "DATA_W",
                        "descr": "",
                    },
                    {
                        "name": "multiplier",
                        "direction": "input",
                        "width": "DATA_W",
                        "descr": "",
                    },
                    {
                        "name": "product",
                        "direction": "output",
                        "width": "2*DATA_W",
                        "descr": "",
                    },
                ],
            },
        ],
        "blocks": [
            {
                "core_name": "iob_reg_re",
                "instance_name": "iob_reg_re_inst",
            },
            {
                "core_name": "iob_counter",
                "instance_name": "iob_counter_inst",
            },
        ],
    }

    return attributes_dict
