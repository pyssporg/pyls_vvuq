from __future__ import annotations

from itertools import combinations
from typing import Any, Mapping, Sequence
import pylsuq as lsuq
import plotly.graph_objects as go
import numpy as np
from scipy.spatial import ConvexHull, QhullError

def _axis_labels(plot_axes:list[lsuq.Axis]) -> list[str]:
    return [axis.name + " [" + (axis.unit or "-") + "]" for axis in plot_axes]

def _axis_indeces(plot_axes:list[str] | list[int],axes: lsuq.Axes) -> list[int]:
    if isinstance(plot_axes[0],int):
        return plot_axes
    return [iA for iA,axis in enumerate(axes.axes) if axis.name in plot_axes]
    
def _style(style: dict | None) -> dict[str, Any]:
    """Normalize public style aliases into a compact internal style dictionary."""
    if style is None:
        style = {}
    
    values = dict(style)
    color = values.get("color", "#1f77b4")
    edgecolor = values.get("edgecolor", color)
    facecolor = values.get("facecolor", color)
    linewidth = values.get("edge_width", values.get("linewidth", 3))
    markersize = values.get("markersize", values.get("markersize", 4))
    alpha = values.get("alpha", values.get("opacity", 0.75))

    try:
        linewidth = float(linewidth)
        markersize = float(markersize)
        alpha = float(alpha)
    except (TypeError, ValueError) as exc:
        raise ValueError("linewidth, markersize, and alpha must be numeric.") from exc
    if linewidth < 0 or markersize < 0 or not 0 <= alpha <= 1:
        raise ValueError("linewidth and markersize must be non-negative and alpha must be between 0 and 1.")

    dash = str(values.get("linestyle", values.get("dash", "solid"))).lower()
    dash = {"-": "solid", "--": "dash", ":": "dot", "-.": "dashdot"}.get(dash, dash)
    if dash not in {"solid", "dot", "dash", "dashdot"}:
        raise ValueError("linestyle must be solid, dot, dash, dashdot, or a common matplotlib alias.")

    return {
        "edgecolor": edgecolor,
        "facecolor": facecolor,
        "linewidth": linewidth,
        "dash": dash,
        "alpha": alpha,
        "marker": values.get("marker", "circle"),
        "markersize": markersize,
        "name": values.get("name", values.get("label")),
    }

def _hyper_rectangle_corners(bounds:list[list[int]]):
    """Return all corners of a two- or three-dimensional axis-aligned hyper_rectangle."""
    corners = [[]]

    for lower, upper in bounds:
        corners = [
            corner + [value]
            for corner in corners
            for value in (lower, upper)
            ]

    return np.asarray(corners, dtype=float)

def _line_kwargs(style: dict, is_3d: bool = False) -> dict[str, Any]:
    line = {"color": style["edgecolor"], "width": style["linewidth"]}
    if not is_3d:
        line["dash"] = style["dash"]
    return line

def _marker_kwargs(style: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "color": style["edgecolor"],
        "size": style["markersize"],
        "symbol": style["marker"],
        "opacity": style["alpha"],
    }

def _set_axis_titles(fig: go.Figure, labels: list[str]) -> None:
    """Set Plotly axis titles for the active two- or three-dimensional projection."""
    if len(labels) == 2:
        fig.update_layout(xaxis_title=labels[0], yaxis_title=labels[1])
    else:
        fig.update_layout(
            scene={
                "xaxis": {"title": labels[0]},
                "yaxis": {"title": labels[1]},
                "zaxis": {"title": labels[2]},
            }
        )

def _boundary_coordinates(corners: Any, dimension: int) -> tuple[list[float | None], ...]:
    """Build Plotly line coordinates for boundaries encoded with None separators."""
    coordinates: list[list[float | None]] = [[] for _ in range(dimension)]
    for first, second in combinations(range(len(corners)), 2):
        # hyper_rectangle corner ordering from itertools.product differs in one bit per edge.
        if sum(a != b for a, b in zip(corners[first], corners[second])) != 1:
            continue
        for axis in range(dimension):
            coordinates[axis].extend([corners[first, axis], corners[second, axis], None])
    return tuple(coordinates)

def _coplanar_perimeter(points: Any, ConvexHull: Any, QhullError: Any, np: Any) -> Any:
    """Find a 3D coplanar perimeter by calculating a hull in its fitted plane."""
    centered = points - points.mean(axis=0)
    _u, singular_values, vh = np.linalg.svd(centered, full_matrices=False)
    tolerance = max(points.shape) * np.finfo(float).eps * (singular_values[0] if singular_values.size else 1.0)
    if singular_values.size < 2 or singular_values[1] <= tolerance:
        raise ValueError("Projected 3D points are collinear; a perimeter cannot be formed.")
    planar = centered @ vh[:2].T
    try:
        hull = ConvexHull(planar)
    except QhullError as exc:
        raise ValueError("Could not compute a perimeter for the coplanar points.") from exc
    return points[hull.vertices]

def _add_line_marker_trace(fig: go.Figure,coordinates: list[float],style: dict, name: str | None = None, is_3d: bool | None = None, mode = "lines+markers",hovertemplate = (),customdata = []) -> Any:
    if is_3d is None:
        is_3d = len(coordinates) == 3
    trace_class = go.Scatter3d if is_3d else go.Scatter
    fields = dict(
        mode=mode,
        line=_line_kwargs(style, is_3d=is_3d),
        opacity=style["alpha"],
        marker = _marker_kwargs(style),
        name=name if name is not None else style["name"],
        showlegend=bool(name if name is not None else style["name"]),
        hovertemplate = hovertemplate,
        customdata = customdata
    )
    if is_3d:
        trace = trace_class(x=coordinates[0], y=coordinates[1], z=coordinates[2], **fields)
    else:
        trace = trace_class(x=coordinates[0], y=coordinates[1], **fields)
    fig.add_trace(trace)
    return trace

def _add_points_trace(
    fig: Any,
    points: Any,
    style: Mapping[str, Any],
    name: str | None = None,
    is_3d: bool | None = None,
    customdata = [],
    hovertemplate=()
) -> Any:
    if is_3d is None:
        is_3d = points.shape[1] == 3
    trace_class = go.Scatter3d if is_3d else go.Scatter
    fields = dict(
        mode="markers",
        marker=_marker_kwargs(style),
        name=name if name is not None else style["name"],
        showlegend=bool(name if name is not None else style["name"]),
        customdata = customdata,
        hovertemplate = hovertemplate
    )
    if is_3d:
        trace = trace_class(x=points[:, 0], y=points[:, 1], z=points[:, 2], **fields)
    else:
        trace = trace_class(x=points[:, 0], y=points[:, 1], **fields)
    fig.add_trace(trace)
    return trace

def add_boundary_plot(boundary:lsuq.Boundary,plot_axes: list[str] | list [int],style = None,axes: lsuq.Axes = None, fig: go.Figure = None,experiment_points = None) -> go.Figure | None:   
    if fig is None:
        fig = go.Figure()
        returnFig = True
    else:
        returnFig = False
     
    if experiment_points is None:
        trace_experiment = False
    else:
        trace_experiment = True
    
    markers_loop = ["cross",
                    "diamond",
                    "diamond-open",
                    "square",
                    "square-open",
                    "x"]    
    
    normalized_style = _style(style)
    axis_indeces = _axis_indeces(plot_axes, axes)
    axis_labels = _axis_labels([axes.axes[i] for i in axis_indeces])
    dimension = len(axis_indeces)
    
    if dimension not in (2, 3):
        raise ValueError("dims must resolve to exactly two or three dimensions.")
        
    is_3d = dimension == 3
    
    match boundary.shape.__class__.__name__:
        case "HyperRectangle":
            bounds = []
            for i in axis_indeces:
                pair = [boundary.shape.points[0].coordinates[i],boundary.shape.points[1].coordinates[i]]
                bounds.append([np.min(pair),np.max(pair)])
            corners = _hyper_rectangle_corners(bounds)
            hovertemplate =( (normalized_style.get("name") or "HyperRectangle") + " boundary (HyperRectangle)"+ "<br>" +                       
             axis_labels[0]+": %{x}<br>" +                       
              
            axis_labels[1]+": %{y}<br>"+
            (axis_labels[2]+": %{z}" if is_3d else "")+
            "<extra></extra>"
            )
            _add_line_marker_trace(
                fig,
                _boundary_coordinates(corners,dimension),
                normalized_style,
                (normalized_style.get("name") or "HyperRectangle") + " boundary  (HyperRectangle)",
                is_3d = is_3d,
                hovertemplate = hovertemplate
                )
            if is_3d:
                mesh = go.Mesh3d(
                    x=corners[:, 0],
                    y=corners[:, 1],
                    z=corners[:, 2],
                    i=[0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1],
                    j=[1, 3, 5, 7, 1, 5, 3, 7, 2, 6, 3, 7],
                    k=[3, 2, 7, 6, 5, 4, 7, 6, 6, 4, 7, 5],
                    color=normalized_style["facecolor"],
                    opacity=normalized_style["alpha"]*0.6,
                    name= (normalized_style["name"] or "HyperRectangle")+ " boundary face (HyperRectangle)",
                    showlegend=True,
                 )   
                fig.add_trace(mesh)
        case "ConvexHull":
            data = np.asarray([point.coordinates for point in boundary.shape.points])
            projected = data[:,axis_indeces]
            unique_points  = np.unique(projected,axis=0)
            if len(unique_points) < len(axis_indeces) + 1:
                raise ValueError("Not enough unique projected points to construct a convex hull.")
            
            
            if dimension == 2:
                try:
                    hull = ConvexHull(unique_points)
                except QhullError as exc:
                   raise ValueError("Projected points are collinear; a 2D convex hull cannot be formed.") from exc
                hovertemplate =( (normalized_style.get("name") or "ConvexHull") + " boundary (ConvexHull)"+ "<br>" +                       
                 axis_labels[0]+": %{x}<br>" +                    
                axis_labels[1]+": %{y}<br>"+
                "<extra></extra>"
                )
                perimeter = unique_points[list(hull.vertices) + [hull.vertices[0]]]
                _add_line_marker_trace(fig,
                                (perimeter[:, 0], perimeter[:, 1]),
                                normalized_style,
                                (normalized_style["name"] or "ConvexHull")+ " boundary (ConvexHull)",
                                is_3d = is_3d,
                                hovertemplate = hovertemplate
                                )
               
                
            else:
                centered = unique_points - unique_points.mean(axis=0)
                rank = np.linalg.matrix_rank(centered)
                if rank < 2:
                    raise ValueError("Projected 3D points are collinear; a convex hull cannot be formed.")
                if rank == 2:
                    hovertemplate =( (normalized_style.get("name") or "ConvexHull") + " boundary (ConvexHull)"+ "<br>" +                       
                    axis_labels[0]+": %{x}<br>" +                    
                    axis_labels[1]+": %{y}<br>"+
                    "<extra></extra>"
                    )
                    perimeter = _coplanar_perimeter(unique_points, ConvexHull, QhullError, np)
                    
                    closed = np.vstack((perimeter, perimeter[0]))
                    _add_line_marker_trace(
                        fig, 
                        (closed[:, 0], closed[:, 1], closed[:, 2]),
                        normalized_style,
                        (normalized_style["name"] or "ConvexHull")+" boundary (ConvexHull)",
                        hovertemplate = hovertemplate
                        )
                    
                else:
                    try:
                        hull = ConvexHull(unique_points)
                    except QhullError as exc:
                        raise ValueError("Could not compute a 3D convex hull for the projected points.") from exc

            
                    edges = set()

                    for simplex in hull.simplices:
                        edges.update(tuple(sorted(pair)) for pair in combinations(simplex, 2))

                    line_coordinates = [[], [], []]

                    for first, second in sorted(edges):
                        # Coordinates for the Plotly line trace
                        for axis in range(3):
                            line_coordinates[axis].extend([
                                unique_points[first, axis],
                                unique_points[second, axis],
                                None,
                                ])                    
                    hovertemplate =( (normalized_style.get("name") or "HyperRectangle") + " boundary (ConvexHull)"+ "<br>" +                       
                     axis_labels[0]+": %{x}<br>" +                    
                    axis_labels[1]+": %{y}<br>"+
                    axis_labels[2]+": %{z}"
                    "<extra></extra>"
                    )
                    _add_line_marker_trace(fig,
                    tuple(line_coordinates),
                    normalized_style, 
                    (normalized_style["name"] or "ConvexHull") + " boundary  (ConvexHull)",
                    is_3d = is_3d,
                    hovertemplate = hovertemplate
                    )
                    
                    simplices = hull.simplices
                    mesh = go.Mesh3d(
                         x=unique_points[:, 0],
                         y=unique_points[:, 1],
                         z=unique_points[:, 2],
                         i=simplices[:, 0],
                         j=simplices[:, 1],
                         k=simplices[:, 2],
                         color=normalized_style["facecolor"],
                         opacity=normalized_style["alpha"]*0.6,
                         name= (normalized_style["name"] or "ConvexHull")+ " boundary faces  (ConvexHull)",
                         showlegend=True,
                         )   
                    fig.add_trace(mesh)
            if trace_experiment:
                normalized_style["markersize"] += 3
                for ip,point_set in enumerate(experiment_points.point_sets):
                
                    normalized_style["marker"] = markers_loop[ip]
                    customdata = [[point_set.id,point.id] for point in point_set.points]
                    hovertemplate=(
                        "PointSet: %{customdata[0]}<br>" + 
                        "Point: %{customdata[1]}<br>" +                       
                         axis_labels[0]+": %{x}<br>" +                       
                          
                        axis_labels[1]+": %{y}<br>"+
                        (axis_labels[2]+": %{z}" if is_3d else "")+
                        "<extra></extra>"
                        )
                    data_experiment = np.asarray([point.coordinates for point in point_set.points])
                    projected_experiment = data_experiment[:,axis_indeces]
                    _add_points_trace(fig,
                                      projected_experiment, 
                                      normalized_style, 
                                      (normalized_style["name"] or "ConvexHull")+ " "+point_set.id,
                                      is_3d = is_3d,
                                      customdata = customdata,
                                      hovertemplate = hovertemplate)
            
    _set_axis_titles(fig, axis_labels)    
   
    if returnFig:
        return fig

def add_domain_plot(domain:lsuq.ActivityDomain | lsuq.TypedOperationalDomain,plot_axes: list[str] | list[int],style = None,fig: go.Figure = None ) -> go.Figure | None:      
    if style is None:
        style = {}
    if style.get('label') is None:
        style['label'] = domain.id
    if fig is None:
        fig = go.Figure()
        returnFig = True
    else:
        returnFig = False
        
    
    match domain.boundary.shape.__class__.__name__:
        case "HyperRectangle":
            add_boundary_plot(fig = fig,boundary = domain.boundary,axes = domain.axes,plot_axes = plot_axes,style = style)
        case "ConvexHull":            
            add_boundary_plot(fig = fig,boundary = domain.boundary,axes = domain.axes,plot_axes = plot_axes,style = style,experiment_points=domain.experiment_points)
    if returnFig:
        return fig

