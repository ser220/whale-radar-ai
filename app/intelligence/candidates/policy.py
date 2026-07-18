from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateIdentityPolicy:
    version: str = "v1"

    include_subject: bool = True
    include_category: bool = True
    include_hypothesis_reference: bool = True

    def validate(self) -> None:
        if self.version != "v1":
            raise ValueError(
                "unsupported identity policy version"
            )
