// Entry/exit requests are synchronous, debounced, single-cycle events.
// An acknowledged event represents an atomic completed crossing in this model.
module prep356_parking(
  input wire clk,rst,entry_req,exit_req,
  output reg [5:0] occupancy,
  output wire full,accept_entry,accept_exit,reject_entry,reject_exit,state_error
);
  assign state_error = occupancy > 6'd50;
  assign full = occupancy[5] & occupancy[4] & ~occupancy[3]
                & ~occupancy[2] & occupancy[1] & ~occupancy[0];
  assign accept_exit = ~rst & ~state_error & exit_req & (occupancy != 0);
  assign accept_entry = ~rst & ~state_error & entry_req
                        & ((occupancy < 6'd50) | accept_exit);
  assign reject_entry = entry_req & ~accept_entry;
  assign reject_exit = exit_req & ~accept_exit;
  always @(posedge clk) begin
    if (rst || state_error) occupancy <= 6'd0;
    else if (accept_entry && !accept_exit) occupancy <= occupancy + 6'd1;
    else if (accept_exit && !accept_entry) occupancy <= occupancy - 6'd1;
  end
endmodule
