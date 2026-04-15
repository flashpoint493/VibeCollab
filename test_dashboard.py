#!/usr/bin/env python3
"""
Test script for VibeCollab Dashboard functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_snapshot_generation():
    """Test workflow snapshot generation."""
    try:
        # Use absolute import
        from vibecollab_dashboard.workflow_snapshot import WorkflowSnapshotGenerator
        
        generator = WorkflowSnapshotGenerator(Path("."))
        snapshot = generator.generate_snapshot()
        
        print("✅ Snapshot generation successful")
        print(f"   Generated at: {snapshot.generated_at}")
        if snapshot.project:
            print(f"   Project: {snapshot.project.name}")
        
        return True
    except Exception as e:
        print(f"❌ Snapshot generation failed: {e}")
        return False

def test_validation():
    """Test workflow validation."""
    try:
        # Use absolute import
        from vibecollab_dashboard.workflow_validator import validate_workflow
        
        result = validate_workflow(Path("."))
        
        print("✅ Validation successful")
        print(f"   Status: {result.status}")
        print(f"   Issues: {result.total_issues}")
        
        return True
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def test_cli_commands():
    """Test CLI command registration."""
    try:
        from vibecollab.cli.main import main
        import click.testing
        
        runner = click.testing.CliRunner()
        
        # Test workflow --help
        result = runner.invoke(main, ["workflow", "--help"])
        if result.exit_code == 0 and "Workflow Dashboard" in result.output:
            print("✅ CLI command registration successful")
            return True
        else:
            print(f"❌ CLI command test failed: {result.output}")
            return False
            
    except Exception as e:
        print(f"❌ CLI command test failed: {e}")
        return False

def test_role_requests_panel():
    """Test role requests panel display."""
    try:
        from src.vibecollab_dashboard.workflow_panel import WorkflowPanel
        from pathlib import Path
        import sys

        # 添加当前目录到Python路径
        sys.path.insert(0, '.')

        # 创建dashboard面板
        panel = WorkflowPanel(Path('.'))
        layout = panel.render_panel()

        # 获取角色请求部分的内容
        role_requests_panel = layout['role_requests'].renderable
        print('=== Role Requests Panel Content ===')
        print(role_requests_panel)

        # 打印面板的文本表示
        print('\n=== Panel Text Representation ===')
        print(str(role_requests_panel))
        
        return True
    except Exception as e:
        print(f"❌ Role requests panel test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing VibeCollab Dashboard Implementation")
    print("=" * 50)
    
    tests = [
        ("Snapshot Generation", test_snapshot_generation),
        ("Workflow Validation", test_validation),
        ("CLI Commands", test_cli_commands),
        ("Role Requests Panel", test_role_requests_panel),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✨ All tests passed! Dashboard implementation is ready.")
        print("\nAvailable commands:")
        print("  vibecollab workflow panel")
        print("  vibecollab workflow panel --watch")
        print("  vibecollab workflow validate")
        print("  vibecollab workflow snapshot")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()