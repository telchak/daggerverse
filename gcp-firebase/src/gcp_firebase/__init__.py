"""GCP Firebase - Dagger module for Firebase Hosting and Firestore management.

This module provides utilities for:
- Firebase Hosting: Build and deploy web applications, preview channels
- Firestore: Create, update, delete, and manage Firestore databases
"""

from .firestore import Firestore as Firestore
from .main import GcpFirebase as GcpFirebase
