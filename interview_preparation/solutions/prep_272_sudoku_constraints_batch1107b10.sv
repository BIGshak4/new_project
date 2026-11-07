// Complete 9x9 solution grids, not partially filled puzzles.
class sudoku_board_batch1107b10;
 rand int unsigned board[9][9];
 constraint domain {
   foreach(board[r,c]) board[r][c] inside {[1:9]};
 }
 constraint peers {
   foreach(board[r,c]) foreach(board[r2,c2])
     if ((r*9+c < r2*9+c2) &&
         ((r==r2) || (c==c2) ||
          ((r/3==r2/3) && (c/3==c2/3))))
       board[r][c] != board[r2][c2];
 }
endclass

module prep272_sudoku_tb_batch1107b10;
 sudoku_board_batch1107b10 item;
 integer sample,r,c;
 initial begin
   item=new;
   for(sample=0;sample<2;sample=sample+1) begin
     if(item.randomize()==0) $fatal(1,"Sudoku constraint solver failed");
     $display("BOARD %0d",sample);
     for(r=0;r<9;r=r+1) begin
       for(c=0;c<9;c=c+1) $write("%0d ",item.board[r][c]);
       $write("\n");
     end
   end
   $display("PASS generated 2 boards");
   $finish;
 end
endmodule
