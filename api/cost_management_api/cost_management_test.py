"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import azure.functions as func
from shared.budget import BudgetConfig
from shared.error_handling import SutraAPIError
from ..conftest import create_auth_request
from . import main as cost_management_main
from api.shared.budget import BudgetManager
from api.shared.models import LLMProvider, User, UserRole

Tests for cost_management_api - Budget and cost tracking endpoints
"""
