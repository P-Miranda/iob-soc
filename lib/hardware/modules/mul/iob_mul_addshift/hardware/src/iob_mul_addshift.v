`timescale 1ns / 1ps

module iob_mul_addshift #(
   parameter DATA_W = 32
) (
   `include "iob_mul_addshift_io.vs"
);
    localparam CNT_W = $clog2(DATA_W+1);

    wire multiplicand_en;
    wire [2*DATA_W-1:0] multiplicand_nxt;
    wire [2*DATA_W-1:0] multiplicand_reg;

    assign multiplicand_en = start_i | (~done_o);
    assign multiplicand_nxt = (start_i & done_o) ? {{DATA_W{1'b0}}, multiplicand_i} : (multiplicand_reg << 1);

   iob_reg_re #(
      .DATA_W (2 * DATA_W),
      .RST_VAL({(2*DATA_W){1'b0}})
   ) multiplicand_reg_inst (
      `include "iob_mul_addshift_clk_en_rst_s_s_portmap.vs"
      .rst_i(rst_i),
      .en_i (multiplicand_en),
      .data_i(multiplicand_nxt),
      .data_o(multiplicand_reg)
   );

   wire multiplier_en;
   wire [2*DATA_W-1:0] multiplier_nxt;
   wire [2*DATA_W-1:0] multiplier_reg;

   assign multiplier_en = start_i | (~done_o);
   assign multiplier_nxt = (start_i & done_o) ? {{DATA_W{1'b0}}, multiplier_i} : (multiplier_reg >> 1);

   iob_reg_re #(
      .DATA_W (2 * DATA_W),
      .RST_VAL({(2*DATA_W){1'b0}})
   ) multiplier_reg_inst (
      `include "iob_mul_addshift_clk_en_rst_s_s_portmap.vs"
      .rst_i(rst_i),
      .en_i (multiplier_en),
      .data_i(multiplier_nxt),
      .data_o(multiplier_reg)
   );

   wire [2*DATA_W-1:0] product_nxt;
   wire product_en;
   wire product_rst;

   assign product_rst = rst_i | (start_i & done_o);
   assign product_en = ~done_o;

   assign product_nxt = (multiplier_reg[0]) ? (product_o + multiplicand_reg) : product_o;

   iob_reg_re #(
       .DATA_W (2 * DATA_W),
       .RST_VAL({(2*DATA_W){1'b0}})
   ) product_reg_inst (
      .clk_i (clk_i),
      .cke_i (cke_i),
      .arst_i (arst_i),
      .rst_i(product_rst),
      .en_i (product_en),
      .data_i(product_nxt),
      .data_o(product_o)
   );

   wire bit_cnt_rst;
   wire bit_cnt_en;
   wire [CNT_W-1:0] bit_count;

   assign bit_cnt_rst = rst_i | (start_i & done_o);
   assign bit_cnt_en = ~done_o & (bit_count < DATA_W);
   iob_counter #(
       .DATA_W (CNT_W),
       .RST_VAL({CNT_W{1'b0}})
   ) bit_counter_inst (
      .clk_i (clk_i),
      .cke_i (cke_i),
      .arst_i (arst_i),
      .rst_i(bit_cnt_rst),
      .en_i (bit_cnt_en),
      .data_o(bit_count)
   );

   wire done_en;
   wire done_nxt;

   assign done_en = ~done_o | start_i;
   assign done_nxt = (~done_o) & (bit_count == (DATA_W-1));
   iob_reg_re #(
       .DATA_W (1),
       .RST_VAL(1'b1)
   ) done_reg_inst (
      .clk_i (clk_i),
      .cke_i (cke_i),
      .arst_i (arst_i),
      .rst_i(rst_i),
      .en_i (done_en),
      .data_i(done_nxt),
      .data_o(done_o)
   );

endmodule
