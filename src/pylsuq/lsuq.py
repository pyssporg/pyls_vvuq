from dataclasses import dataclass, field, KW_ONLY
from typing import ClassVar
from collections.abc import MutableSequence

from lxml import etree as et

from pylsuq.domelem import DomElem, xml_metadata, xml_attr
from pylsuq.ssc import ATopLevelMetaData
from collections.abc import MutableSequence


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
class ErrorMetric(UQElem):
    """
    Represents an error metric in results.
    """
    type: str = field(metadata=xml_attr())
    value: float = field(metadata=xml_attr())
    name: str | None = field(default=None, metadata=xml_attr())
    threshold: float | None = field(default=None, metadata=xml_attr())
    observed_variable: str | None = field(
        default=None,
        metadata=xml_attr(name="observedVariable")
    )

@dataclass
class Results(UQElem):
    """
    Container for results, which can be distributions or error metrics.
    Supports external data sources via AExternalSource.
    """
    # TODO: Add distribution support once GDistribution is defined
    error_metrics: list[ErrorMetric] = field(default_factory=list)
    point: str | None = field(default=None, metadata=xml_attr())


    # AExternalSource attributes
    source: str | None = field(default=None, metadata=xml_attr())
    type: str | None = field(default=None, metadata=xml_attr())
    source_base: str | None = field(
        default=None,
        metadata=xml_attr(name="sourceBase")
    )
    def set_point_reference(self, point_id: str) -> None:
        """Set reference to a point by ID."""
        self.point = point_id

@dataclass
class ResultSet(UQElem):
    """Container for multiple Results elements."""
    results: list[Results] = field(default_factory=list)

@dataclass
class ForwardUncertaintyQuantification(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = field(default=None)
    #desired_results: DesiredResults | None = field(default=None)
    #simulation_setting: SimulationSetting | None = field(default=None)
    #sampling_method: SamplingMethod | None = field(default=None)
    #result_set: ResultSet | None = field(default=None)

@dataclass
class  Validation(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = field(default=None)
    id: str | None = field(default=None, metadata=xml_attr())
    #desired_results: DesiredResults | None = field(default=None)
    #simulation_setting: SimulationSetting | None = field(default=None)
    #sampling_method: SamplingMethod | None = field(default=None)
    result_set: ResultSet | None = field(default=None)
    activity_domain_ref: str |  None = field(default=None)



@dataclass
class  Verification(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = field(default=None)
    id: str | None = field(default=None, metadata=xml_attr())
    #desired_results: DesiredResults | None = field(default=None)
    #simulation_setting: SimulationSetting | None = field(default=None)
    #sampling_method: SamplingMethod | None = field(default=None)
    #result_set: ResultSet | None = field(default=None)

@dataclass
class  Calibration(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = field(default=None)
    id: str | None = field(default=None, metadata=xml_attr())
    #desired_results: DesiredResults | None = field(default=None)
    #simulation_setting: SimulationSetting | None = field(default=None)
    #sampling_method: SamplingMethod | None = field(default=None)
    #result_set: ResultSet | None = field(default=None)

@dataclass
class  SensitivityAnalysis(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = field(default=None)
    id: str | None = field(default=None, metadata=xml_attr())
    #desired_results: DesiredResults | None = field(default=None)
    #simulation_setting: SimulationSetting | None = field(default=None)
    #sampling_method: SamplingMethod | None = field(default=None)
    #result_set: ResultSet | None = field(default=None)



@dataclass
class Activities(UQElem, MutableSequence):
    """
    Container for all activity types.
    Activities can be interspersed in any order (Verification, Calibration,
    Validation, SensitivityAnalysis, ForwardUncertaintyQuantification).

    Attributes:
        activities: List of activities in document order (can be mixed types)
        id: Optional identifier
        credibility_level: Optional credibility level for all activities
    """
    activities: list = field(default_factory=list)

    id: str | None = field(default=None, metadata=xml_attr())
    credibility_level: str | None = field(
        default=None,
        metadata=xml_attr(name="credibilityLevel")
    )

    def __getitem__(self, idx: int):
        """Get an activity by index."""
        return self.activities[idx]

    def __setitem__(self, idx: int, value) -> None:
        """Set an activity at index."""
        self.activities[idx] = value

    def __delitem__(self, idx: int) -> None:
        """Delete an activity at index."""
        del self.activities[idx]

    def __len__(self) -> int:
        """Return total number of activities."""
        return len(self.activities)

    def insert(self, idx: int, value) -> None:
        """Insert an activity at index."""
        self.activities.insert(idx, value)

    def add_verification(self, verification: 'Verification') -> None:
        """Add a verification activity."""
        self.activities.append(verification)

    def add_calibration(self, calibration: 'Calibration') -> None:
        """Add a calibration activity."""
        self.activities.append(calibration)

    def add_validation(self, validation: 'Validation') -> None:
        """Add a validation activity."""
        self.activities.append(validation)

    def add_sensitivity_analysis(self, sa: 'SensitivityAnalysis') -> None:
        """Add a sensitivity analysis activity."""
        self.activities.append(sa)

    def add_forward_uq(self, forward_uq: 'ForwardUncertaintyQuantification') -> None:
        """Add a forward UQ activity."""
        self.activities.append(forward_uq)

    def get_verifications(self) -> list['Verification']:
        """Return all verification activities in document order."""
        from pylsuq.uq import Verification
        return [a for a in self.activities if isinstance(a, Verification)]

    def get_calibrations(self) -> list['Calibration']:
        """Return all calibration activities in document order."""
        from pylsuq.uq import Calibration
        return [a for a in self.activities if isinstance(a, Calibration)]

    def get_validations(self) -> list['Validation']:
        """Return all validation activities in document order."""
        from pylsuq.uq import Validation
        return [a for a in self.activities if isinstance(a, Validation)]

    def get_sensitivity_analyses(self) -> list['SensitivityAnalysis']:
        """Return all sensitivity analysis activities in document order."""
        from pylsuq.uq import SensitivityAnalysis
        return [a for a in self.activities if isinstance(a, SensitivityAnalysis)]

    def get_forward_uqs(self) -> list['ForwardUncertaintyQuantification']:
        """Return all forward UQ activities in document order."""
        from pylsuq.uq import ForwardUncertaintyQuantification
        return [a for a in self.activities if isinstance(a, ForwardUncertaintyQuantification)]



@dataclass
class Model(UQElem):
    name: str | None = field(default=None, metadata=xml_attr())
    file: str | None = field(default=None, metadata=xml_attr())
    model: str | None = field(default=None, metadata=xml_attr())
    model_resource_metadata: str | None = field(
        default=None, metadata=xml_attr(name="modelResourceMetaData")
    )


@dataclass
class UncertaintyQuantification(UQElem, ATopLevelMetaData, is_document=True):
    """
    Root element for UQ metadata.
    """
    activities: Activities
    name: str = field(metadata=xml_attr())

    model: Model | None = field(default=None)
    #required_assumptions: list[RequiredAssumptions] = field(default_factory=list)
    #domains: Domains | None = field(default=None)

    info: str | None = field(default=None, metadata=xml_attr())
    required_assumptions_refs: str | None = field(
        default=None,
        metadata=xml_attr(name="requiredAssumptionsRefs")
    )
    stmd_ref: str | None = field(
        default=None,
        metadata=xml_attr(name="stmdRef")
    )
    srmd_ref: str | None = field(
        default=None,
        metadata=xml_attr(name="srmdRef")
    )


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
