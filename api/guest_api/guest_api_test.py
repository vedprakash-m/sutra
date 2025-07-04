"""

import json
import sys
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import azure.functions as func
from ..conftest import create_auth_request
from guest_api import main as guest_api_main

Tests for Guest API - Fixed version with proper mocking
"""
