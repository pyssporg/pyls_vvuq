import pylsuq as lsuq
from pathlib import Path

# create output directory
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

# Points in DoUQ_1, to define parameterset
p0 = lsuq.Point(coordinates=[0, 350, 200, 1, 1, 20, 20, 1, 1, 1, 35], id='P0')
p1 = lsuq.Point(coordinates=[0, 400, 200, 1, 1, 20, 20, 1, 1, 1, 35], id='P1')

points = lsuq.Points([p0, p1])

# Observed variables in the results
observedvariables = lsuq.ObservedVariables(observed_variables = [lsuq.ObservedVariable('qA',unit = 'l/min'),
                                            lsuq.ObservedVariable('qB',unit = 'l/min')])

pointset = lsuq.PointSet(points, id='DoUQ_1', parameters=observedvariables)

experiment_points = lsuq.ExperimentPoints(point_sets=[pointset])

parameterset = lsuq.ParameterSet(operational_domain = experiment_points)

# UQ results, to define results set
p0exp_qA = lsuq.Normal(mu = -0.063, sigma = 0.0028, minimum = -0.07,maximum = -0.057,observed_variable='qA')
p0exp_qB = lsuq.Normal(mu = 0, sigma = 0,minimum = 0,maximum = 0,observed_variable='qB')

p1exp_qA = lsuq.Normal(mu = -8.6, sigma = 0.0028,minimum = -9.6,maximum = -7.9,observed_variable='qA')
p1exp_qB = lsuq.Normal(mu = 4.6, sigma = 0.2,minimum = 4.2,maximum = 5.1,observed_variable='qB')

p0Dist = lsuq.Results(distributions=[p0exp_qA,p0exp_qB],point = 'P0')
p1Dist = lsuq.Results(distributions=[p1exp_qA,p1exp_qB],point = 'P1')
result_set = lsuq.ResultSet(results=[p0Dist,p1Dist])

# Information gathered in activities class
uq_activity = lsuq.ForwardUncertaintyQuantification(parameter_set=parameterset,result_set = result_set)


# # Save as XML
lsuq.save_xml(output_dir / "douq.xml", uq_activity)