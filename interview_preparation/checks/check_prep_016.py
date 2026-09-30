"""All 65,536 requests, including arbitrary codes from inactive local blocks."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_016_interrupt_controller import controller16,controller16_gates_only

for word in range(65536):
    expected=(int(word!=0),max(0,word.bit_length()-1))
    for invalid in range(4):
        assert controller16(word,False,invalid)==expected,(word,invalid,'four')
        assert controller16(word,True,invalid)==expected,(word,invalid,'five')
    assert controller16_gates_only(word)==expected,(word,'gates')
print('PASS: all 65,536 input vectors, four-/five-controller and gates-only constructions.')
print('PASS: all four possible invalid local codes; deterministic zero index for no requests.')
