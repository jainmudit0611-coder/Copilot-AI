import os

class PathGuard:
    @staticmethod
    def validate_safe_path(base_dir: str, target_path: str) -> str:
        abs_base = os.path.abspath(base_dir)
        abs_target = os.path.abspath(os.path.join(base_dir, target_path))

        if not abs_target.startswith(abs_base):
            raise ValueError(f"Path traversal attack detected: '{target_path}'")
        return abs_target
