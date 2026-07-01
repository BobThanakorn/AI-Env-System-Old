#!/usr/bin/env python
"""
Test script for the new create_file feature.
Run: python test_create_file.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.tools.file_tools import create_file, list_files
from app.core.config import WORKSPACE_DIR

def test_create_file():
    """Test the create_file function."""
    
    print("=" * 50)
    print("Testing create_file Feature")
    print("=" * 50)
    
    # Test 1: Create a simple file
    print("\n✓ Test 1: Create simple file")
    result1 = create_file("test.txt", "Hello World")
    print(f"  Result: {result1}")
    assert result1["status"] == "success"
    assert result1["created_file"] == "test.txt"
    print("  ✓ Passed")
    
    # Test 2: Try to create existing file (should fail)
    print("\n✓ Test 2: Try to create existing file (should fail)")
    result2 = create_file("test.txt", "Another content")
    print(f"  Result: {result2}")
    assert "error" in result2
    assert "already exists" in result2["error"]
    print("  ✓ Passed - correctly blocked existing file")
    
    # Test 3: Create file with Thai content
    print("\n✓ Test 3: Create file with Thai content")
    result3 = create_file("thai_file.txt", "สวัสดีครับ นี่คือไฟล์ทดสอบ")
    print(f"  Result: {result3}")
    assert result3["status"] == "success"
    print("  ✓ Passed")
    
    # Test 4: Create file in subdirectory
    print("\n✓ Test 4: Create file in subdirectory")
    result4 = create_file("documents/report.txt", "This is a report")
    print(f"  Result: {result4}")
    assert result4["status"] == "success"
    assert result4["created_file"] == "documents/report.txt"
    print("  ✓ Passed - subdirectory auto-created")
    
    # Test 5: Missing path
    print("\n✓ Test 5: Missing path (should fail)")
    result5 = create_file("", "Content")
    print(f"  Result: {result5}")
    assert "error" in result5
    print("  ✓ Passed - correctly rejected empty path")
    
    # Test 6: Missing content
    print("\n✓ Test 6: Missing content (should fail)")
    result6 = create_file("empty.txt", "")
    print(f"  Result: {result6}")
    assert "error" in result6
    print("  ✓ Passed - correctly rejected empty content")
    
    # Test 7: List files to verify creation
    print("\n✓ Test 7: List files to verify creation")
    result7 = list_files()
    files = result7["files"]
    print(f"  Total files: {len(files)}")
    print(f"  Created files found:")
    for f in files:
        if "test" in f or "thai" in f or "report" in f:
            print(f"    - {f}")
    assert any("test.txt" in f for f in files)
    assert any("thai_file.txt" in f for f in files)
    assert any("report.txt" in f for f in files)
    print("  ✓ Passed - all created files found")
    
    # Test 8: Verify actual file content
    print("\n✓ Test 8: Verify actual file content")
    test_file = WORKSPACE_DIR / "test.txt"
    content = test_file.read_text(encoding="utf-8")
    print(f"  Content: {content}")
    assert content == "Hello World"
    print("  ✓ Passed - content is correct")
    
    print("\n" + "=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)
    
    print("\n📝 Summary:")
    print("  - create_file() function works correctly")
    print("  - Blocks existing files")
    print("  - Supports Thai characters")
    print("  - Auto-creates subdirectories")
    print("  - Files are stored in workspace/")
    
    print("\n💡 Next steps:")
    print("  - Run: python main.py")
    print("  - Open: http://localhost:8000/chat")
    print("  - Click: 'Create File' button in sidebar")
    print("  - Or type: 'สร้างไฟล์ชื่อ myfile.txt ด้วยเนื้อหา hello'")

if __name__ == "__main__":
    try:
        test_create_file()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
