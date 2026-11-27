import pytest

pytest.importorskip("numpy")
pytest.importorskip("scipy")
pytest.importorskip("matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import pylsuq as lsuq


def _domain(domain_id):
    axes = lsuq.Axes([
        lsuq.Axis(name="x"),
        lsuq.Axis(name="y"),
        lsuq.Axis(name="z"),
    ])
    boundary = lsuq.Boundary(lsuq.HyperRectangle([
        lsuq.Point([0, 0, 0]),
        lsuq.Point([1, 1, 1]),
    ]))
    return lsuq.ActivityDomain(
        id=domain_id,
        kind="test",
        axes=axes,
        boundary=boundary,
    )


def test_add_domain_plot_matplotlib_2d_and_reuses_axes():
    domain = _domain("first")
    _, ax = plt.subplots()

    result = lsuq.add_domain_plot(
        domain, ["x", "y"], backend="matplotlib", fig=ax
    )

    assert result is ax
    assert ax.get_xlabel() == "x [-]"
    assert ax.get_ylabel() == "y [-]"
    assert len(ax.lines) == 4


def test_add_domain_plot_matplotlib_3d_draws_faces_and_cycles_colors():
    ax = lsuq.add_domain_plot(
        _domain("first"), ["x", "y", "z"], backend="matplotlib"
    )
    lsuq.add_domain_plot(
        _domain("second"), ["x", "y", "z"], backend="matplotlib", fig=ax
    )

    assert ax.get_zlabel() == "z [-]"
    assert len(ax.lines) == 24
    assert len(ax.collections) == 2
    assert all(isinstance(item, Poly3DCollection) for item in ax.collections)
    assert ax.lines[0].get_color() != ax.lines[12].get_color()


def test_add_boundary_plot_matplotlib_convex_hull():
    axes = lsuq.Axes([
        lsuq.Axis(name="x"),
        lsuq.Axis(name="y"),
        lsuq.Axis(name="z"),
    ])
    boundary = lsuq.Boundary(lsuq.ConvexHull([
        lsuq.Point([0, 0, 0]),
        lsuq.Point([1, 0, 0]),
        lsuq.Point([1, 1, 0]),
        lsuq.Point([0, 1, 0]),
        lsuq.Point([0, 0, 1]),
        lsuq.Point([1, 0, 1]),
        lsuq.Point([1, 1, 1]),
        lsuq.Point([0, 1, 1]),
    ]))

    ax = lsuq.add_boundary_plot(
        boundary, ["x", "y", "z"], axes=axes, backend="matplotlib"
    )

    assert len(ax.lines) == 18
    assert len(ax.collections) == 1
    assert isinstance(ax.collections[0], Poly3DCollection)


def test_add_domain_plot_matplotlib_rejects_unknown_backend():
    with pytest.raises(ValueError, match="backend must be"):
        lsuq.add_domain_plot(_domain("first"), ["x", "y"], backend="unknown")
