`timescale 1ns / 1ps

`define CLK_FREQ (100000000)

module iob_mul_addshift_tb;

   parameter clk_frequency = `CLK_FREQ;
   parameter clk_period = 1e9/clk_frequency; //ns
   parameter DATA_W = 8;
   parameter TEST_SZ = 1000;

   reg clk = 0;
   reg rst = 0;
   reg start = 0;
   wire done;

   //data
   reg [DATA_W-1:0]  multiplicand [0:TEST_SZ-1];
   reg [DATA_W-1:0]  multiplier [0:TEST_SZ-1];
   reg [2*DATA_W-1:0]  product [0:TEST_SZ-1];

   //core outputs
   wire [2*DATA_W-1:0] product_out;
   
   integer i;
   integer fp;

 
   initial begin

`ifdef VCD
      $dumpfile("uut.vcd");
      $dumpvars();
`endif

      // generate test data
      for (i=0; i < TEST_SZ; i=i+1) begin
        multiplicand[i] = $random;
        multiplier[i] = $random;
        product[i] = {{DATA_W{1'b0}}, multiplicand[i]} * {{DATA_W{1'b0}}, multiplier[i]};
      end
            
      //reset pulse
      #100 rst = 1;
      @(posedge clk) #1 rst = 0;
      
      //compute divisions
      for (i=0; i < TEST_SZ; i=i+1) begin
         //pulse start
         @(posedge clk) #1 start = 1;
         @(posedge clk) #1 start = 0;

         //wait for done
         @(posedge clk) #1;
         while(!done)
           @(posedge clk) #1;
         
         //verify results
         if(product_out != product[i])
           $display ("%d * %d = %d, but got %d", multiplicand[i], multiplier[i], product[i], product_out);
         else begin
            fp = $fopen("test.log", "w");
            $fdisplay(fp, "Test passed!");
         end
      end

      #clk_period;
      $display("%c[1;34m", 27);
      $display("Test completed successfully.");
      $display("%c[0m", 27);

      #(5 * clk_period) $finish();

   end

   //clock
   always #(clk_period/2) clk = ~clk;   

   //instantiate unsigned multiplier
   iob_mul_addshift 
     # (
        .DATA_W(DATA_W)
        )
   uut 
     (
      .clk_i(clk),
      .arst_i(rst),
      .cke_i(1'b1),
      .rst_i(1'b0),
      .start_i(start),
      .done_o(done),

      .multiplicand_i(multiplicand[i]),
      .multiplier_i(multiplier[i]),
      .product_o(product_out)
      );
   
endmodule
