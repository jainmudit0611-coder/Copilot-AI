from typing import Dict, Any

class GitTools:
    @staticmethod
    def parse_git_diff(diff_text: str) -> Dict[str, Any]:
        changed_files = []
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                changed_files.append(line.replace("+++ b/", ""))
        return {
            "changed_files_count": len(changed_files),
            "files": changed_files
        }
