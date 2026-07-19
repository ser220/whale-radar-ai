from enum import Enum


class CandidateAssociationType(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    CONTEXT = "CONTEXT"


class AssociationReferenceVersion(str, Enum):
    V1 = "V1"
