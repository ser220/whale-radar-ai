"""Immutable root-cause tree contract and structural validation."""

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Tuple

from .enums import RootCauseDisposition
from .validation import (
    frozen_mapping,
    mapping_payload,
    plain,
    positive_integer,
    required_text,
    text_tuple,
)


def _edge_tuple(value: Any) -> Tuple[Tuple[str, str], ...]:
    if isinstance(value, (str, bytes, set, frozenset)):
        raise TypeError("edges must be an ordered collection")
    edges = []
    for item in value:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise TypeError("each edge must contain parent and child IDs")
        parent = required_text(item[0], "edge parent")
        child = required_text(item[1], "edge child")
        if parent == child:
            raise ValueError("self-edges are forbidden")
        edges.append((parent, child))
    if len(set(edges)) != len(edges):
        raise ValueError("duplicate edges are forbidden")
    return tuple(sorted(edges))


@dataclass(frozen=True)
class RootCauseTree:
    tree_id: str
    tree_version: str
    candidate_ids: Tuple[str, ...]
    root_candidate_ids: Tuple[str, ...]
    accepted_candidate_ids: Tuple[str, ...]
    rejected_candidate_ids: Tuple[str, ...]
    unresolved_candidate_ids: Tuple[str, ...]
    edges: Tuple[Tuple[str, str], ...]
    maximum_depth: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tree_id", required_text(self.tree_id, "tree_id"))
        object.__setattr__(self, "tree_version", required_text(self.tree_version, "tree_version"))
        candidate_ids = text_tuple(self.candidate_ids, "candidate_ids", required=True)
        roots = text_tuple(self.root_candidate_ids, "root_candidate_ids", required=True)
        accepted = text_tuple(self.accepted_candidate_ids, "accepted_candidate_ids")
        rejected = text_tuple(self.rejected_candidate_ids, "rejected_candidate_ids")
        unresolved = text_tuple(self.unresolved_candidate_ids, "unresolved_candidate_ids")
        edges = _edge_tuple(self.edges)
        maximum_depth = positive_integer(self.maximum_depth, "maximum_depth")
        known = set(candidate_ids)
        for label, group in (
            ("root_candidate_ids", roots),
            ("accepted_candidate_ids", accepted),
            ("rejected_candidate_ids", rejected),
            ("unresolved_candidate_ids", unresolved),
        ):
            if not set(group) <= known:
                raise ValueError("{0} contains unknown candidates".format(label))
        grouped = accepted + rejected + unresolved
        if len(set(grouped)) != len(grouped):
            raise ValueError("candidate disposition groups must be disjoint")
        if set(grouped) != known:
            raise ValueError("candidate disposition groups must cover every candidate")
        parents = {}
        adjacency = {candidate_id: [] for candidate_id in candidate_ids}
        for parent, child in edges:
            if parent not in known or child not in known:
                raise ValueError("every edge must reference an existing candidate")
            if child in parents:
                raise ValueError("a candidate may not have more than one parent")
            parents[child] = parent
            adjacency[parent].append(child)
        if any(root in parents for root in roots):
            raise ValueError("root candidates must not have a parent edge")
        calculated_roots = known - set(parents)
        if set(roots) != calculated_roots:
            raise ValueError("root_candidate_ids must identify all tree roots")
        visiting = set()
        visited = set()

        def visit(node: str, depth: int) -> None:
            if node in visiting:
                raise ValueError("root-cause tree must not contain cycles")
            if depth > maximum_depth:
                raise ValueError("root-cause tree exceeds maximum_depth")
            if node in visited:
                return
            visiting.add(node)
            for child in adjacency[node]:
                visit(child, depth + 1)
            visiting.remove(node)
            visited.add(node)

        for root in roots:
            visit(root, 1)
        if visited != known:
            raise ValueError("root-cause tree contains an unreachable cycle")
        object.__setattr__(self, "candidate_ids", candidate_ids)
        object.__setattr__(self, "root_candidate_ids", roots)
        object.__setattr__(self, "accepted_candidate_ids", accepted)
        object.__setattr__(self, "rejected_candidate_ids", rejected)
        object.__setattr__(self, "unresolved_candidate_ids", unresolved)
        object.__setattr__(self, "edges", edges)
        object.__setattr__(self, "maximum_depth", maximum_depth)
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        return plain({
            "tree_id": self.tree_id,
            "tree_version": self.tree_version,
            "candidate_ids": self.candidate_ids,
            "root_candidate_ids": self.root_candidate_ids,
            "accepted_candidate_ids": self.accepted_candidate_ids,
            "rejected_candidate_ids": self.rejected_candidate_ids,
            "unresolved_candidate_ids": self.unresolved_candidate_ids,
            "edges": self.edges,
            "maximum_depth": self.maximum_depth,
            "metadata": self.metadata,
        })

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RootCauseTree":
        return cls(**mapping_payload(value, "RootCauseTree"))


def validate_root_cause_tree(tree: RootCauseTree, candidates: Iterable[Any]) -> None:
    """Validate references and candidate/tree agreement without mutation."""

    if not isinstance(tree, RootCauseTree):
        raise TypeError("tree must be a RootCauseTree")
    candidates_tuple = tuple(candidates)
    candidate_by_id = {}
    for candidate in candidates_tuple:
        candidate_id = getattr(candidate, "candidate_id", None)
        if not isinstance(candidate_id, str):
            raise TypeError("candidates must be RootCauseCandidate-like objects")
        if candidate_id in candidate_by_id:
            raise ValueError("duplicate candidate ID")
        candidate_by_id[candidate_id] = candidate
    if set(candidate_by_id) != set(tree.candidate_ids):
        raise ValueError("tree candidate IDs must exactly match supplied candidates")
    edge_set = set(tree.edges)
    accepted_dispositions = {
        RootCauseDisposition.ACCEPTED,
        RootCauseDisposition.PARTIALLY_SUPPORTED,
    }
    expected_accepted = set()
    expected_rejected = set()
    expected_unresolved = set()
    for candidate_id, candidate in candidate_by_id.items():
        parent = getattr(candidate, "parent_candidate_id")
        children = tuple(getattr(candidate, "child_candidate_ids"))
        alternatives = tuple(getattr(candidate, "alternative_candidate_ids"))
        supporting = tuple(getattr(candidate, "supporting_evidence_refs"))
        contradicting = tuple(getattr(candidate, "contradicting_evidence_refs"))
        for reference in children + alternatives:
            if reference not in candidate_by_id:
                raise ValueError("candidate reference does not resolve")
        if parent is not None and parent not in candidate_by_id:
            raise ValueError("candidate parent does not resolve")
        if parent is None:
            if candidate_id not in tree.root_candidate_ids:
                raise ValueError("candidate parent reference disagrees with roots")
        elif (parent, candidate_id) not in edge_set:
            raise ValueError("candidate parent reference disagrees with edges")
        if {(candidate_id, child) for child in children} != {
            edge for edge in edge_set if edge[0] == candidate_id
        }:
            raise ValueError("candidate child references disagree with edges")
        if set(supporting) & set(contradicting):
            raise ValueError("supporting and contradicting evidence must be disjoint")
        disposition = getattr(candidate, "disposition")
        if disposition in accepted_dispositions:
            expected_accepted.add(candidate_id)
        elif disposition == RootCauseDisposition.REJECTED:
            expected_rejected.add(candidate_id)
        elif disposition == RootCauseDisposition.UNRESOLVED:
            expected_unresolved.add(candidate_id)
        else:
            raise ValueError("invalid candidate disposition")
    if expected_accepted != set(tree.accepted_candidate_ids):
        raise ValueError("accepted candidate group does not match dispositions")
    if expected_rejected != set(tree.rejected_candidate_ids):
        raise ValueError("rejected candidate group does not match dispositions")
    if expected_unresolved != set(tree.unresolved_candidate_ids):
        raise ValueError("unresolved candidate group does not match dispositions")


__all__ = ["RootCauseTree", "validate_root_cause_tree"]
