import pylsuq as lsuq 
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull, QhullError

# Example of visualising operational and activity domains

def ConvexHull_boundary_points_from_points(points: lsuq.Points):
    """
    Return unique original coordinates belonging to the convex hull boundary.

    The hull is calculated using all coordinate dimensions. If the data lies
    in a lower-dimensional subspace because some coordinates are constant or
    linearly dependent, the hull is calculated in that effective subspace.

    Parameters
    ----------
    points : list
        Objects with a `.coordinates` attribute, such as lsuq.Point objects.

    Returns
    -------
    np.ndarray
        Array of full-dimensional coordinates for points on the hull boundary.
    """
    points  = points.points

    # Full coordinates: one row per input point.
    coordinates = np.asarray(
        [point.coordinates for point in points],
        dtype=float,
    )

    # Remove duplicate points, for example P1 and P2.
    unique_coordinates = np.unique(coordinates, axis=0)

    if len(unique_coordinates) == 1:
        coord_out = unique_coordinates

    # Move the point cloud to the origin.
    center = unique_coordinates.mean(axis=0)
    centered = unique_coordinates - center

    # Find the effective dimension/rank of the point cloud.
    _, singular_values, vt = np.linalg.svd(centered, full_matrices=False)

    tolerance = (
        np.finfo(float).eps
        * max(centered.shape)
        * singular_values[0]
    )
    rank = np.sum(singular_values > tolerance)

    # All points are identical after numerical tolerance handling.
    if rank == 0:
        coord_out = unique_coordinates[:1]

    # One-dimensional hull: only the two endpoints are on the boundary.
    if rank == 1:
        direction = vt[0]
        projected = centered @ direction

        endpoint_indices = [
            np.argmin(projected),
            np.argmax(projected),
        ]

        coord_out = unique_coordinates[np.unique(endpoint_indices)]

    # Project into the effective coordinate space before calculating the hull.
    basis = vt[:rank]
    reduced_coordinates = centered @ basis.T

    # A d-dimensional hull needs at least d + 1 unique points.
    if len(unique_coordinates) < rank + 1:
        raise ValueError(
            f"Cannot calculate a {rank}D convex hull from "
            f"{len(unique_coordinates)} unique points."
        )

    try:
        hull = ConvexHull(reduced_coordinates)
    except QhullError as error:
        raise ValueError(
            "Could not calculate the convex hull for these coordinates."
        ) from error

    # In 2D, hull.vertices follows the perimeter order.
    # In 3D or higher, it contains the indices of boundary vertices.
    coord_out =  unique_coordinates[hull.vertices]
    
    return [lsuq.Point(coordinates = coord) for coord in coord_out]

# create output directory
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

# Define an operational domain
axes_od = lsuq.Axes(
    [lsuq.Axis(name="uA", unit="mA"),
     lsuq.Axis(name="uB", unit="mA"),
     lsuq.Axis(name="pP", unit="bar"),
     lsuq.Axis(name="pTA", unit="bar"),
     lsuq.Axis(name="pTB", unit="bar"),
     lsuq.Axis(name="pA", unit="bar"),
     lsuq.Axis(name="pB", unit="bar"),
     lsuq.Axis(name="pLin", unit="bar"),
     lsuq.Axis(name="pLmax", unit="bar"),
     lsuq.Axis(name="p_TP", unit="bar"),
     lsuq.Axis(name="p_PS", unit="bar")])

# set boundary of od
boundary_od = lsuq.Boundary(lsuq.HyperRectangle(
    [lsuq.Point([  0,   0,   0,   0,   0,   0,   0,   0,  0,  0]), 
     lsuq.Point([900, 900, 400,  20,  20, 400, 400, 500, 35, 50])]))

# Define od
od = lsuq.TypedOperationalDomain(id = "L90LS_OD",kind = lsuq.TypedOperationalDomainKind.OPERATIONAL_DESIGN_DOMAIN,axes=axes_od, boundary=boundary_od)

# Start defining forward uq activity
axes_uq = axes_od

# Experiment coordinates
p0 = lsuq.Point(coordinates=[0,350,200,1,1,20, 20 ,1,1,1,35], id='P0')
p1 = lsuq.Point(coordinates=[0,400,200,1,1,20, 20 ,1,1,1,35], id='P1')
p2 = lsuq.Point(coordinates=[0,550,200,1,1,20, 20 ,1,1,1,35], id='P2')
p3 = lsuq.Point(coordinates=[350,0,200,1,1,20, 20 ,1,1,1,35], id='P3')
p4 = lsuq.Point(coordinates=[0,350,200,1,1,150,150,1,1,1,35], id='P4')
p5 = lsuq.Point(coordinates=[600,0,200,1,1,150,150,1,1,1,35], id='P5')
p6 = lsuq.Point(coordinates=[200,0,200,1,1,50,50,1,1,1,35], id='P6')
p7 = lsuq.Point(coordinates=[200,200,200,1,1,50,50,1,1,1,35], id='P7')

# All experiment points collected
points_all = lsuq.Points([p0, p1,p2,p3,p4,p5,p6,p7])


# Define uncertain parameter of experiment
uncrtKqGain1_MI = lsuq.UncertainParameter(distribution = lsuq.Normal(mu = 1, sigma = 0.1),name = 'KqMI_PBAT_gain')
parameters = lsuq.Parameters(uncertain_parameters = [uncrtKqGain1_MI])
parameterset = lsuq.ParameterSet(parameters = parameters)

# Extract convex hull boundary from all experiment points
boundary_points_uq = ConvexHull_boundary_points_from_points(points_all)

# Define boundary of the forward uq domain
boundary_uq = lsuq.Boundary(lsuq.ConvexHull(boundary_points_uq))

# Divide experiment points into two points set
pointset0 = lsuq.PointSet(lsuq.Points([p0, p1,p2,p3,p4]), id='PointSet0', parameters=parameters)
pointset1 = lsuq.PointSet(lsuq.Points([p5,p6,p7]), id='PointSet1', parameters=parameters)
experiment_points = lsuq.ExperimentPoints(point_sets=[pointset0,pointset1])

# Define as an activity domain
DoUQ_1 = lsuq.ActivityDomain(id = 'DoUQ_1', name ='DoUQ_1', kind = 'UncertaintyQuantification' ,experiment_points = experiment_points, axes = axes_uq,boundary = boundary_uq)


# %%

# Decide which axes to project on
plot_axes = [("uA","uB"),("uA","uB","pA"),("uA","pA","pB")]

for ip,sub_plot_axes in enumerate(plot_axes):
    
    # Let first plot define the first figure (plot od first)
    fig = lsuq.add_domain_plot(od,plot_axes = sub_plot_axes,style = {'color':'cornflowerblue'})      
    
    # Add the uq domain to the same figure
    lsuq.add_domain_plot(DoUQ_1,plot_axes = sub_plot_axes,style = {'color':'orangered'},fig=fig)   
    
    # Save figure in html file
    fig.write_html(output_dir / Path( "domains_"+ str(ip) +".html"))


