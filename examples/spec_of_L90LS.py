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

# ------------------- Data common for all experiments ---------------
axes_exp = lsuq.Axes(
    [lsuq.Axis(name="uA", unit="mA"),
     lsuq.Axis(name="uB", unit="mA"),
     lsuq.Axis(name="pA", unit="bar"),
     lsuq.Axis(name="pB", unit="bar")])

# Experiment observed variables
observedvariables = lsuq.ObservedVariables(observed_variables = [lsuq.ObservedVariable('qA',unit = 'l/min'),    
                                                                 lsuq.ObservedVariable('qB',unit = 'l/min')])


# ------------------- UQ EXPERIMENT 1 ---------------------------    
# Define uncertain parameter of experiment
uncrtKqGain1_MI = lsuq.UncertainParameter(distribution = lsuq.Normal(mu = 1, sigma = 0.1),name = 'KqMI_PBAT_gain')
uqname = "DoUQ_1"
parameters = lsuq.Parameters(uncertain_parameters = [uncrtKqGain1_MI])
parameterset = lsuq.ParameterSet(parameters = parameters)

axes_uq = axes_exp

# Experiment coordinates
p0 = lsuq.Point(coordinates=[600, 0, 0, 5], id=uqname + '_P0')
p1 = lsuq.Point(coordinates=[325, 0, 0, 3.5], id=uqname + '_P1')
p2 = lsuq.Point(coordinates=[550, 0, 0, 35], id=uqname + '_P2')
p3 = lsuq.Point(coordinates=[350, 0, 0, 35], id=uqname + '_P3')

points = lsuq.Points([p0, p1, p2, p3])
pointset = lsuq.PointSet(points, id='PointSet0', parameters=parameters)
experiment_points = lsuq.ExperimentPoints(point_sets=[pointset])

boundary_uq = lsuq.Boundary(lsuq.ConvexHull([lsuq.Point(p0.coordinates),lsuq.Point(p1.coordinates),lsuq.Point(p2.coordinates),lsuq.Point(p3.coordinates)]))

# Define as an activity domain
DoUQ_1 = lsuq.ActivityDomain(id = uqname, name = uqname, kind = 'UncertaintyQuantification' ,experiment_points = experiment_points, axes = axes_uq,boundary = boundary_uq)

# Add to domains element
domains.add_activity_domain(DoUQ_1)


# Experiment results
p0exp_qA = lsuq.Normal(mu=1.11e-14, sigma=4.97e-16, minimum=1.01e-14, maximum=1.23e-14)
p0exp_qB = lsuq.Normal(mu=-42.5, sigma=1.91, minimum=-47.3, maximum=-38.7)

p1exp_qA = lsuq.Normal(mu = 0, sigma = 0, minimum = 0,maximum = 0)
p1exp_qB = lsuq.Normal(mu = 0, sigma = 0,minimum = 0,maximum = 0)

p2exp_qA = lsuq.Normal(mu=63.9, sigma=2.63, minimum=58.5, maximum=70.5)
p2exp_qB = lsuq.Normal(mu=-124.2, sigma=5.52, minimum=-138.0, maximum=-112.8)

p3exp_qA = lsuq.Normal(mu=0.16, sigma=0.00706, minimum=0.145, maximum=0.178)
p3exp_qB = lsuq.Normal(mu=-1.27, sigma=0.0566, minimum=-1.41, maximum=-1.16)

p0Dist = lsuq.Results(distributions=[p0exp_qA,p0exp_qB],point = p0.id)
p1Dist = lsuq.Results(distributions=[p1exp_qA,p1exp_qB],point = p1.id)
p2Dist = lsuq.Results(distributions=[p2exp_qA,p2exp_qB],point = p2.id)
p3Dist = lsuq.Results(distributions=[p3exp_qA,p3exp_qB],point = p3.id)

result_set = lsuq.ResultSet(results=[p0Dist,p1Dist,p2Dist,p3Dist])



# Combine everything in the fwduq activity
uq_activity = lsuq.ForwardUncertaintyQuantification(result_set = result_set,activity_domain_ref = DoUQ_1.id,observed_variables=observedvariables)
activities = lsuq.Activities()
activities.add_forward_uq(uq_activity)

# ------------------- UQ EXPERIMENT 2 ---------------------------    
# Define uncertain parameter of experiment
uncrtKqGain2_MI = lsuq.UncertainParameter(distribution = lsuq.Normal(mu = 1, sigma = 0.1),name = 'KqMI_PBAT_gain')
parameters2 = lsuq.Parameters(uncertain_parameters = [uncrtKqGain2_MI])
parameterset = lsuq.ParameterSet(parameters = parameters2)
uqname = "DoUQ_2"
axes_uq2 = axes_exp

# Experiment coordinates
p02 = lsuq.Point(coordinates=[450, 0, 0, 3.5], id=uqname+'_P0')
p12 = lsuq.Point(coordinates=[500, 0, 0, 3.5], id=uqname+'_P1')
p22= lsuq.Point(coordinates=[475, 0, 0, 35], id=uqname+'_P2')
p32 = lsuq.Point(coordinates=[500, 0, 0, 35], id=uqname+'_P3')

points2 = lsuq.Points([p02, p12, p22, p32])
pointset2 = lsuq.PointSet(points2, id='PointSet0', parameters=parameters2)
experiment_points2 = lsuq.ExperimentPoints(point_sets=[pointset2])

boundary_uq2 = lsuq.Boundary(lsuq.ConvexHull([lsuq.Point(p02.coordinates),lsuq.Point(p12.coordinates),lsuq.Point(p22.coordinates),lsuq.Point(p32.coordinates)]))

# Define as an activity domain
DoUQ_2 = lsuq.ActivityDomain(id = uqname, name =uqname, kind = 'UncertaintyQuantification' ,experiment_points = experiment_points2, axes = axes_uq2,boundary = boundary_uq2)

# Add to domains element
domains.add_activity_domain(DoUQ_2)

# Experiment results
p02exp_qA = lsuq.Normal(mu=35.4, sigma=1.51, minimum=32.3, maximum=39.2)
p02exp_qB = lsuq.Normal(mu=-17.3, sigma=0.77, minimum=-19.2, maximum=-15.7)

p12exp_qA = lsuq.Normal(mu=63.2, sigma=2.6, minimum=57.8, maximum=69.8)
p12exp_qB = lsuq.Normal( mu=-30.4, sigma=1.35, minimum=-33.8, maximum=-27.6)

p22exp_qA = lsuq.Normal(mu=52.5, sigma=2.19, minimum=47.9, maximum=58.0)
p22exp_qB = lsuq.Normal(mu=-102.5, sigma=4.55, minimum=-113.8, maximum=-93.1)

p32exp_qA = lsuq.Normal(mu=63.2, sigma=2.6, minimum=57.8, maximum=69.8)
p32exp_qB = lsuq.Normal(mu=-122.8, sigma=5.46, minimum=-136.5, maximum=-111.6)

p02Dist = lsuq.Results(distributions=[p02exp_qA,p02exp_qB],point = p02.id)
p12Dist = lsuq.Results(distributions=[p12exp_qA,p12exp_qB],point = p12.id)
p22Dist = lsuq.Results(distributions=[p22exp_qA,p22exp_qB],point = p22.id)
p32Dist = lsuq.Results(distributions=[p32exp_qA,p32exp_qB],point = p32.id)

result_set2 = lsuq.ResultSet(results=[p02Dist,p12Dist,p22Dist,p32Dist])



# Combine everything in the fwduq activity
uq_activity2 = lsuq.ForwardUncertaintyQuantification(result_set = result_set2,activity_domain_ref = DoUQ_2.id,observed_variables=observedvariables)
activities.add_forward_uq(uq_activity2)

# ------------------- VALIDATION EXPERIMENT ---------------------------  
expname = "DoV"
axes_v = axes_exp

# Experiment coordinates
pv0 = lsuq.Point(coordinates=[480, 0, 0, 20], id=expname+'_P0')
pv1 = lsuq.Point(coordinates=[420, 0, 0, 70], id=expname+'_P1')
pv2= lsuq.Point(coordinates=[550, 0, 0, 140], id=expname+'_P2')
pv3  = lsuq.Point(coordinates=[900, 0, 0, 100], id=expname+'_P3')
pv4 = lsuq.Point(coordinates=[800, 0, 0, 10], id=expname+'_P4')

pointsv = lsuq.Points([pv0, pv1, pv2, pv3, pv4])
pointsetv = lsuq.PointSet(pointsv, id='PointSet0')
experiment_pointsv = lsuq.ExperimentPoints(point_sets=[pointsetv])

boundary_v = lsuq.Boundary(lsuq.ConvexHull([lsuq.Point(pv0.coordinates),lsuq.Point(pv1.coordinates),lsuq.Point(pv2.coordinates),lsuq.Point(pv3.coordinates),lsuq.Point(pv4.coordinates)]))

# Define as an activity domain
DoV = lsuq.ActivityDomain(id = expname, name =expname, kind = 'Validation' ,experiment_points = experiment_pointsv, axes = axes_v,boundary = boundary_v)

# Add to domains element
domains.add_activity_domain(DoV)

# Validation results, for all points, to define result_set
pv0error_qA = lsuq.ErrorMetric(type='relativeError', name='pv0', value=0.03, observed_variable='qA')
pv0error_qB = lsuq.ErrorMetric(type='relativeError', name='pv0', value=0.02, observed_variable='qB')
pv0error = lsuq.Results(error_metrics=[pv0error_qA, pv0error_qB])

pv1error_qA = lsuq.ErrorMetric(type='relativeError', name='pv1', value=0.01, observed_variable='qA')
pv1error_qB = lsuq.ErrorMetric(type='relativeError', name='pv1', value=0.05, observed_variable='qB')
pv1error = lsuq.Results(error_metrics=[pv1error_qA, pv1error_qB])

pv2error_qA = lsuq.ErrorMetric(type='relativeError', name='pv2', value=0.06, observed_variable='qA')
pv2error_qB = lsuq.ErrorMetric(type='relativeError', name='pv2', value=-0.02, observed_variable='qB')
pv2error = lsuq.Results(error_metrics=[pv2error_qA, pv2error_qB])

pv3error_qA = lsuq.ErrorMetric(type='relativeError', name='pv3', value=-0.03, observed_variable='qA')
pv3error_qB = lsuq.ErrorMetric(type='relativeError', name='pv3', value=0.07, observed_variable='qB')
pv3error = lsuq.Results(error_metrics=[pv3error_qA, pv3error_qB])

pv4error_qA = lsuq.ErrorMetric(type='relativeError', name='pv4', value=0.06, observed_variable='qA')
pv4error_qB = lsuq.ErrorMetric(type='relativeError', name='pv4', value=-0.05, observed_variable='qB')
pv4error = lsuq.Results(error_metrics=[pv4error_qA, pv4error_qB])

result_setv = lsuq.ResultSet(results=[pv0error, pv1error, pv2error, pv3error, pv4error])

# Combine everything in the validation activity
v_activity = lsuq.Validation(result_set = result_setv,activity_domain_ref = DoV.id,observed_variables=observedvariables)
activities.add_validation(v_activity)

# Create full file
UQout = lsuq.UncertaintyQuantification(name='test',activities = activities,domains = domains,model=model,author='Viktor larsson')
lsuq.save_xml(output_dir / "L90LS_UD_OS_OS_UQ.xml", UQout)
