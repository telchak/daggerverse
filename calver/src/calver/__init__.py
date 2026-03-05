"""Calendar Versioning (CalVer) utilities for generating date-based version strings in Dagger pipelines.

Supports configurable date formats (YYYY.MM.DD, v.YYYY.MM.MICRO, etc.), automatic micro version
incrementing from git tags, and optional tag pushing to remote repositories.
"""

from .main import Calver as Calver
