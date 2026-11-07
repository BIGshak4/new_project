; R1=a,R2=b are naturals. R3,R4 may initially be arbitrary.
; Only CLEAR/INC/DEC/JUMP_NZ register,label. No flag-based branches.
; END is beyond the listing (educational fall-through completion).
CLEAR R3
CLEAR R4
JUMP_NZ R1, CHECK_B
INC R3
JUMP_NZ R3, END
CHECK_B:
JUMP_NZ R2, OUTER
INC R3
JUMP_NZ R3, END
OUTER:
DEC R2
ADD:
DEC R1
INC R3
INC R4
JUMP_NZ R1, ADD
RESTORE:
DEC R3
INC R1
JUMP_NZ R3, RESTORE
JUMP_NZ R2, OUTER
END:
