"""

import pytest
import json
import uuid
import os
from unittest.mock import Mock, AsyncMock, patch, PropertyMock, MagicMock
import azure.functions as func
from datetime import datetime, timezone
import pytest
import json
import uuid
import os
from unittest.mock import Mock, AsyncMock, patch, PropertyMock, MagicMock
import azure.functions as func
from datetime import datetime, timezone
from api.prompts import (
from ..shared.models import (
from ..shared.error_handling import ValidationException, BusinessLogicException

Comprehensive test file for Prompts API.

"""
