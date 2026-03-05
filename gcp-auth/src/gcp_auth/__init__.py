"""GCP authentication utilities for Dagger pipelines using service accounts and OIDC.

Provides container authentication via service account JSON keys, OIDC/Workload Identity Federation,
Application Default Credentials (ADC), and access token generation for Google Cloud services.
"""

from .main import GcpAuth as GcpAuth
