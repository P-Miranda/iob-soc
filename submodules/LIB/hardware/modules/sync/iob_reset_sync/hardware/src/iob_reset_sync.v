`timescale 1ns / 1ps
`include "iob_reg_conf.vh"

module iob_reset_sync (
   input  clk_i,
   input  arst_i,
   output arst_o
);

   wire [1:0] data;
   reg [1:0] sync;

   localparam RST_POL = `IOB_REG_RST_POL;

   generate
      if (RST_POL == 0) begin: gen_rst_pol_0
         assign data = {sync[0], 1'b1};
      end else begin: gen_rst_pol_1
         assign data = {sync[0], 1'b0};
      end
   endgenerate
   
   iob_r #(
           .DATA_W  (2),
           .RST_VAL (2'b0)
           )     
   reg1 (
         .clk_i (clk_i),
         .arst_i (arst_i),
         .data_i(data),
         .data_o(sync)
         );

   assign arst_o = sync[1];
   
endmodule
