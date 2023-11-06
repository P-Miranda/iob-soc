#!/usr/bin/env python3
#
#    mkregs.py: build Verilog software accessible registers and software getters and setters
#

import sys, os
from math import ceil, log
from latex import write_table
from submodule_utils import eval_param_expression_from_config
import re
import iob_colors


# Use a class for the entire module, as it may be imported multiple times, but must have instance variables (multiple cores/submodules have different registers)
class mkregs:
    def __init__(self):
        self.cpu_n_bytes = 4
        self.core_addr_w = None
        self.config = None

    @staticmethod
    def boffset(n, n_bytes):
        return 8 * (n % n_bytes)

    @staticmethod
    def bfloor(n, log2base):
        base = int(2**log2base)
        if n % base == 0:
            return n
        return base * int(n / base)

    @staticmethod
    def verilog_max(a, b):
        if a == b:
            return a
        try:
            # Assume a and b are int
            a = int(a)
            b = int(b)
            return a if a > b else b
        except ValueError:
            # a or b is a string
            return f"(({a} > {b}) ? {a} : {b})"

    def get_reg_table(self, regs, rw_overlap, autoaddr):
        # Create reg table
        reg_table = []
        for i_regs in regs:
            reg_table += i_regs["regs"]

        return self.compute_addr(reg_table, rw_overlap, autoaddr)

    def bceil(self, n, log2base):
        base = int(2**log2base)
        n = eval_param_expression_from_config(n, self.config, "max")
        # print(f"{n} of {type(n)} and {base}")
        if n % base == 0:
            return n
        else:
            return int(base * ceil(n / base))

    # Calculate numeric value of addr_w, replacing params by their max value
    def calc_addr_w(self, log2n_items, n_bytes):
        return int(
            ceil(
                eval_param_expression_from_config(log2n_items, self.config, "max")
                + log(n_bytes, 2)
            )
        )

    # Generate symbolic expression string to caluclate addr_w in verilog
    @staticmethod
    def calc_verilog_addr_w(log2n_items, n_bytes):
        n_bytes = int(n_bytes)
        try:
            # Assume log2n_items is int
            log2n_items = int(log2n_items)
            return log2n_items + ceil(log(n_bytes, 2))
        except ValueError:
            # log2n_items is a string
            if n_bytes == 1:
                return log2n_items
            else:
                return f"{log2n_items}+{ceil(log(n_bytes,2))}"

    def gen_wr_reg(self, row, f):
        name = row["name"]
        rst_val = int(row["rst_val"])
        n_bits = row["n_bits"]
        log2n_items = row["log2n_items"]
        n_bytes = self.bceil(n_bits, 3) / 8
        if n_bytes == 3:
            n_bytes = 4
        addr = row["addr"]
        addr_w = self.calc_verilog_addr_w(log2n_items, n_bytes)
        auto = row["autoreg"]

        f.write(
            f"\n\n//NAME: {name};\n//TYPE: {row['type']}; WIDTH: {n_bits}; RST_VAL: {rst_val}; ADDR: {addr}; SPACE (bytes): {2**self.calc_addr_w(log2n_items,n_bytes)} (max); AUTO: {auto}\n\n"
        )

        # compute wdata with only the needed bits
        f.write(f"wire [{self.verilog_max(n_bits,1)}-1:0] {name}_wdata; \n")
        f.write(
            f"assign {name}_wdata = iob_wdata_i[{self.boffset(addr,self.cpu_n_bytes)}+:{self.verilog_max(n_bits,1)}];\n"
        )

        # signal to indicate if the register is addressed
        f.write(f"wire {name}_addressed;\n")

        # test if addr and addr_w are int and substitute with their values
        if isinstance(addr, int) and isinstance(addr_w, int):
            f.write(
                f"assign {name}_addressed = (waddr >= {addr}) && (waddr < {addr+2**addr_w});\n"
            )
        else:
            f.write(
                f"assign {name}_addressed = (waddr >= {addr}) && (waddr < ({addr}+(2**({addr_w}))));\n"
            )

        if auto:  # generate register
            # fill remaining bits with 0s
            if isinstance(n_bits, str):
                if rst_val != 0:
                    # get number of bits needed to represent rst_val
                    rst_n_bits = ceil(log(rst_val + 1, 2))
                    zeros_filling = (
                        "{(" + str(n_bits) + "-" + str(rst_n_bits) + "){1'd0}}"
                    )
                    rst_val_str = (
                        "{"
                        + zeros_filling
                        + ","
                        + str(rst_n_bits)
                        + "'d"
                        + str(rst_val)
                        + "}"
                    )
                else:
                    rst_val_str = "{" + str(n_bits) + "{1'd0}}"
            else:
                rst_val_str = str(n_bits) + "'d" + str(rst_val)
            f.write(f"wire {name}_wen;\n")
            f.write(
                f"assign {name}_wen = (iob_avalid_i) & ((|iob_wstrb_i) & {name}_addressed);\n"
            )
            f.write(f"iob_reg_e #(\n")
            f.write(f"  .DATA_W({n_bits}),\n")
            f.write(f"  .RST_VAL({rst_val_str}),\n")
            f.write('  .CLKEDGE("posedge")\n')
            f.write(f") {name}_datareg (\n")
            f.write("  .clk_i  (clk_i),\n")
            f.write("  .cke_i  (cke_i),\n")
            f.write("  .arst_i (arst_i),\n")
            f.write(f"  .en_i   ({name}_wen),\n")
            f.write(f"  .data_i ({name}_wdata),\n")
            f.write(f"  .data_o ({name}_o)\n")
            f.write(");\n")
        else:  # compute wen
            f.write(
                f"assign {name}_wen_o = ({name}_addressed & iob_avalid_i)? |iob_wstrb_i: 1'b0;\n"
            )
            f.write(f"assign {name}_wdata_o = {name}_wdata;\n")

    def gen_rd_reg(self, row, f):
        name = row["name"]
        rst_val = row["rst_val"]
        n_bits = row["n_bits"]
        log2n_items = row["log2n_items"]
        n_bytes = self.bceil(n_bits, 3) / 8
        if n_bytes == 3:
            n_bytes = 4
        addr = row["addr"]
        addr_w = self.calc_verilog_addr_w(log2n_items, n_bytes)
        auto = row["autoreg"]

        f.write(
            f"\n\n//NAME: {name};\n//TYPE: {row['type']}; WIDTH: {n_bits}; RST_VAL: {rst_val}; ADDR: {addr}; SPACE (bytes): {2**self.calc_addr_w(log2n_items,n_bytes)} (max); AUTO: {auto}\n\n"
        )

        if not auto:  # output read enable
            if "W" not in row["type"]:
                f.write(f"wire {name}_addressed;\n")
                f.write(
                    f"assign {name}_addressed = (iob_addr_i >= {addr}) && (iob_addr_i < ({addr}+(2**({addr_w}))));\n"
                )
            f.write(
                f"assign {name}_ren_o = {name}_addressed & iob_avalid_i & (~|iob_wstrb_i);\n"
            )

    # generate ports for swreg module
    def gen_port(self, table, f):
        for row in table:
            name = row["name"]
            n_bits = row["n_bits"]
            auto = row["autoreg"]

            # VERSION is not a register, it is an internal constant
            if name != "VERSION":
                if "W" in row["type"]:
                    if auto:
                        f.write(
                            f"  output [{self.verilog_max(n_bits,1)}-1:0] {name}_o,\n"
                        )
                    else:
                        f.write(
                            f"  output [{self.verilog_max(n_bits,1)}-1:0] {name}_wdata_o,\n"
                        )
                        f.write(f"  output {name}_wen_o,\n")
                        f.write(f"  input {name}_wready_i,\n")
                if "R" in row["type"]:
                    if auto:
                        f.write(
                            f"  input [{self.verilog_max(n_bits,1)}-1:0] {name}_i,\n"
                        )
                    else:
                        f.write(
                            f"  input [{self.verilog_max(n_bits,1)}-1:0] {name}_rdata_i,\n"
                        )
                        f.write(f"  output {name}_ren_o,\n")
                        f.write(f"  input {name}_rready_i,\n")

    # auxiliar read register case name
    def aux_read_reg_case_name(self, row):
        aux_read_reg_case_name = ""
        if "R" in row["type"]:
            addr = row["addr"]
            n_bits = row["n_bits"]
            log2n_items = row["log2n_items"]
            n_bytes = int(self.bceil(n_bits, 3) / 8)
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            addr_w_base = max(log(self.cpu_n_bytes, 2), addr_w)
            aux_read_reg_case_name = f"iob_addr_i_{self.bfloor(addr, addr_w_base)}_{self.boffset(addr, self.cpu_n_bytes)}"
        return aux_read_reg_case_name

    # generate wires to connect instance in top module
    def gen_inst_wire(self, table, f):
        for row in table:
            name = row["name"]
            n_bits = row["n_bits"]
            auto = row["autoreg"]

            # VERSION is not a register, it is an internal constant
            if name != "VERSION":
                if "W" in row["type"]:
                    if auto:
                        f.write(f"wire [{self.verilog_max(n_bits,1)}-1:0] {name}_wr;\n")
                    else:
                        f.write(
                            f"wire [{self.verilog_max(n_bits,1)}-1:0] {name}_wdata_wr;\n"
                        )
                        f.write(f"wire {name}_wen_wr;\n")
                        f.write(f"wire {name}_wready_wr;\n")
                if "R" in row["type"]:
                    if auto:
                        f.write(f"wire [{self.verilog_max(n_bits,1)}-1:0] {name}_rd;\n")
                    else:
                        f.write(
                            f"wire [{self.verilog_max(n_bits,1)}-1:0] {name}_rdata_rd;\n"
                        )
                        f.write(f"wire {name}_ren_rd;\n")
                        f.write(f"wire {name}_rready_rd;\n")
        f.write("\n")

    # generate portmap for swreg instance in top module
    def gen_portmap(self, table, f):
        for row in table:
            name = row["name"]
            auto = row["autoreg"]

            # VERSION is not a register, it is an internal constant
            if name != "VERSION":
                if "W" in row["type"]:
                    if auto:
                        f.write(f"  .{name}_o({name}_wr),\n")
                    else:
                        f.write(f"  .{name}_wdata_o({name}_wdata_wr),\n")
                        f.write(f"  .{name}_wen_o({name}_wen_wr),\n")
                        f.write(f"  .{name}_wready_i({name}_wready_wr),\n")
                if "R" in row["type"]:
                    if auto:
                        f.write(f"  .{name}_i({name}_rd),\n")
                    else:
                        f.write(f"  .{name}_rdata_i({name}_rdata_rd),\n")
                        f.write(f"  .{name}_ren_o({name}_ren_rd),\n")
                        f.write(f"  .{name}_rready_i({name}_rready_rd),\n")

    def write_hwcode(self, table, out_dir, top):
        #
        # SWREG INSTANCE
        #

        os.makedirs(out_dir, exist_ok=True)
        f_inst = open(f"{out_dir}/{top}_swreg_inst.vs", "w")

        # connection wires
        self.gen_inst_wire(table, f_inst)

        f_inst.write(f"{top}_swreg_gen #(\n")
        f_inst.write(f'  `include "{top}_inst_params.vs"\n')
        f_inst.write("\n) swreg_0 (\n")
        self.gen_portmap(table, f_inst)
        f_inst.write('  `include "iob_s_portmap.vs"\n')
        f_inst.write("  .clk_i(clk_i),\n")
        f_inst.write("  .cke_i(cke_i),\n")
        f_inst.write("  .arst_i(arst_i)\n")

        f_inst.write("\n);\n")

        #
        # SWREG MODULE
        #

        f_gen = open(f"{out_dir}/{top}_swreg_gen.v", "w")

        # time scale
        f_gen.write("`timescale 1ns / 1ps\n\n")

        # iob utils
        f_gen.write(f'`include "iob_utils.vh"\n')

        # macros
        f_gen.write(f'`include "{top}_conf.vh"\n')
        f_gen.write(f'`include "{top}_swreg_def.vh"\n\n')

        # declaration
        f_gen.write(f"module {top}_swreg_gen\n")

        # parameters
        f_gen.write("#(\n")
        f_gen.write(f'`include "{top}_params.vs"\n')
        f_gen.write(")\n")
        f_gen.write("(\n")

        # ports
        self.gen_port(table, f_gen)
        f_gen.write('  `include "iob_s_port.vs"\n')
        f_gen.write("  //General Interface Signals\n")
        f_gen.write("  input clk_i,\n")
        f_gen.write("  input cke_i,\n")
        f_gen.write("  input arst_i\n")

        f_gen.write(");\n\n")

        # write address
        f_gen.write("\n//write address\n")

        # extract address byte offset
        f_gen.write(f"wire [($clog2(DATA_W/8)+1)-1:0] byte_offset;\n")
        f_gen.write(
            f"iob_ctls #(.W(DATA_W/8), .MODE(0), .SYMBOL(0)) bo_inst (.data_i(iob_wstrb_i), .count_o(byte_offset));\n"
        )

        # compute write address
        f_gen.write(f"wire [ADDR_W-1:0] waddr;\n")
        f_gen.write(f"assign waddr = `IOB_WORD_ADDR(iob_addr_i) + byte_offset;\n")

        # insert write register logic
        for row in table:
            if "W" in row["type"]:
                self.gen_wr_reg(row, f_gen)

        # insert read register logic
        for row in table:
            if "R" in row["type"]:
                self.gen_rd_reg(row, f_gen)

        #
        # RESPONSE SWITCH
        #
        f_gen.write("\n\n//RESPONSE SWITCH\n")

        # use variables to compute response
        f_gen.write(f"\n reg [{8*self.cpu_n_bytes}-1:0] rdata_int;\n")
        f_gen.write(f"wire rvalid_int;\n")
        f_gen.write(f"reg wready_int;\n")
        f_gen.write(f"reg rready_int;\n\n")

        # auxiliar read register cases
        for row in table:
            if "R" in row["type"]:
                aux_read_reg = self.aux_read_reg_case_name(row)
                if aux_read_reg:
                    f_gen.write(f"reg {aux_read_reg};\n")
        f_gen.write("\n")

        f_gen.write("reg ready_int;\n")

        # rvalid output
        f_gen.write("//rvalid output\n")
        f_gen.write("reg rvalid_nxt;\n")
        f_gen.write("iob_reg #( \n")
        f_gen.write("  .DATA_W (1),\n")
        f_gen.write("  .RST_VAL (1'd0),\n")
        f_gen.write('  .CLKEDGE ("posedge")\n')
        f_gen.write(") rvalid_reg_inst (\n")
        f_gen.write("  .clk_i  (clk_i),\n")
        f_gen.write("  .cke_i  (cke_i),\n")
        f_gen.write("  .arst_i (arst_i),\n")
        f_gen.write("  .data_i (rvalid_nxt),\n")
        f_gen.write("  .data_o (iob_rvalid_o)\n")
        f_gen.write(");\n\n")

        f_gen.write("always @* begin\n")

        f_gen.write(f"  rdata_int = {8*self.cpu_n_bytes}'d0;\n")
        f_gen.write(f"  rready_int = 1'b1;\n")
        f_gen.write(f"  wready_int = 1'b1;\n\n")

        # read register response
        for row in table:
            name = row["name"]
            addr = row["addr"]
            n_bits = row["n_bits"]
            log2n_items = row["log2n_items"]
            n_bytes = int(self.bceil(n_bits, 3) / 8)
            if n_bytes == 3:
                n_bytes = 4
            addr_last = int(
                addr
                + (
                    (
                        2
                        ** eval_param_expression_from_config(
                            log2n_items, self.config, "max"
                        )
                    )
                )
                * n_bytes
            )
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            addr_w_base = max(log(self.cpu_n_bytes, 2), addr_w)
            auto = row["autoreg"]

            if "R" in row["type"]:
                aux_read_reg = self.aux_read_reg_case_name(row)

                if self.bfloor(addr, addr_w_base) == self.bfloor(
                    addr_last, addr_w_base
                ):
                    f_gen.write(
                        f"  {aux_read_reg} = (`IOB_WORD_ADDR(iob_addr_i) == {self.bfloor(addr, addr_w_base)});\n"
                    )
                    f_gen.write(f"  if({aux_read_reg}) ")
                else:
                    f_gen.write(
                        f"  {aux_read_reg} = (`IOB_WORD_ADDR(iob_addr_i) >= {self.bfloor(addr, addr_w_base)} && `IOB_WORD_ADDR(iob_addr_i) < {self.bfloor(addr_last, addr_w_base)});\n"
                    )
                    f_gen.write(f"  if({aux_read_reg}) ")
                f_gen.write(f"begin\n")
                if name == "VERSION":
                    rst_val = row["rst_val"]
                    f_gen.write(
                        f"    rdata_int[{self.boffset(addr, self.cpu_n_bytes)}+:{8*n_bytes}] = 16'h{rst_val}|{8*n_bytes}'d0;\n"
                    )
                elif auto:
                    f_gen.write(
                        f"    rdata_int[{self.boffset(addr, self.cpu_n_bytes)}+:{8*n_bytes}] = {name}_i|{8*n_bytes}'d0;\n"
                    )
                else:
                    f_gen.write(
                        f"    rdata_int[{self.boffset(addr, self.cpu_n_bytes)}+:{8*n_bytes}] = {name}_rdata_i|{8*n_bytes}'d0;\n"
                    )
                if not auto:
                    f_gen.write(f"    rready_int = {name}_rready_i;\n")
                f_gen.write(f"  end\n\n")

        # write register response
        for row in table:
            name = row["name"]
            addr = row["addr"]
            n_bits = row["n_bits"]
            log2n_items = row["log2n_items"]
            n_bytes = int(self.bceil(n_bits, 3) / 8)
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            auto = row["autoreg"]

            if "W" in row["type"]:
                if not auto:
                    # get wready
                    f_gen.write(
                        f"  if((waddr >= {addr}) && (waddr < {addr + 2**addr_w})) begin\n"
                    )
                    f_gen.write(f"    wready_int = {name}_wready_i;\n  end\n")

        f_gen.write("  ready_int = (|iob_wstrb_i)? wready_int: rready_int;\n")

        f_gen.write("end //always @*\n\n")

        # iob_ready_o output
        f_gen.write("assign iob_ready_o = ready_int;\n\n")

        # iob_rdata_o output
        f_gen.write("assign iob_rdata_o = rdata_int;\n\n")

        # rvalid computation
        f_gen.write(
            "assign rvalid_nxt = (iob_avalid_i & iob_ready_o) & (~(|iob_wstrb_i));\n\n"
        )

        f_gen.write("endmodule\n")
        f_gen.close()
        f_inst.close()

    # Generate *_swreg_lparam.vs file. Macros from this file contain the default values of the registers. These should not be used inside the instance of the core/system.
    def write_lparam_header(self, table, out_dir, top):
        os.makedirs(out_dir, exist_ok=True)
        f_def = open(f"{out_dir}/{top}_swreg_lparam.vs", "w")
        f_def.write("//used address space width\n")
        addr_w_prefix = f"{top}_swreg".upper()
        f_def.write(f"localparam {addr_w_prefix}_ADDR_W = {self.core_addr_w};\n\n")
        f_def.write("//These macros only contain default values for the registers\n")
        f_def.write("//address macros\n")
        macro_prefix = f"{top}_".upper()
        f_def.write("//addresses\n")
        for row in table:
            name = row["name"]
            n_bits = row["n_bits"]
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            log2n_items = row["log2n_items"]
            addr_w = int(
                ceil(
                    eval_param_expression_from_config(log2n_items, self.config, "val")
                    + log(n_bytes, 2)
                )
            )
            f_def.write(f"localparam {macro_prefix}{name}_ADDR = {row['addr']};\n")
            if eval_param_expression_from_config(log2n_items, self.config, "val") > 0:
                f_def.write(f"localparam {macro_prefix}{name}_ADDR_W = {addr_w};\n")
            f_def.write(
                f"localparam {macro_prefix}{name}_W = {eval_param_expression_from_config(n_bits, self.config,'val')};\n\n"
            )
        f_def.close()

    # Generate *_swreg_def.vh file. Macros from this file should only be used inside the instance of the core/system since they may contain parameters which are only known by the instance.
    def write_hwheader(self, table, out_dir, top):
        os.makedirs(out_dir, exist_ok=True)
        f_def = open(f"{out_dir}/{top}_swreg_def.vh", "w")
        f_def.write("//used address space width\n")
        addr_w_prefix = f"{top}_swreg".upper()
        f_def.write(f"`define {addr_w_prefix}_ADDR_W {self.core_addr_w}\n\n")
        f_def.write("//These macros may be dependent on instance parameters\n")
        f_def.write("//address macros\n")
        macro_prefix = f"{top}_".upper()
        f_def.write("//addresses\n")
        for row in table:
            name = row["name"]
            n_bits = row["n_bits"]
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            log2n_items = row["log2n_items"]
            f_def.write(f"`define {macro_prefix}{name}_ADDR {row['addr']}\n")
            if eval_param_expression_from_config(log2n_items, self.config, "max") > 0:
                f_def.write(
                    f"`define {macro_prefix}{name}_ADDR_W {self.verilog_max(self.calc_verilog_addr_w(log2n_items,n_bytes),1)}\n"
                )
            f_def.write(
                f"`define {macro_prefix}{name}_W {self.verilog_max(n_bits,1)}\n\n"
            )
        f_def.close()

    # Get C type from swreg n_bytes
    # uses unsigned int types from C stdint library
    @staticmethod
    def swreg_type(name, n_bytes):
        type_dict = {1: "uint8_t", 2: "uint16_t", 4: "uint32_t", 8: "uint64_t"}
        try:
            type_try = type_dict[n_bytes]
        except:
            print(
                f"{iob_colors.FAIL}register {name} has invalid number of bytes {n_bytes}.{iob_colors.ENDC}"
            )
            type_try = -1
        return type_try

    def write_swheader(self, table, out_dir, top):
        os.makedirs(out_dir, exist_ok=True)
        fswhdr = open(f"{out_dir}/{top}_swreg.h", "w")

        core_prefix = f"{top}_".upper()

        fswhdr.write(f"#ifndef H_{core_prefix}SWREG_H\n")
        fswhdr.write(f"#define H_{core_prefix}SWREG_H\n\n")
        fswhdr.write("#include <stdint.h>\n\n")

        fswhdr.write("//used address space width\n")
        fswhdr.write(f"#define  {core_prefix}SWREG_ADDR_W {self.core_addr_w}\n\n")

        fswhdr.write("//Addresses\n")
        for row in table:
            name = row["name"]
            if "W" in row["type"] or "R" in row["type"]:
                fswhdr.write(f"#define {core_prefix}{name}_ADDR {row['addr']}\n")

        fswhdr.write("\n//Data widths (bit)\n")
        for row in table:
            name = row["name"]
            n_bits = row["n_bits"]
            n_bytes = int(self.bceil(n_bits, 3) / 8)
            if n_bytes == 3:
                n_bytes = 4
            if "W" in row["type"] or "R" in row["type"]:
                fswhdr.write(f"#define {core_prefix}{name}_W {n_bytes*8}\n")

        fswhdr.write("\n// Base Address\n")
        fswhdr.write(f"void {core_prefix}INIT_BASEADDR(uint32_t addr);\n")

        fswhdr.write("\n// Core Setters and Getters\n")
        for row in table:
            name = row["name"]
            n_bits = row["n_bits"]
            log2n_items = row["log2n_items"]
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            if "W" in row["type"]:
                sw_type = self.swreg_type(name, n_bytes)
                addr_arg = ""
                if addr_w / n_bytes > 1:
                    addr_arg = ", int addr"
                fswhdr.write(
                    f"void {core_prefix}SET_{name}({sw_type} value{addr_arg});\n"
                )
            if "R" in row["type"]:
                sw_type = self.swreg_type(name, n_bytes)
                addr_arg = ""
                if addr_w / n_bytes > 1:
                    addr_arg = "int addr"
                fswhdr.write(f"{sw_type} {core_prefix}GET_{name}({addr_arg});\n")

        fswhdr.write(f"\n#endif // H_{core_prefix}_SWREG_H\n")

        fswhdr.close()

    def write_swcode(self, table, out_dir, top):
        os.makedirs(out_dir, exist_ok=True)
        fsw = open(f"{out_dir}/{top}_swreg_emb.c", "w")
        core_prefix = f"{top}_".upper()
        fsw.write(f'#include "{top}_swreg.h"\n\n')
        fsw.write("\n// Base Address\n")
        fsw.write("static int base;\n")
        fsw.write(f"void {core_prefix}INIT_BASEADDR(uint32_t addr) {{\n")
        fsw.write("  base = addr;\n")
        fsw.write("}\n")

        fsw.write("\n// Core Setters and Getters\n")

        for row in table:
            name = row["name"]
            n_bits = row["n_bits"]
            log2n_items = row["log2n_items"]
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            if "W" in row["type"]:
                sw_type = self.swreg_type(name, n_bytes)
                addr_arg = ""
                addr_arg = ""
                addr_shift = ""
                if addr_w / n_bytes > 1:
                    addr_arg = ", int addr"
                    addr_shift = f" + (addr << {int(log(n_bytes, 2))})"
                fsw.write(
                    f"void {core_prefix}SET_{name}({sw_type} value{addr_arg}) {{\n"
                )
                fsw.write(
                    f"  (*( (volatile {sw_type} *) ( (base) + ({core_prefix}{name}_ADDR){addr_shift}) ) = (value));\n"
                )
                fsw.write("}\n\n")
            if "R" in row["type"]:
                sw_type = self.swreg_type(name, n_bytes)
                addr_arg = ""
                addr_shift = ""
                if addr_w / n_bytes > 1:
                    addr_arg = "int addr"
                    addr_shift = f" + (addr << {int(log(n_bytes, 2))})"
                fsw.write(f"{sw_type} {core_prefix}GET_{name}({addr_arg}) {{\n")
                fsw.write(
                    f"  return (*( (volatile {sw_type} *) ( (base) + ({core_prefix}{name}_ADDR){addr_shift}) ));\n"
                )
                fsw.write("}\n\n")
        fsw.close()

    # check if address is aligned
    @staticmethod
    def check_alignment(addr, addr_w):
        if addr % (2**addr_w) != 0:
            sys.exit(
                f"{iob_colors.FAIL}address {addr} with span {2**addr_w} is not aligned{iob_colors.ENDC}"
            )

    # check if address overlaps with previous
    @staticmethod
    def check_overlap(addr, addr_type, read_addr, write_addr):
        if addr_type == "R" and addr < read_addr:
            sys.exit(
                f"{iob_colors.FAIL}read address {addr} overlaps with previous addresses{iob_colors.ENDC}"
            )
        elif addr_type == "W" and addr < write_addr:
            sys.exit(
                f"{iob_colors.FAIL}write address {addr} overlaps with previous addresses{iob_colors.ENDC}"
            )

    # check autoaddr configuration
    @staticmethod
    def check_autoaddr(autoaddr, row):
        is_version = row["name"] == "VERSION"
        if is_version:
            # VERSION has always automatic address
            return -1

        # invalid autoaddr + register addr configurations
        if autoaddr and ("addr" in row):
            sys.exit(
                f"{iob_colors.FAIL}Manual address in register named {row['name']} while in auto address mode.{iob_colors.ENDC}"
            )
        if (not autoaddr) and ("addr" not in row):
            sys.exit(
                f"{iob_colors.FAIL}Missing address in register named {row['name']} while in manual address mode.{iob_colors.ENDC}"
            )

        if autoaddr:
            return -1
        else:
            return row["addr"]

    # compute address
    def compute_addr(self, table, rw_overlap, autoaddr):
        read_addr = 0
        write_addr = 0

        tmp = []

        for row in table:
            addr = self.check_autoaddr(autoaddr, row)
            addr_type = row["type"]
            n_bits = row["n_bits"]
            log2n_items = row["log2n_items"]
            n_bytes = self.bceil(n_bits, 3) / 8
            if n_bytes == 3:
                n_bytes = 4
            addr_w = self.calc_addr_w(log2n_items, n_bytes)
            if addr >= 0:  # manual address
                self.check_alignment(addr, addr_w)
                self.check_overlap(addr, addr_type, read_addr, write_addr)
                addr_tmp = addr
            elif "R" in addr_type:  # auto address
                read_addr = self.bceil(read_addr, addr_w)
                addr_tmp = read_addr
            elif "W" in addr_type:
                write_addr = self.bceil(write_addr, addr_w)
                addr_tmp = write_addr
            else:
                sys.exit(
                    f"{iob_colors.FAIL}invalid address type {addr_type} for register named {row['name']}{iob_colors.ENDC}"
                )

            if not rw_overlap:
                addr_tmp = max(read_addr, write_addr)

            # save address temporarily in list
            tmp.append(addr_tmp)

            # update addresses
            addr_tmp += 2**addr_w
            if "R" in addr_type:
                read_addr = addr_tmp
            elif "W" in addr_type:
                write_addr = addr_tmp
            if not rw_overlap:
                read_addr = addr_tmp
                write_addr = addr_tmp

        # update reg addresses
        for i in range(len(tmp)):
            table[i]["addr"] = tmp[i]

        # update core address space size
        self.core_addr_w = int(ceil(log(max(read_addr, write_addr), 2)))

        return table

    # Generate swreg.tex file with list TeX tables of regs
    @staticmethod
    def generate_swreg_tex(regs, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        swreg_file = open(f"{out_dir}/swreg.tex", "w")

        swreg_file.write(
            """
    The software accessible registers of the core are described in the following
    tables. The tables give information on the name, read/write capability, address, width in bits, and a textual description.
    """
        )

        for table in regs:
            swreg_file.write(
                """
    \\begin{table}[H]
      \centering
      \\begin{tabularx}{\\textwidth}{|l|c|c|c|c|X|}
        
        \hline
        \\rowcolor{iob-green}
        {\\bf Name} & {\\bf R/W} & {\\bf Addr} & {\\bf Width} & {\\bf Default} & {\\bf Description} \\\\ \hline

        \input """
                + table["name"]
                + """_swreg_tab
     
      \end{tabularx}
      \caption{"""
                + table["descr"].replace("_", "\_")
                + """}
      \label{"""
                + table["name"]
                + """_swreg_tab:is}
    \end{table}
    """
            )

        swreg_file.write("\clearpage")
        swreg_file.close()

    # Generate TeX tables of registers
    # regs: list of tables containing registers, as defined in <corename>_setup.py
    # regs_with_addr: list of all registers, where 'addr' field has already been computed
    # out_dir: output directory
    @classmethod
    def generate_regs_tex(cls, regs, regs_with_addr, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        # Create swreg.tex file
        cls.generate_swreg_tex(regs, out_dir)

        for table in regs:
            tex_table = []
            for reg in table["regs"]:
                # Find address of matching register in regs_with_addr list
                addr = next(
                    register["addr"]
                    for register in regs_with_addr
                    if register["name"] == reg["name"]
                )
                tex_table.append(
                    [
                        reg["name"],
                        reg["type"],
                        str(addr),
                        str(reg["n_bits"]),
                        str(reg["rst_val"]),
                        reg["descr"],
                    ]
                )

            write_table(f"{out_dir}/{table['name']}_swreg", tex_table)