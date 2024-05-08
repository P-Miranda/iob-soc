def setup(py_params_dict):
    attributes_dict = {
        "original_name": "iob_div_subshift",
        "name": "iob_div_subshift",
        "version": "0.1",
        "generate_hw": False,
        "ports": [
            {
                "name": "clk_en_rst",
                "type": "slave",
                "port_prefix": "",
                "wire_prefix": "",
                "descr": "Clock, clock enable and reset",
                "signals": [],
            },
            {
                "name": "status",
                "type": "master",
                "port_prefix": "",
                "wire_prefix": "",
                "descr": "",
                "signals": [
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
                "name": "div",
                "type": "master",
                "port_prefix": "",
                "wire_prefix": "",
                "descr": "Division interface",
                "signals": [
                    {
                        "name": "dividend",
                        "direction": "input",
                        "width": "DATA_W",
                        "descr": "",
                    },
                    {
                        "name": "divisor",
                        "direction": "input",
                        "width": "DATA_W",
                        "descr": "",
                    },
                    {
                        "name": "quotient",
                        "direction": "output",
                        "width": "DATA_W",
                        "descr": "",
                    },
                    {
                        "name": "remainder",
                        "direction": "output",
                        "width": "DATA_W",
                        "descr": "",
                    },
                ],
            },
        ],
        "blocks": [
            {
                "core_name": "iob_reg",
                "instance_name": "iob_reg_inst",
            },
        ],
    }

    return attributes_dict