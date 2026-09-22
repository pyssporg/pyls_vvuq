import pylsuq as lsuq

# set axis
axes = lsuq.Axes([lsuq.Axis(name="mach", unit="1"), lsuq.Axis(name="alt", unit="m")])
# set boundary
boundary = lsuq.Boundary(lsuq.ConvexHull([lsuq.Point([0, 0]), lsuq.Point([1, 0]), lsuq.Point([0, 1]), lsuq.Point([1, 1])]))
od = lsuq.OperationalDomain(axes=axes, boundary=boundary)
lsuq.save_xml("pylsuq/od.xml", od)