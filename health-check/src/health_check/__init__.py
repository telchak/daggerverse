"""Simple, reusable container health checking for Dagger.

This module provides health checking utilities for containers using Dagger's
service binding features. Supports HTTP, TCP, and custom exec-based health checks.
"""

from .main import HealthCheck as HealthCheck
