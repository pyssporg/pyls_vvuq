import pylsuq as lsuq
from pathlib import Path

# create output directory
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

# Set model info
model = lsuq.Model(name = 'valve_model',file = 'L90LS_UD_OS_OS.fmu')

# set axis
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
# set boundary
boundary_od = lsuq.Boundary(lsuq.HyperRectangle(
    [lsuq.Point([  0,   0,   0,   0,   0,   0,   0,   0,  0,  0]), 
     lsuq.Point([900, 900, 400,  20,  20, 400, 400, 500, 35, 50])]))

# Define model od
od = lsuq.TypedOperationalDomain(id = "L90LS_OD",kind = lsuq.TypedOperationalDomainKind.OPERATIONAL_DESIGN_DOMAIN,axes=axes_od, boundary=boundary_od)

# Define domains and add od
domains = lsuq.Domains()
domains.add_typed_operational_domain(od)
     
# Define uncertain parameter of experiment
uncrtKqGain1_MI = lsuq.UncertainParameter(distribution = lsuq.Normal(mu = 1, sigma = 0.1),name = 'KqMI_PBAT_gain')
parameters = lsuq.Parameters(uncertain_parameters = [uncrtKqGain1_MI])
parameterset = lsuq.ParameterSet(parameters = parameters)

axes_uq = axes_od = lsuq.Axes(
    [lsuq.Axis(name="uA", unit="mA"),
     lsuq.Axis(name="uB", unit="mA"),
     lsuq.Axis(name="pP", unit="bar")])

# Experiment coordinates
p0 = lsuq.Point(coordinates=[0, 350, 200], id='P0')
p1 = lsuq.Point(coordinates=[0, 400, 200], id='P1')
points = lsuq.Points([p0, p1])
pointset = lsuq.PointSet(points, id='PointSet0', parameters=parameters)
experiment_points = lsuq.ExperimentPoints(point_sets=[pointset])

boundary_uq = lsuq.Boundary(lsuq.ConvexHull([lsuq.Point(p0.coordinates),lsuq.Point(p1.coordinates)]))

# Define as an activity domain
DoUQ_1 = lsuq.ActivityDomain(id = 'DoUQ_1', name ='DoUQ_1', kind = 'UncertaintyQuantification' ,experiment_points = experiment_points, axes = axes_uq,boundary = boundary_uq)

# Add to domains element
domains.add_activity_domain(DoUQ_1)

# Experiment observed variables
observedvariables = lsuq.ObservedVariables(observed_variables = [lsuq.ObservedVariable('qA',unit = 'l/min'),    
                                                                 lsuq.ObservedVariable('qB',unit = 'l/min')])

# Experiment results
p0exp_qA = lsuq.Normal(mu = -0.063, sigma = 0.0028, minimum = -0.07,maximum = -0.057,observed_variable='qA')
p0exp_qB = lsuq.Normal(mu = 0, sigma = 0,minimum = 0,maximum = 0,observed_variable='qB')

p1exp_qA = lsuq.Normal(mu = -8.6, sigma = 0.0028,minimum = -9.6,maximum = -7.9,observed_variable='qA')
p1exp_qB = lsuq.Normal(mu = 4.6, sigma = 0.2,minimum = 4.2,maximum = 5.1,observed_variable='qB')

p0Dist = lsuq.Results(distributions=[p0exp_qA,p0exp_qB],point = p0.id)
p1Dist = lsuq.Results(distributions=[p1exp_qA,p1exp_qB],point = p1.id)
result_set = lsuq.ResultSet(results=[p0Dist,p1Dist])

# Combine everything in the fwduq activity
uq_activity = lsuq.ForwardUncertaintyQuantification(result_set = result_set,activity_domain_ref = DoUQ_1.id,observed_variables=observedvariables)
activities = lsuq.Activities()
activities.add_forward_uq(uq_activity)

# Create full file
UQout = lsuq.UncertaintyQuantification(name='test',activities = activities,domains = domains,model=model,author='Viktor larsson')
lsuq.save_xml(output_dir / "L90LS_UD_OS_OS_UQ.xml", UQout)
