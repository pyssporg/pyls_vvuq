"""End-to-end tests for the GDistribution TypeAlias (lsuq.py).

GDistribution is a PEP 604 union of all distribution classes, used both as
a single child (UncertainParameter.distribution) and inside a list
(Results.distributions). These tests pin the round-trip behavior of both
usages through the real schema classes.
"""
import pytest

from pylsuq import (
    Cauchy,
    CauchyTolerance,
    GDistribution,
    MonotoneSplineCDF,
    Normal,
    NormalTolerance,
    Results,
    UncertainParameter,
    Uniform,
    UniformTolerance,
    Weibull,
)

DISTRIBUTIONS: list[GDistribution] = [
    Normal(mu=0.0, sigma=1.0),
    NormalTolerance(nominal=1.0),
    Uniform(minimum=0.0, maximum=1.0),
    UniformTolerance(nominal=0.5),
    Weibull(shape=1.5, scale=2.0),
    Cauchy(x0=0.0, gamma=1.0),
    CauchyTolerance(nominal=0.0),
    MonotoneSplineCDF(x=[0.0, 1.0], y=[0.0, 1.0]),
]


class TestUncertainParameterDistribution:
    @pytest.mark.parametrize(
        "distribution", DISTRIBUTIONS, ids=lambda d: type(d).__name__
    )
    def test_round_trip_each_union_member(self, distribution):
        obj = UncertainParameter(distribution=distribution, name="p")
        assert UncertainParameter.from_xml(obj.to_xml()) == obj


class TestResultsDistributions:
    def test_round_trip_mixed_distributions(self):
        obj = Results(distributions=list(DISTRIBUTIONS), point="P0")
        round_tripped = Results.from_xml(obj.to_xml())
        assert round_tripped == obj

    def test_document_order_is_preserved(self):
        obj = Results(distributions=list(DISTRIBUTIONS))
        round_tripped = Results.from_xml(obj.to_xml())
        assert [type(d) for d in round_tripped.distributions] == [
            type(d) for d in DISTRIBUTIONS
        ]
