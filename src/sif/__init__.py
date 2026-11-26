"""SIF: relational verifier for SIF=(STATE, INTENT, TRANSFORMATION, CONSEQUENCE)."""

from sif.verifier import Invalid, Unknown, verify

__version__ = "0.2.0"
__all__ = ["verify", "Unknown", "Invalid", "__version__"]
