#!/usr/bin/env python
"""
Quick syntax/import validation script for Phase 1 refactor.
Run this to verify the module structure is sound before starting the server.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def validate_imports():
    """Check that all modules import successfully."""
    print("Validating module imports...")
    
    try:
        from app.core.config import (
            BASE_DIR, ENV_PATH, WORKSPACE_DIR, FRONTEND_DIR, 
            AZURE_OPENAI_MODEL, AUDIT_LOG_DIR
        )
        print("✓ app.core.config")
        
        from app.core.azure_client import get_client, call_azure_ai
        print("✓ app.core.azure_client")
        
        from app.runtime.parser import extract_json
        print("✓ app.runtime.parser")
        
        from app.runtime.planner import create_plan, answer_directly, summarize_tool_result
        print("✓ app.runtime.planner")
        
        from app.tools.file_tools import safe_path, list_files, read_file, write_note, execute_tool
        print("✓ app.tools.file_tools")
        
        from app.runtime.agent_runtime import run_agent
        print("✓ app.runtime.agent_runtime")
        
        from app.routes.utils import get_chat_page, get_health, get_env_debug, get_frontend_debug
        print("✓ app.routes.utils")
        
        from app.routes.frontend_routes import router as frontend_router
        print("✓ app.routes.frontend_routes")
        
        from app.routes.chat_routes import router as chat_router
        print("✓ app.routes.chat_routes")
        
        from app.main import app
        print("✓ app.main")
        
        print("\n✅ All imports successful!")
        print(f"\nProject structure:")
        print(f"  BASE_DIR: {BASE_DIR}")
        print(f"  ENV_PATH: {ENV_PATH}")
        print(f"  WORKSPACE_DIR: {WORKSPACE_DIR}")
        print(f"  FRONTEND_DIR: {FRONTEND_DIR}")
        print(f"  AUDIT_LOG_DIR: {AUDIT_LOG_DIR}")
        print(f"\nModel: {AZURE_OPENAI_MODEL}")
        print(f"Directories exist:")
        print(f"  WORKSPACE_DIR: {WORKSPACE_DIR.exists()}")
        print(f"  FRONTEND_DIR: {FRONTEND_DIR.exists()}")
        print(f"  AUDIT_LOG_DIR: {AUDIT_LOG_DIR.exists()}")
        print(f"\nFastAPI app routes: {len(app.routes)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_imports()
    sys.exit(0 if success else 1)
