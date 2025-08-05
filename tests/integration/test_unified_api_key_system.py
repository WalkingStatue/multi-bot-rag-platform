"""
Test script for the unified API key management system.

This script tests the complete API key resolution, fallback, and error handling system.
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any
import uuid
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.unified_api_key_manager import UnifiedAPIKeyManager, APIKeySource
from app.services.enhanced_api_key_service import EnhancedAPIKeyServic