from dataclasses import dataclass, field, KW_ONLY
from typing import ClassVar
from collections.abc import MutableSequence

from lxml import etree as et

from pylsuq.domelem import DomElem, xml_metadata, xml_attr
from pylsuq.ssc import ATopLevelMetaData


UQ_NAMESPACE = "http://openscaling.org/UQ1/UncertaintyQuantification"
et.register_namespace("uq", UQ_NAMESPACE)


class UQElem(DomElem):
    NS: ClassVar[str | None] = UQ_NAMESPACE


@dataclass
class Point(UQElem):
    coordinates: list[float] = field(
        metadata=xml_attr(
            serialize=lambda cs: " ".join(str(c) for c in cs),
            deserialize=lambda s: [float(c) for c in s.strip().split()],
        )
    )
    id: str | None = field(default=None, metadata=xml_attr())


@dataclass
class Parameter(DomElem):
    pass


@dataclass
class UncertainParameter(UQElem):
    pass


@dataclass
class Parameters(UQElem):
    # uncertain_parameters: list[UncertainParameter]

    id: str | None = field(default=None, metadata=xml_attr())


@dataclass
class Points(UQElem, MutableSequence):
    points: list[Point] = field(default_factory=list)

    def __getitem__(self, idx):
        return self.points[idx]

    def __setitem__(self, idx, value):
        self.points[idx] = value

    def __delitem__(self, idx):
        del self.points[idx]

    def __len__(self):
        return len(self.points)

    def insert(self, idx, value):
        self.points.insert(idx, value)


@dataclass
class PointSet(UQElem, MutableSequence):
    points: Points
    parameters: Parameters
    id: str = field(metadata=xml_attr())

    def __getitem__(self, idx):
        return self.points[idx]

    def __setitem__(self, idx, value):
        self.points[idx] = value

    def __delitem__(self, idx):
        del self.points[idx]

    def __len__(self):
        return len(self.points)

    def insert(self, idx, value):
        self.points.insert(idx, value)


@dataclass
class ExperimentPoints(UQElem, MutableSequence):
    point_sets: list[PointSet]

    def __getitem__(self, idx):
        return self.point_sets[idx]

    def __setitem__(self, idx, value):
        self.point_sets[idx] = value

    def __delitem__(self, idx):
        del self.point_sets[idx]

    def __len__(self):
        return len(self.point_sets)

    def insert(self, idx, value):
        self.point_sets.insert(idx, value)


@dataclass
class Box(UQElem, MutableSequence):
    points: list[Point]

    def __getitem__(self, idx):
        return self.points[idx]

    def __setitem__(self, idx, value):
        self.points[idx] = value

    def __delitem__(self, idx):
        del self.points[idx]

    def __len__(self):
        return len(self.points)

    def insert(self, idx, value):
        self.points.insert(idx, value)


@dataclass
class ConvexHull(UQElem, MutableSequence):
    points: list[Point]

    def __getitem__(self, idx):
        return self.points[idx]

    def __setitem__(self, idx, value):
        self.points[idx] = value

    def __delitem__(self, idx):
        del self.points[idx]

    def __len__(self):
        return len(self.points)

    def insert(self, idx, value):
        self.points.insert(idx, value)




@dataclass
class Boundary(UQElem):
    shape: ConvexHull | Box


@dataclass
class Axis(UQElem):
    name: str = field(metadata=xml_attr())
    unit: str | None = field(default=None, metadata=xml_attr())
    id: str | None = field(default=None, metadata=xml_attr())


@dataclass
class Axes(UQElem, MutableSequence):
    axes: list[Axis] = field(default_factory=list)

    def __getitem__(self, idx):
        return self.axes[idx]

    def __setitem__(self, idx, value):
        self.axes[idx] = value

    def __delitem__(self, idx):
        del self.axes[idx]

    def __len__(self):
        return len(self.axes)

    def insert(self, idx, value):
        self.axes.insert(idx, value)


@dataclass
class OperationalDomain(UQElem, is_document=True):
    axes: Axes
    boundary: Boundary
    experiment_points: ExperimentPoints | None = field(default=None)

@dataclass
class ParameterSet(UQElem):
    parameters: Parameters | None = field(default=None)
    operational_domain: OperationalDomain | None = field(default=None)
    # enumerations: Enumerations | None = field(default=None)
    # units: Units | None = field(default=None)
    # annotations: Annotations | None = field(default=None)

    id: str | None = field(default=None, metadata=xml_attr())
    description: str | None = field(default=None, metadata=xml_attr())


@dataclass
class ObservedVariable(UQElem):
    name: str = field(metadata=xml_attr())
    distribution_approximation: str | None = field(
        default=None,
        metadata=xml_attr(name="distributionApproximation")
    )
    unit: str | None = field(default=None, metadata=xml_attr())


@dataclass
class ObservedVariables(UQElem):
    """
    Container for multiple observed variables in a UQ activity.
    Implements MutableSequence for list-like operations on variables.
    """
    observed_variables: list[ObservedVariable] = field(default_factory=list)
    def __getitem__(self, idx: int) -> ObservedVariable:
        """Get an observed variable by index."""
        return self.observed_variables[idx]

    def __setitem__(self, idx: int, value: ObservedVariable) -> None:
        """Set an observed variable at index."""
        if not isinstance(value, ObservedVariable):
            raise TypeError(f"Expected ObservedVariable, got {type(value)}")
        self.observed_variables[idx] = value

    def __delitem__(self, idx: int) -> None:
        """Delete an observed variable at index."""
        del self.observed_variables[idx]

    def __len__(self) -> int:
        """Return the number of observed variables."""
        return len(self.observed_variables)

    def insert(self, idx: int, value: ObservedVariable) -> None:
        """Insert an observed variable at index."""
        if not isinstance(value, ObservedVariable):
            raise TypeError(f"Expected ObservedVariable, got {type(value)}")
        self.observed_variables.insert(idx, value)


@dataclass
class ForwardUncertaintyQuantification(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables
    # desired_results: DesiredResults
    # simulation_setting: SimulationSetting
    # sampling_method: SamplingMethod

@dataclass
class  Validation(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables
    # desired_results: DesiredResults
    # simulation_setting: SimulationSetting
    # sampling_method: SamplingMethod

@dataclass
class  Verification(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables
    # desired_results: DesiredResults
    # simulation_setting: SimulationSetting
    # sampling_method: SamplingMethod

@dataclass
class  Calibration(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables
    # desired_results: DesiredResults
    # simulation_setting: SimulationSetting
    # sampling_method: SamplingMethod

@dataclass
class  SensitivityAnalysis(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables
    # desired_results: DesiredResults
    # simulation_setting: SimulationSetting
    # sampling_method: SamplingMethod



@dataclass
class ExperimentSet(UQElem):
    forward_uq: ForwardUncertaintyQuantification | None = field(default=None)
    validation: Validation | None = field(default=None)
    verification: Verification | None = field(default=None)
    calibration: Calibration | None = field(default=None)
    sensitivity_analysis: SensitivityAnalysis | None = field(default=None)
    id: str | None = field(default=None, metadata=xml_attr())

    def __post_init__(self):
        """Ensure at least one activity is provided."""
        activities = [self.forward_uq, self.validation, self.verification,
                      self.calibration, self.sensitivity_analysis]
        if not any(activities):
            raise ValueError("At least one activity type must be provided")



@dataclass
class Model(UQElem):
    name: str | None = field(default=None, metadata=xml_attr())
    file: str | None = field(default=None, metadata=xml_attr())
    model: str | None = field(default=None, metadata=xml_attr())
    model_resource_metadata: str | None = field(
        default=None, metadata=xml_attr(name="modelResourceMetaData")
    )


@dataclass
class ExperimentSetup(UQElem, ATopLevelMetaData):
    model: Model
    experiment_set: ExperimentSet
    name: str = field(metadata=xml_attr())
    info: str | None = field(default=None, metadata=xml_attr())


def main():
    axes = Axes([Axis(name="mach", unit="1"), Axis(name="alt", unit="m")])
    boundary = Boundary(ConvexHull([Point([0, 0]), Point([0, 0.8]), Point([18000, 0.8]), Point([18000, 2.8])]))
    od = OperationalDomain(axes=axes, boundary=boundary, experiment_points=ExperimentPoints(point_sets=[]))
    elem = od.to_xml(ns=UQ_NAMESPACE)
    print(et.tostring(elem, pretty_print=True, encoding=str))

    # model = Model(name="Example model", file="Example.fmu")
    # experiment_set = ExperimentSet(forward_uq=ForwardUncertaintyQuantification(ParameterSet()))
    # experiment_setup = ExperimentSetup(
    #     model=model, experiment_set=experiment_set, name="Example setup"
    # )

    # elem = experiment_setup.to_xml()
    # print(et.tostring(elem, pretty_print=True, encoding=str))


if __name__ == "__main__":
    main()
