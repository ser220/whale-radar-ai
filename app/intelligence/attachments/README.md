# Reality Gap Analysis Attachment contract

This package defines immutable reference records and
`RealityGapAnalysisAttachment`. The attachment stores only the relationship
among one Analysis revision, one exact Classification snapshot, and one exact
MetricSet snapshot.

Snapshot references use canonical `sha256:<64 lowercase hex>` tokens. This
package validates their syntax but does not calculate or resolve digests. A
future separately reviewed Integration Service must verify that each digest
matches an existing artifact and that all artifacts share an approved
historical boundary.

The package contains no integration service, classification, metrics, evidence,
tree, Assembly, persistence, learning, provider, Telegram, or production logic.
It depends only on the Python standard library.
