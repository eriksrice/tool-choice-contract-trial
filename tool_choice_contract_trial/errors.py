"""Named errors for the Milestone 1 invalidity boundary."""

from __future__ import annotations


class SchemaInvalidError(ValueError):
    """An artifact is structurally invalid and cannot enter evaluation."""


class SchemaDriftError(ValueError):
    """Generated schema bytes do not match the checked-in projections."""


class ArtifactIntegrityError(ValueError):
    """Typed artifacts cannot be linked into one unambiguous evaluation run."""
