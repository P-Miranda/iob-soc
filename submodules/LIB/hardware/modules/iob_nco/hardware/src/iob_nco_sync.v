`timescale 1ns / 1ps
`include "iob_nco_conf.vh"
`include "iob_nco_swreg_def.vh"

module iob_nco_sync #(
    parameter PERIOD_W = 0
) (
    input clk_i,
    input cke_i,
    input arst_i,

    input clk_in_i,

    input soft_reset_i,
    input enable_i,
    input [PERIOD_W-1:0] period_wdata_i,
    input period_wen_i,

    output soft_reset_o,
    output enable_o,
    output [PERIOD_W-1:0] period_wdata_o,
    output period_wen_o
);

   //synchronize CSR clock to clk_in_i clock
   iob_sync #(
       .DATA_W(1),
       .RST_VAL(1'b0)
   ) soft_reset_sync (
    .clk_i     (clk_in_i),
    .arst_i    (arst_i),
    .signal_i  (soft_reset_i),
    .signal_o  (soft_reset_o)
   );

   iob_sync #(
       .DATA_W(1),
       .RST_VAL(1'b0)
   ) enable_sync (
    .clk_i     (clk_in_i),
    .arst_i    (arst_i),
    .signal_i  (enable_i),
    .signal_o  (enable_o)
   );


   wire [PERIOD_W:0] period_wdata_int;
   wire [PERIOD_W:0] period_wdata_out;
   assign period_wdata_int = {period_wdata_i, period_wen_i};
   iob_sync #(
       .DATA_W(PERIOD_W+1),
       .RST_VAL({(PERIOD_W+1){1'b0}})
   ) period_wdata_sync (
    .clk_i     (clk_in_i),
    .arst_i    (arst_i),
    .signal_i  (period_wdata_int),
    .signal_o  (period_wdata_out)
   );
   assign period_wdata_o = period_wdata_out[1+:PERIOD_W];
   assign period_wen_o = period_wdata_out[0];

endmodule
