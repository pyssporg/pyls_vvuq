import pylsuq as lsuq
from pathlib import Path

# create output directory
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(parents=True, exist_ok=True)

# set axis
axes = lsuq.Axes([lsuq.Axis(name="mach", unit="1"), lsuq.Axis(name="alt", unit="m")])
# set boundary
boundary = lsuq.Boundary(lsuq.ConvexHull([lsuq.Point([0, 0]), lsuq.Point([1, 0]), lsuq.Point([0, 1]), lsuq.Point([1, 1])]))
od = lsuq.OperationalDomain(axes=axes, boundary=boundary)
lsuq.save_xml(output_dir / "od.xml", od)