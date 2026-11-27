import pylsuq as lsuq
from pathlib import Path

# create output directory
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

# set dov experiment
boundary = lsuq.Boundary(
    lsuq.ConvexHull([lsuq.Point([0, 0]), lsuq.Point([1, 0]), lsuq.Point([0, 1]), lsuq.Point([1, 1])]))

# Points in dov1, to define parameterset
p1 = lsuq.Point(coordinates=[0.1, 0.1], id='p1')
p2 = lsuq.Point(coordinates=[0.7, 0.7], id='p2')
points = lsuq.Points([p1, p2])
observedvariables = lsuq.ObservedVariables([lsuq.ObservedVariable('tempIn'), lsuq.ObservedVariable('tempOut')])
pointset = lsuq.PointSet(points, id='dov1', parameters=observedvariables)
experiment_points = lsuq.ExperimentPoints(point_sets=[pointset])
parameterset = lsuq.ParameterSet(operational_domain=experiment_points)

# Validation results, for p1, to define result_set
p1error_tempIn = lsuq.ErrorMetric(type='relativeError', name='p1', value=0.03, observed_variable='tempIn')
p1error_tempOut = lsuq.ErrorMetric(type='relativeError', name='p1', value=0.02, observed_variable='tempIn')
p1error = lsuq.Results(error_metrics=[p1error_tempIn, p1error_tempOut])
result_set = lsuq.ResultSet(results=[p1error])

# Information gathered in activities class
val = lsuq.Validation(parameter_set=parameterset, result_set=result_set)
activities = lsuq.Activities()
activities.add_validation(val)

# Save as XML
lsuq.save_xml(output_dir / "dov.xml", val)