"""Illustrative characterized-delay table, not a PDK or an STA engine."""
from fractions import Fraction as F

# Values are ns. They deliberately follow the stated conventional model.
TEACHING_CORNERS = {
    'SS_lowV_hot': {'cq_max':F('0.20'), 'logic_max':F('0.75'),
                    'cq_min':F('0.10'), 'logic_min':F('0.25')},
    'TT_nominal': {'cq_max':F('0.12'), 'logic_max':F('0.50'),
                   'cq_min':F('0.05'), 'logic_min':F('0.10')},
    'FF_highV_cold': {'cq_max':F('0.08'), 'logic_max':F('0.35'),
                     'cq_min':F('0.03'), 'logic_min':F('0.02')},
}


def slack(corner, period=F(1), skew=F(0), setup=F('0.08'),
          hold=F('0.06'), setup_uncertainty=F('0.02'),
          hold_uncertainty=F('0.02')):
    """Positive skew means capture clock later than launch clock."""
    setup_slack = (period+skew-setup_uncertainty-setup
                   -corner['cq_max']-corner['logic_max'])
    hold_slack = (corner['cq_min']+corner['logic_min']
                  -skew-hold_uncertainty-hold)
    return setup_slack, hold_slack
