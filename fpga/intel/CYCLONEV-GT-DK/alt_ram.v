`include "system.vh"
`timescale 1ns / 1ps

module ram #(
	     parameter ADDR_W = 12, //must be lower than ADDR_W-N_SLAVES_W
             parameter FILE = "none"	          
		     )
   (      
          input 	       clk,
          input 	       rst,

          //native interface 
	  input [ADDR_W-1:0]   i_addr,
	  input [3:0] 	       i_en,
	  output [`DATA_W-1:0] i_data,
	  output reg 	       i_ready, 

          input [`DATA_W-1:0]  wdata,
          input [ADDR_W-1:0]   addr,
          input [3:0] 	       wstrb,
          output [`DATA_W-1:0] rdata,
          input 	       valid,
          output reg 	       ready
	  );
   
   // byte memories
   // byte 0
   parameter file_name_0 = (FILE == "none")? "none": {FILE, "_0", ".dat"};
   bytewrite_tdp_ram_rf  #(
                  .FILE(file_name_0),
                  .NUM_COL(1),
		  .COL_WIDTH(8),
                  .ADDR_WIDTH(ADDR_W))
   main_mem_byte0
     (
      .clkA           (clk),
      .enaA            (valid),
      .weA            (wstrb[0]),
      .addrA          (addr),
      .doutA      (rdata[7:0]),
      .dinA       (wdata[7:0]),
      .clkB           (clk),
      .enaB             (i_en[0]),
      .addrB          (i_addr),
      .weB            (1'b0),
      .dinB           (wdata[7:0]),
      .doutB          (i_data[7:0])
      );

   //byte 1
   parameter file_name_1 = (FILE == "none")? "none": {FILE, "_1", ".dat"};
   bytewrite_tdp_ram_rf  #(
                  .FILE(file_name_1),
                  .NUM_COL(1),
		  .COL_WIDTH(8),
                  .ADDR_WIDTH(ADDR_W))
   main_mem_byte1
     (
      .clkA           (clk),
      .enaA            (valid),
      .weA            (wstrb[1]),
      .addrA          (addr),
      .doutA      (rdata[15:8]),
      .dinA       (wdata[15:8]),
      .clkB           (clk),
      .enaB             (i_en[1]),
      .addrB          (i_addr),
      .weB            (1'b0),
      .dinB           (wdata[15:8]),
      .doutB          (i_data[15:8])
      );
   
   // byte 2
   parameter file_name_2 = (FILE == "none")? "none": {FILE, "_2", ".dat"};
   bytewrite_tdp_ram_rf  #(
                  .FILE(file_name_2),
                  .NUM_COL(1),
		  .COL_WIDTH(8),
                  .ADDR_WIDTH(ADDR_W))
   main_mem_byte2
     (
      .clkA           (clk),
      .enaA            (valid),
      .weA            (wstrb[2]),
      .addrA          (addr),
      .doutA      (rdata[23:16]),
      .dinA       (wdata[23:16]),
      .clkB           (clk),
      .enaB             (i_en[2]),
      .addrB          (i_addr),
      .weB            (1'b0),
      .dinB           (wdata[23:16]),
      .doutB          (i_data[23:16])
      );
   //byte 3
   parameter file_name_3 = (FILE == "none")? "none": {FILE, "_3", ".dat"};
   bytewrite_tdp_ram_rf  #(
                  .FILE(file_name_3),
                  .NUM_COL(1),
		  .COL_WIDTH(8),
                  .ADDR_WIDTH(ADDR_W))
   main_mem_byte3
     (
      .clkA           (clk),
      .enaA            (valid),
      .weA            (wstrb[3]),
      .addrA          (addr),
      .doutA      (rdata[31:24]),
      .dinA       (wdata[31:24]),
      .clkB           (clk),
      .enaB             (i_en[3]),
      .addrB          (i_addr),
      .weB            (1'b0),
      .dinB           (wdata[31:24]),
      .doutB          (i_data[31:24])
      );

   //reply with ready 
   always @(posedge clk, posedge rst)
     if(rst) begin
	ready <= 1'b0;
	i_ready <= 1'b0;
     end
     else begin 
	ready <= valid;
	i_ready <= |i_en;
     end
endmodule
