"""Two chips share a latent factory; independence is conditional on that factory."""
from fractions import Fraction


def probability(value):
    if type(value) not in (int, Fraction):
        raise ValueError("use an exact integer or Fraction probability")
    result = Fraction(value)
    if not 0 <= result <= 1:
        raise ValueError("probability must lie in0..1")
    return result


def posterior_details(pa, pb, prior_a=Fraction(1, 2)):
    """Condition on a good first chip in a box from one selected factory.

    Given that factory, both chip outcomes are independent with rate pa or pb.
    This function does not assume marginal independence after mixing factories.
    """
    pa, pb, prior = map(probability, (pa, pb, prior_a))
    evidence = prior * pa + (1 - prior) * pb
    if evidence == 0:
        raise ValueError("conditioning event has probability zero")
    posterior_a = prior * pa / evidence
    second_good = (prior * pa * pa + (1 - prior) * pb * pb) / evidence
    return {"first_good": evidence, "factory_a": posterior_a,
            "factory_b": 1 - posterior_a, "second_good": second_good}


def posterior_quality(pa, pb):
    """The primary exercise has equal prior probability for the two factories."""
    return posterior_details(pa, pb)["second_good"]
