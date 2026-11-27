import pytest

pytest.importorskip("numpy")
pytest.importorskip("plotly")
pytest.importorskip("scipy")

import plotly.graph_objects as go

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


def test_add_domain_plot_cycles_colorway_per_domain():
    fig = go.Figure()
    fig.update_layout(colorway=["red", "blue"])

    lsuq.add_domain_plot(_domain("first"), ["x", "y", "z"], fig=fig)
    lsuq.add_domain_plot(_domain("second"), ["x", "y", "z"], fig=fig)

    first_boundary, first_faces, second_boundary, second_faces = fig.data
    assert first_boundary.line.color == "red"
    assert first_boundary.marker.color == "red"
    assert first_faces.color == "red"
    assert second_boundary.line.color == "blue"
    assert second_boundary.marker.color == "blue"
    assert second_faces.color == "blue"


def test_add_domain_plot_explicit_color_does_not_consume_cycle():
    style = {"color": "purple"}
    fig = lsuq.add_domain_plot(
        _domain("explicit"), ["x", "y", "z"], style=style
    )
    lsuq.add_domain_plot(_domain("automatic"), ["x", "y", "z"], fig=fig)

    explicit_boundary, explicit_faces, automatic_boundary, automatic_faces = fig.data
    assert explicit_boundary.line.color == "purple"
    assert explicit_faces.color == "purple"
    default_color = fig.layout.template.layout.colorway[0].casefold()
    assert automatic_boundary.line.color.casefold() == default_color
    assert automatic_faces.color.casefold() == default_color
    assert style == {"color": "purple"}