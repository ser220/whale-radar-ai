from enum import Enum


class EvidenceReferenceType(str, Enum):
    OBSERVATION = "OBSERVATION"
    PROVIDER = "PROVIDER"
    SITUATION = "SITUATION"


class EvidenceAssemblyVersion(str, Enum):
    V1 = "V1"
