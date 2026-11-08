"""Five-state direction-on-completion model under explicit observability limits."""
IDLE,WAIT_B,EXIT_B,WAIT_A,EXIT_A=range(5)


def step(state, ab, short_mode):
    if state not in range(5) or ab not in range(4):
        raise ValueError('state0..4 and sensor mask0..3 required')
    right=left=False
    if state==IDLE:
        state={2:WAIT_B,1:WAIT_A}.get(ab,IDLE)
    elif state==WAIT_B:
        if ab==1:
            state=EXIT_B
        elif (ab==0 and not short_mode) or(ab==3 and short_mode):
            state=IDLE
    elif state==EXIT_B:
        if ab==0:
            state=IDLE;right=True
        elif ab==3:
            state=IDLE if short_mode else WAIT_B
        elif ab==2:
            state=IDLE
    elif state==WAIT_A:
        if ab==2:
            state=EXIT_A
        elif(ab==0 and not short_mode)or(ab==3 and short_mode):
            state=IDLE
    elif state==EXIT_A:
        if ab==0:
            state=IDLE;left=True
        elif ab==3:
            state=IDLE if short_mode else WAIT_A
        elif ab==1:
            state=IDLE
    return state,right,left


def sensors(position,length_,distance=4):
    return (2*int(position<=0<=position+length_)
            +int(position<=distance<=position+length_))
