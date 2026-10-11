from typing import Dict, Any, List

class CodeTools:
    @staticmethod
    def run_static_analysis(file_path: str, content: str) -> Dict[str, Any]:
        issues = []
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            if "TODO" in line or "FIXME" in line:
                issues.append({"line": i, "severity": "LOW", "type": "Maintainability", "message": "Unresolved TODO comment"})
            if "secret" in line.lower() or "password" in line.lower() and "=" in line:
                if not line.strip().startswith("//") and not line.strip().startswith("#"):
                    issues.append({"line": i, "severity": "HIGH", "type": "Security", "message": "Potential hardcoded credentials"})
            if "time.sleep" in line and "async" in content:
                issues.append({"line": i, "severity": "MEDIUM", "type": "Performance", "message": "Blocking sleep inside async module"})

        return {
            "file_path": file_path,
            "issues_found": len(issues),
            "issues": issues
        }
