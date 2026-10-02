import pylsuq as lsuq
from pathlib import Path

# create output directory
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

# Set model info
model = lsuq.Model(name = 'valve_model',file = 'L90LS_UD_OS_OS.fmu')

# set axis
axes = lsuq.Axes(
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
# set boundary
boundary = lsuq.Boundary(lsuq.Box(
    [lsuq.Point([0, 900]),
     lsuq.Point([0, 900]),
     lsuq.Point([0, 400]),
     lsuq.Point([0, 20]),
     lsuq.Point([0, 20]),
     lsuq.Point([0, 400]),
     lsuq.Point([0, 400]),
     lsuq.Point([0, 500]),
     lsuq.Point([0, 35]),
     lsuq.Point([0, 50])]))

# Define model od
od = lsuq.TypedOperationalDomain(id = "L90LS_OD",kind = lsuq.TypedOperationalDomainKind.OPERATIONAL_DESIGN_DOMAIN,axes=axes, boundary=boundary)

# Add to domains element
domains = lsuq.Domains()
domains.add_typed_operational_domain(od)

# Add observed variables (to add in parameter set)
observedvariables = lsuq.ObservedVariables(observed_variables = [lsuq.ObservedVariable('qA',unit = 'l/min'),
                                            lsuq.ObservedVariable('qB',unit = 'l/min')])

# Experiment coordinates
p0 = lsuq.Point(coordinates=[0, 350, 200, 1, 1, 20, 20, 1, 1, 1, 35], id='P0')
p1 = lsuq.Point(coordinates=[0, 400, 200, 1, 1, 20, 20, 1, 1, 1, 35], id='P1')
points = lsuq.Points([p0, p1])
pointset = lsuq.PointSet(points, id='PointSet0', parameters=observedvariables)
experiment_points = lsuq.ExperimentPoints(point_sets=[pointset])

# Define uncertain parameter of experiment
uncrtKqGain1_MI = lsuq.UncertainParameter(distribution = lsuq.Normal(mu = 1, sigma = 0.1),name = 'KqMI_PBAT_gain')
parameters = lsuq.Parameters(uncertain_parameters = [uncrtKqGain1_MI])
parameterset = lsuq.ParameterSet(parameters = parameters)

# Define as an acitivity domain
DoUQ_1 = lsuq.ActivityDomain(id = 'DoUQ_1', name ='DoUQ_1', kind = 'UncertaintyQuantification', domainRef = od.id ,experiment_points = experiment_points )
domains.add_activity_domain(DoUQ_1)


# Experiment results
p0exp_qA = lsuq.Normal(mu = -0.063, sigma = 0.0028, minimum = -0.07,maximum = -0.057,observed_variable='qA')
p0exp_qB = lsuq.Normal(mu = 0, sigma = 0,minimum = 0,maximum = 0,observed_variable='qB')

p1exp_qA = lsuq.Normal(mu = -8.6, sigma = 0.0028,minimum = -9.6,maximum = -7.9,observed_variable='qA')
p1exp_qB = lsuq.Normal(mu = 4.6, sigma = 0.2,minimum = 4.2,maximum = 5.1,observed_variable='qB')

p0Dist = lsuq.Results(distributions=[p0exp_qA,p0exp_qB],point = 'P0')
p1Dist = lsuq.Results(distributions=[p1exp_qA,p1exp_qB],point = 'P1')
result_set = lsuq.ResultSet(results=[p0Dist,p1Dist])

# Combine everything in the fwduq activity
uq_activity = lsuq.ForwardUncertaintyQuantification(parameter_set=parameterset,result_set = result_set,activity_domain_ref = 'DoUQ_1')
activities = lsuq.Activities()
activities.add_forward_uq(uq_activity)


# # Save as XML
lsuq.save_xml(output_dir / "douq.xml", domains)