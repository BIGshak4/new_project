from fractions import Fraction
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_017_clock_angle import hand_angles,smaller_angle

assert hand_angles(6,30)==(195,180)
for time,expected in [((6,30),15),((6,0),180),((0,0),0),((12,30),165),
                      ((3,15),Fraction(15,2)),((9,45),Fraction(45,2))]:
    assert smaller_angle(*time)==expected
for t in range(720):
    h,m=divmod(t,60)
    a=smaller_angle(h,m)
    assert 0<=a<=180
    assert a==smaller_angle(h+12,m)
    # Relative motion is 6 - 0.5 = 5.5 degrees per minute, modulo a full turn.
    relative=(Fraction(11,2)*t)%360
    assert a==min(relative,360-relative)
print('PASS: 06:30 -> 15 degrees; six examples; all 720 minute positions checked against relative motion and 12-hour periodicity.')
