# from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar
from collections.abc import MutableSequence
from enum import Enum

from lxml import etree as et

from pylsuq.domelem import DomElem, xml_metadata, xml_attr
from pylsuq.ssc import ATopLevelMetaData

UQ_NAMESPACE = "http://openscaling.org/UQ1/UncertaintyQuantification"
et.register_namespace("uq", UQ_NAMESPACE)


class UQElem(DomElem):
    NS: ClassVar[str | None] = UQ_NAMESPACE


# ============================================================================
# ENUMERATIONS
# ============================================================================

class TypedOperationalDomainKind(Enum):
    """Domain role in the ODD/OD/ModelOD hierarchy"""
    OPERATIONAL_DESIGN_DOMAIN = "OperationalDesignDomain"
    REQUESTED_OPERATIONAL_DOMAIN = "RequestedOperationalDomain"
    MODELED_OPERATIONAL_DOMAIN = "ModeledOperationalDomain"


# ============================================================================
# LEAF CLASSES (no dependencies on other custom classes)
# ============================================================================

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
class Axis(UQElem):
    name: str = field(metadata=xml_attr())
    unit: str | None = field(default=None, metadata=xml_attr())
    id: str | None = field(default=None, metadata=xml_attr())


@dataclass
class Parameter(UQElem):
    """Deterministic parameter."""
    name: str
    value: str | int | float | bool
    unit: str | None = None

    def to_dict(self) -> dict:
        return {'name': self.name, 'value': self.value, 'unit': self.unit}


@dataclass
class CredibilityAssessment(UQElem):
    level: str
    purpose: str | None = None
    standard: str | None = None
    description: str | None = None


@dataclass
class ProcessContext(UQElem):
    """Process and phase context for an artifact"""
    process: str | None = None
    phase: str | None = None
    glueParticleRef: str | None = None
    description: str | None = None


@dataclass
class ObservedVariable(UQElem):
    name: str = field(metadata=xml_attr())
    distribution_approximation: str | None = field(
        default=None,
        metadata=xml_attr(name="distributionApproximation")
    )
    unit: str | None = field(default=None, metadata=xml_attr())


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
class ActivitySettings(UQElem):
    """Settings for an activity."""
    method: str | None = None
    description: str | None = None
    key_values: dict | None = None

    def to_dict(self) -> dict:
        return {
            'method': self.method,
            'description': self.description,
            'key_values': self.key_values,
        }


@dataclass
class Annotations(UQElem):
    """Placeholder for Annotations"""
    content: str | None = None


@dataclass
class RequiredAssumptions(UQElem):
    """Placeholder for RequiredAssumptions"""
    id: str | None = None
    description: str | None = None


# ============================================================================
# COLLECTION CLASSES (depend on leaf classes)
# ============================================================================

@dataclass
class UncertainParameter(UQElem):
    """Parameter with uncertainty."""
    name: str = field(metadata=xml_attr())
    distribution: str = field(metadata=xml_attr())
    mean: float | None = field(default=None, metadata=xml_attr())
    stdDev: float | None = field(default=None, metadata=xml_attr())
    min: float | None = field(default=None, metadata=xml_attr())
    max: float | None = field(default=None, metadata=xml_attr())

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'distribution': self.distribution,
            'mean': self.mean,
            'stdDev': self.stdDev,
            'min': self.min,
            'max': self.max,
        }


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
class ObservedVariables(UQElem, MutableSequence):
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
class Parameters(UQElem):
    uncertain_parameters: list[UncertainParameter] = field(default_factory=list)
    id: str | None = field(default=None, metadata=xml_attr())


@dataclass
class ConvexHull(UQElem, MutableSequence):
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
class Box(UQElem, MutableSequence):
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
class Results(UQElem):
    """
    Container for results, which can be distributions or error metrics.
    Supports external data sources via AExternalSource.
    """
    error_metrics: list[ErrorMetric] = field(default_factory=list)
    point: str | None = field(default=None, metadata=xml_attr())
    source: str | None = field(default=None, metadata=xml_attr())
    type: str | None = field(default=None, metadata=xml_attr())
    source_base: str | None = field(
        default=None,
        metadata=xml_attr(name="sourceBase")
    )

    def set_point_reference(self, point_id: str) -> None:
        """Set reference to a point by ID."""
        self.point = point_id


# ============================================================================
# BOUNDARY TYPES
# ============================================================================

@dataclass
class Boundary(UQElem):
    shape: ConvexHull | Box


# ============================================================================
# GEOMETRY & DOMAIN TYPES
# ============================================================================

@dataclass
class ResultSet(UQElem):
    """Container for multiple Results elements."""
    results: list[Results] = field(default_factory=list)


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
    point_sets: list[PointSet] = field(default_factory=list)

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
class OperationalDomain(UQElem):
    axes: Axes
    boundary: Boundary
    experiment_points: ExperimentPoints | None = None


@dataclass
class ParameterSet(UQElem):
    parameters: Parameters | None = None
    operational_domain: OperationalDomain | None = None
    id: str | None = field(default=None, metadata=xml_attr())
    description: str | None = field(default=None, metadata=xml_attr())


# ============================================================================
# DOMAIN HIERARCHY TYPES
# ============================================================================

@dataclass
class TypedOperationalDomain(UQElem):
    """Domain with semantic metadata: kind, hierarchy, and credibility."""
    id: str
    kind: TypedOperationalDomainKind
    name: str | None = None
    geometryKind: str | None = None
    parentRef: str | None = None
    srmdRef: str | None = None
    description: str | None = None
    credibility_assessment: CredibilityAssessment | None = None
    process_context: ProcessContext | None = None
    axes: Axes | None = None
    boundary: Boundary | None = None
    experiment_points: ExperimentPoints | None = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'kind': self.kind.value,
            'name': self.name,
            'geometryKind': self.geometryKind,
            'parentRef': self.parentRef,
            'srmdRef': self.srmdRef,
            'description': self.description,
            'credibility_assessment': self.credibility_assessment.to_dict() if self.credibility_assessment else None,
            'process_context': self.process_context.to_dict() if self.process_context else None,
        }


@dataclass
class ActivityDomain(UQElem):
    """
    Domain scoped to a specific activity (DoVerification, DoCalibration, DoV, DoSA, DoUQ).
    A sub-region of parent ModelOD with its own boundary.
    """
    id: str
    kind: str
    name: str | None = None
    domainRef: str | None = None
    srmdRef: str | None = None
    description: str | None = None
    axes: Axes | None = None
    boundary: Boundary | None = None
    experiment_points: ExperimentPoints | None = None
    settings: ActivitySettings | None = None
    result_set: ResultSet | None = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'kind': self.kind,
            'name': self.name,
            'domainRef': self.domainRef,
            'srmdRef': self.srmdRef,
            'description': self.description,
            'settings': self.settings.to_dict() if self.settings else None,
        }


@dataclass
class Domains(UQElem):
    """Top-level container for all domain definitions"""
    typed_operational_domains: list[TypedOperationalDomain] = field(default_factory=list)
    activity_domains: list[ActivityDomain] = field(default_factory=list)

    def add_typed_operational_domain(self, domain: TypedOperationalDomain) -> None:
        """Add a TypedOperationalDomain (ODD, RequestedOD, or ModeledOD)"""
        self.typed_operational_domains.append(domain)

    def add_activity_domain(self, domain: ActivityDomain) -> None:
        """Add an ActivityDomain (DoVerification, DoCalibration, etc.)"""
        self.activity_domains.append(domain)


# ============================================================================
# ACTIVITY TYPES
# ============================================================================

@dataclass
class ForwardUncertaintyQuantification(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = None
    result_set: ResultSet | None = None


@dataclass
class Verification(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = None
    id: str | None = field(default=None, metadata=xml_attr())


@dataclass
class Calibration(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = None
    id: str | None = field(default=None, metadata=xml_attr())


@dataclass
class Validation(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = None
    result_set: ResultSet | None = None
    id: str | None = field(default=None, metadata=xml_attr())
    activity_domain_ref: str | None = field(
        default=None,
        metadata=xml_attr(name="activityDomainRef")
    )


@dataclass
class SensitivityAnalysis(UQElem):
    parameter_set: ParameterSet
    observed_variables: ObservedVariables | None = None
    id: str | None = field(default=None, metadata=xml_attr())


@dataclass
class Activities(UQElem, MutableSequence):
    """
    Container for all activity types.
    Activities can be interspersed in any order (Verification, Calibration,
    Validation, SensitivityAnalysis, ForwardUncertaintyQuantification).
    """
    activities: list = field(default_factory=list)
    id: str | None = field(default=None, metadata=xml_attr())

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

    def add_verification(self, verification: Verification) -> None:
        """Add a verification activity."""
        self.activities.append(verification)

    def add_calibration(self, calibration: Calibration) -> None:
        """Add a calibration activity."""
        self.activities.append(calibration)

    def add_validation(self, validation: Validation) -> None:
        """Add a validation activity."""
        self.activities.append(validation)

    def add_sensitivity_analysis(self, sa: SensitivityAnalysis) -> None:
        """Add a sensitivity analysis activity."""
        self.activities.append(sa)

    def add_forward_uq(self, forward_uq: ForwardUncertaintyQuantification) -> None:
        """Add a forward UQ activity."""
        self.activities.append(forward_uq)

    def get_verifications(self) -> list[Verification]:
        """Return all verification activities in document order."""
        return [a for a in self.activities if isinstance(a, Verification)]

    def get_calibrations(self) -> list[Calibration]:
        """Return all calibration activities in document order."""
        return [a for a in self.activities if isinstance(a, Calibration)]

    def get_validations(self) -> list[Validation]:
        """Return all validation activities in document order."""
        return [a for a in self.activities if isinstance(a, Validation)]

    def get_sensitivity_analyses(self) -> list[SensitivityAnalysis]:
        """Return all sensitivity analysis activities in document order."""
        return [a for a in self.activities if isinstance(a, SensitivityAnalysis)]

    def get_forward_uqs(self) -> list[ForwardUncertaintyQuantification]:
        """Return all forward UQ activities in document order."""
        return [a for a in self.activities if isinstance(a, ForwardUncertaintyQuantification)]


# ============================================================================
# MODEL & ROOT ELEMENT
# ============================================================================

@dataclass
class Model(UQElem):
    name: str | None = field(default=None, metadata=xml_attr())
    file: str | None = field(default=None, metadata=xml_attr())
    model: str | None = field(default=None, metadata=xml_attr())
    model_resource_metadata: str | None = field(
        default=None, metadata=xml_attr(name="modelResourceMetaData")
    )


@dataclass
class UncertaintyQuantification(UQElem):
    """
    Root element of the UQ1 schema.
    """
    name: str
    info: str | None = None
    requiredAssumptionsRefs: str | None = None
    stmdRef: str | None = None
    srmdRef: str | None = None
    version: str | None = None
    domains: Domains | None = None
    model: Model | None = None
    activities: Activities | None = None
    classifications: list[str] = field(default_factory=list)
    annotations: Annotations | None = None

    def set_domains(self, domains: Domains) -> None:
        """Set the Domains container."""
        self.domains = domains

    def set_model(self, model: Model) -> None:
        """Set the Model."""
        self.model = model

    def set_activities(self, activities: Activities) -> None:
        """Set the Activities container."""
        self.activities = activities

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'info': self.info,
            'requiredAssumptionsRefs': self.requiredAssumptionsRefs,
            'stmdRef': self.stmdRef,
            'srmdRef': self.srmdRef,
            'version': self.version,
            'domains': self.domains if self.domains else None,
            'model': self.model if self.model else None,
            'activities': self.activities if self.activities else None,
        }


def main():
    axes = Axes([Axis(name="mach", unit="1"), Axis(name="alt", unit="m")])
    boundary = Boundary(ConvexHull([Point([0, 0]), Point([0, 0.8]), Point([18000, 0.8]), Point([18000, 2.8])]))
    od = OperationalDomain(axes=axes, boundary=boundary, experiment_points=ExperimentPoints(point_sets=[]))
    elem = od.to_xml(ns=UQ_NAMESPACE)
    print(et.tostring(elem, pretty_print=True, encoding=str))


if __name__ == "__main__":
    main()
