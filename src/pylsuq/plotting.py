from __future__ import annotations

from itertools import combinations
from typing import Any, Mapping
import pylsuq as lsuq
import warnings

def _require_plotting_dependencies():
    try:
        import numpy as np
        import plotly.graph_objects as go
        from scipy.spatial import ConvexHull, QhullError
    except ImportError as exc:
        raise ImportError(
            "Domain plotting requires optional dependencies. "
            "Install them with: pip install pylsuq[plotting]"
        ) from exc

    return np, go, ConvexHull, QhullError

def _axis_labels(
    axis_indices: list[int],
    axes: lsuq.Axes | None = None,
) -> list[str]:
    if axes is None:
        return [f"Ax {index}" for index in axis_indices]

    labels = []

    for index in axis_indices:
        axis = axes.axes[index]
        unit = axis.unit or "-"
        labels.append(f"{axis.name} [{unit}]")

    return labels

def _axis_indices(
    plot_axes: list[str] | list[int],
    axes: lsuq.Axes | None = None,
) -> list[int]:
    if not plot_axes:
        raise ValueError("plot_axes cannot be empty.")

    if all(isinstance(axis, int) for axis in plot_axes):
        return list(plot_axes)

    if axes is None:
        raise ValueError("axes must be supplied when plot_axes contains names.")

    if not all(isinstance(axis, str) for axis in plot_axes):
        raise ValueError("plot_axes must contain either all names or all indices.")

    index_by_name = {
        axis.name: index
        for index, axis in enumerate(axes.axes)
    }

    missing = [name for name in plot_axes if name not in index_by_name]
    if missing:
        raise ValueError(f"Unknown axis name(s): {missing}")

    return [index_by_name[name] for name in plot_axes]
    
def _style(style: dict | None) -> dict[str, Any]:
    """Normalize public style aliases into a compact internal style dictionary."""
    if style is None:
        style = {}
    
    values = dict(style)
    color = values.get("color", "#1f77b4")
    edgecolor = values.get("edgecolor", color)
    facecolor = values.get("facecolor", color)
    linewidth = values.get("edge_width", values.get("linewidth", 3))
    markersize = values.get("markersize", values.get("marker_size", 4))
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

def _hover_template(
    title: str,
    axis_labels: list[str],
    *,
    include_point_ids: bool = False,
    extra_label: str = "",
) -> str:
    lines = []

    if extra_label:
        lines.append(extra_label)

    lines.append(title)

    if include_point_ids:
        lines.extend([
            "PointSet: %{customdata[0]}",
            "Point: %{customdata[1]}",
        ])

    coordinate_names = ("x", "y", "z")

    for label, coordinate_name in zip(axis_labels, coordinate_names):
        lines.append(f"{label}: %{{{coordinate_name}}}")

    return "<br>".join(lines) + "<extra></extra>"

def _hyper_rectangle_corners(bounds:list[list[int]]):
    """Return all corners of a two- or three-dimensional axis-aligned hyper_rectangle."""
    (np,go,ConvexHull,QhullError) = _require_plotting_dependencies()
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

def _set_axis_titles(fig, labels: list[str]) -> None:
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

def _coplanar_perimeter(points):
    """Return the perimeter of coplanar 3D points."""
    (np,go,ConvexHull,QhullError) = _require_plotting_dependencies()
    centered = points - points.mean(axis=0)

    _, singular_values, vh = np.linalg.svd(
        centered,
        full_matrices=False,
    )

    tolerance = (
        max(points.shape)
        * np.finfo(float).eps
        * singular_values[0]
    )

    if singular_values.size < 2 or singular_values[1] <= tolerance:
        raise ValueError(
            "Projected 3D points are collinear; a perimeter cannot be formed."
        )

    planar_points = centered @ vh[:2].T

    try:
        hull = ConvexHull(planar_points)
    except QhullError as exc:
        raise ValueError(
            "Could not compute a perimeter for the coplanar points."
        ) from exc

    return points[hull.vertices]

def _add_line_marker_trace(fig,
                           coordinates: list[float],
                           style: dict, 
                           name: str | None = None, 
                           is_3d: bool | None = None, 
                           mode = "lines+markers",
                           hovertemplate: str | None = None,
                           customdata: Any = None) -> Any:
    (np,go,ConvexHull,QhullError) = _require_plotting_dependencies()
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
    customdata : Any = None,
    hovertemplate: str | None = None
) -> Any:
    (np,go,ConvexHull,QhullError) = _require_plotting_dependencies()
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

def _plot_hyper_rectangle(fig,shape:lsuq.HyperRectangle,axis_indices,axis_labels,normalized_style,boundaryType):
    (np,go,ConvexHull,QhullError) = _require_plotting_dependencies()
    dimension = len(axis_indices)
    bounds = []
    is_3d = dimension == 3
    for i in axis_indices:
        pair = [shape.points[0].coordinates[i],shape.points[1].coordinates[i]]
        bounds.append([np.min(pair),np.max(pair)])
    corners = _hyper_rectangle_corners(bounds)
    hovertemplate = _hover_template(
        (normalized_style.get("name") or boundaryType) + f" boundary ({boundaryType})",
        axis_labels,
        ) 
        
    _add_line_marker_trace(
        fig,
        _boundary_coordinates(corners,dimension),
        normalized_style,
        (normalized_style.get("name") or boundaryType) + f" boundary ({boundaryType})",
        is_3d = is_3d,
        hovertemplate = hovertemplate
        )
    if is_3d:
        hovertemplate = _hover_template(
            (normalized_style.get("name") or boundaryType) + f" boundary ({boundaryType})",
            axis_labels,
            ) 
        mesh = go.Mesh3d(
            x=corners[:, 0],
            y=corners[:, 1],
            z=corners[:, 2],
            i=[0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1],
            j=[1, 3, 5, 7, 1, 5, 3, 7, 2, 6, 3, 7],
            k=[3, 2, 7, 6, 5, 4, 7, 6, 6, 4, 7, 5],
            color=normalized_style["facecolor"],
            opacity=normalized_style["alpha"]*0.6,
            name= (normalized_style["name"] or boundaryType)+ f" boundary face ({boundaryType})",
            showlegend=True,
            hovertemplate = hovertemplate   
             
            )   
        fig.add_trace(mesh)
        
def _plot_convex_hull(fig,shape,axis_indices,axis_labels,normalized_style,boundaryType):  
    (np,go,ConvexHull,QhullError) = _require_plotting_dependencies()
    data = np.asarray([point.coordinates for point in shape.points])
    projected = data[:,axis_indices]
    unique_points  = np.unique(projected,axis=0)            
    dimension = len(axis_indices)
    if len(unique_points) < dimension+1:
            warnings.warn(
                f"At least {str(dimension+1)} unique points are required for a {str(dimension)}D convex hull.",
                stacklevel=2,
                )
    is_3d = dimension == 3
    if dimension == 2:
        try:
            do_hull = True
            hull = ConvexHull(unique_points)
        except QhullError:
            do_hull = False
            warnings.warn("Projected points are collinear; a 2D convex hull cannot be formed, only points are plotted.")
        
        if do_hull:
            
            hovertemplate = _hover_template(
                (normalized_style.get("name") or boundaryType) + f" boundary ({boundaryType})",
             axis_labels,
                 )
            perimeter = unique_points[list(hull.vertices) + [hull.vertices[0]]]
        
            _add_line_marker_trace(fig,
                        (perimeter[:, 0], perimeter[:, 1]),
                        normalized_style,
                        (normalized_style["name"] or boundaryType)+ f" boundary ({boundaryType})",
                        is_3d = is_3d,
                        hovertemplate = hovertemplate
                        )
       
        
    else:
        centered = unique_points - unique_points.mean(axis=0)
        rank = np.linalg.matrix_rank(centered)
        if rank < 2:
            warnings.warn(
                "Projected 3D points are collinear; a convex hull cannot be formed. "
                "Only points are plotted.",
                stacklevel=2,
                )
        elif rank == 2:
            hovertemplate = _hover_template(
                (normalized_style.get("name") or boundaryType) + f" boundary ({boundaryType})",
                axis_labels,
                )                      
            perimeter = perimeter = _coplanar_perimeter(unique_points)
            
            closed = np.vstack((perimeter, perimeter[0]))
            _add_line_marker_trace(
                fig, 
                (closed[:, 0], closed[:, 1], closed[:, 2]),
                normalized_style,
                (normalized_style["name"] or boundaryType)+f" boundary ({boundaryType})",
                hovertemplate = hovertemplate
                )
            
        else:
            try:
                do_hull = True
                hull = ConvexHull(unique_points)
            except QhullError:
                warnings.warn("Could not compute a 3D convex hull for the projected points, only points are plotted")
                do_hull = False
            if do_hull:
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
                
                
                hovertemplate = _hover_template(
                    (normalized_style.get("name") or boundaryType) + f" boundary ({boundaryType})",
                    axis_labels,
                    ) 
                _add_line_marker_trace(fig,
                                       tuple(line_coordinates),
                                       normalized_style, 
                                       (normalized_style["name"] or boundaryType) + f" boundary  ({boundaryType})",
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
                 name= (normalized_style["name"] or boundaryType)+ f" boundary faces  ({boundaryType})",
                 showlegend=True,
                 hovertemplate =hovertemplate  
                 )
                fig.add_trace(mesh)

def _plot_experiment_points(fig,experiment_points,axis_indices,axis_labels,normalized_style,boundaryType,extraLabel=""):
    (np,go,ConvexHull,QhullError) = _require_plotting_dependencies()
    markers_loop = ["cross",
                    "diamond",
                    "diamond-open",
                    "square",
                    "square-open",
                    "x"]  
    is_3d = len(axis_indices) == 3
    for ip,point_set in enumerate(experiment_points.point_sets):
         
         trace_style = {
             **normalized_style,
             "markersize": normalized_style["markersize"] + 3,
             "marker": markers_loop[ip % len(markers_loop)],
             }       
         customdata = [[point_set.id,point.id] for point in point_set.points]
         hovertemplate = _hover_template(extraLabel,
                 axis_labels,
                 include_point_ids=True,
                 )
         data_experiment = np.asarray([point.coordinates for point in point_set.points])
         projected_experiment = data_experiment[:,axis_indices]
         _add_points_trace(fig,
                           projected_experiment, 
                           trace_style, 
                           (normalized_style["name"] or boundaryType)+ " "+point_set.id,
                           is_3d = is_3d,
                           customdata = customdata,
                           hovertemplate = hovertemplate)
        
def add_boundary_plot(boundary:lsuq.Boundary,plot_axes: list[str] | list [int],style = None,axes: lsuq.Axes = None, fig = None,experiment_points = None,extraLabel = ""):   
    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        raise ImportError(
            "Plotting requires the optional dependency 'plotly'. "
            "Install it with: pip install pylsuq[plotting]"
        ) from exc
    
    if fig is None:
        fig = go.Figure()
    
       
    
    normalized_style = _style(style)
    axis_indices = _axis_indices(plot_axes, axes)
    axis_labels = _axis_labels(axis_indices, axes)
    dimension = len(axis_indices)
    
    if dimension not in (2, 3):
        raise ValueError("dims must resolve to exactly two or three dimensions.")
        
    
    boundaryType = boundary.shape.__class__.__name__
    
    if isinstance(boundary.shape,lsuq.HyperRectangle):
        _plot_hyper_rectangle(fig, boundary.shape, axis_indices, axis_labels, normalized_style,boundaryType) 

    elif isinstance(boundary.shape,lsuq.ConvexHull): 
        _plot_convex_hull(fig,boundary.shape,axis_indices,axis_labels,normalized_style,boundaryType)
    else:
        raise TypeError(
            f"Unsupported boundary shape: {type(boundary.shape).__name__}"
        )
    if experiment_points is not None:
        _plot_experiment_points(fig,experiment_points,axis_indices,axis_labels,normalized_style,boundaryType,extraLabel=extraLabel)
       
            
    _set_axis_titles(fig, axis_labels)    
   
    
    return fig

def add_domain_plot(domain:lsuq.ActivityDomain | lsuq.TypedOperationalDomain,plot_axes: list[str] | list[int],style = None,fig = None ):      
    (np,go,ConvexHull,QhullError) = _require_plotting_dependencies()
    if style is None:
        style = {}
    if style.get('label') is None:
        style['label'] = domain.id
    if fig is None:
        fig = go.Figure()
        
    add_boundary_plot(fig = fig,boundary = domain.boundary,axes = domain.axes,plot_axes = plot_axes,style = style,experiment_points=domain.experiment_points,extraLabel=domain.id)
    
    return fig

