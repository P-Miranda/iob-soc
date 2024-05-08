def setup(py_params_dict):
    attributes_dict = {
        "original_name": "iob_pulse_gen",
        "name": "iob_pulse_gen",
        "version": "0.1",
        "generate_hw": True,
        "confs": [
            {
                "name": "START",
                "type": "P",
                "val": "0",
                "min": "0",
                "max": "NA",
                "descr": "",
            },
            {
                "name": "DURATION",
                "type": "P",
                "val": "0",
                "min": "0",
                "max": "NA",
                "descr": "",
            },
            {
                "name": "WIDTH",
                "type": "F",
                "val": "$clog2(START + DURATION + 2)",
                "min": "NA",
                "max": "NA",
                "descr": "",
            },
            {
                "name": "START_INT",
                "type": "F",
                "val": "(START <= 0) ? 0 : START - 1",
                "min": "NA",
                "max": "NA",
                "descr": "",
            },
            {
                "name": "FINISH",
                "type": "F",
                "val": "START_INT + DURATION",
                "min": "NA",
                "max": "NA",
                "descr": "",
            },
        ],
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
                "name": "start",
                "descr": "Input port",
                "signals": [
                    {"name": "start", "width": 1, "direction": "input"},
                ],
            },
            {
                "name": "pulse",
                "descr": "Output port",
                "signals": [
                    {"name": "pulse", "width": 1, "direction": "output"},
                ],
            },
        ],
        "wires": [
            {
                "name": "start_detected",
                "descr": "Start detect wire",
                "signals": [
                    {"name": "start_detected", "width": 1},
                ],
            },
            {
                "name": "start_detected_nxt",
                "descr": "Start detect next wire",
                "signals": [
                    {"name": "start_detected_nxt", "width": 1},
                ],
            },
            {
                "name": "cnt_en",
                "descr": "",
                "signals": [
                    {"name": "cnt_en", "width": 1},
                ],
            },
            {
                "name": "cnt",
                "descr": "",
                "signals": [
                    {"name": "cnt", "width": "WIDTH"},
                ],
            },
            {
                "name": "pulse_nxt",
                "descr": "",
                "signals": [
                    {"name": "pulse_nxt", "width": 1},
                ],
            },
            #################################################
            {
                "name": "start_detected_io",
                "descr": "",
                "signals": [
                    {"name": "start_detected_nxt", "wire": "start_detected_nxt"},
                    {"name": "start_detected", "wire": "start_detected"},
                ],
            },
            {
                "name": "pulse_reg_io",
                "descr": "",
                "signals": [
                    {"name": "pulse_nxt", "wire": "pulse_nxt"},
                    {"name": "pulse", "wire": "pulse"},
                ],
            },
            # FIXME: get_wire_signal is not implemented yet. These 2 directly above will not work ^^^^. Below are the
            # originals.
            # self.create_wire(
            #    name="start_detected_io",
            #    descr="",
            #    signals=[
            #        self.get_wire_signal("start_detected_nxt", "start_detected_nxt"),
            #        self.get_wire_signal("start_detected", "start_detected"),
            #    ],
            # )
            # self.create_wire(
            #    name="pulse_reg_io",
            #    descr="",
            #    signals=[
            #        self.get_wire_signal("pulse_nxt", "pulse_nxt"),
            #        self.get_wire_signal("pulse", "pulse"),
            #    ],
            # )
            #################################################
        ],
        "blocks": [
            {
                "core_name": "iob_reg",
                "instance_name": "start_detected_inst",
            },
            {
                "core_name": "iob_counter",
                "instance_name": "cnt0",
            },
            {
                "core_name": "iob_reg",
                "instance_name": "pulse_reg",
            },
        ],
        "snippets": [
            {
                "outputs": ["start_detected_nxt", "cnt_en", "pulse_nxt"],
                "verilog_code": """
    assign start_detected_nxt = start_detected | start_i;
    assign cnt_en = start_detected & (cnt <= FINISH);
    assign pulse_nxt = cnt_en & (cnt < FINISH) & (cnt >= START_INT);
                """,
            },
        ],
    }

    return attributes_dict