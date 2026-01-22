"""临时脚本：检查协议遵循情况"""
import sys
from pathlib import Path
import yaml

sys.path.insert(0, 'src')
from vibecollab.protocol_checker import ProtocolChecker

# 加载配置
with open('project.yaml', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 执行检查
checker = ProtocolChecker(Path('.'), config)
results = checker.check_all()
summary = checker.get_summary(results)

# 显示结果
print("=" * 60)
print("Protocol Compliance Check")
print("=" * 60)
print(f"\nTotal: {summary['total']} checks")
print(f"[PASS] Passed: {summary['passed']}")
print(f"[ERROR] Errors: {summary['errors']}")
print(f"[WARN] Warnings: {summary['warnings']}")
print(f"[INFO] Infos: {summary['infos']}")
print(f"\nAll passed: {'Yes' if summary['all_passed'] else 'No'}")

print("\n" + "=" * 60)
print("Detailed Results:")
print("=" * 60)

for result in results:
    icon = "[ERROR]" if result.severity == "error" else "[WARN]" if result.severity == "warning" else "[INFO]"
    status = "PASS" if result.passed else "FAIL"
    print(f"\n{icon} {result.name}")
    print(f"   Status: {status}")
    print(f"   Message: {result.message}")
    if result.suggestion:
        print(f"   Suggestion: {result.suggestion}")
