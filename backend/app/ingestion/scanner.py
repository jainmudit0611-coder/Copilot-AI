import os
import hashlib
from typing import List, Dict, Any

IGNORED_DIRS = {
    'node_modules', '.git', 'dist', 'build', 'coverage', '.next', '__pycache__',
    '.venv', 'venv', 'bin', 'obj', '.idea', '.vscode', '.gradle'
}

IGNORED_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf',
    '.eot', '.mp4', '.webm', '.pdf', '.zip', '.tar', '.gz', '.7z', '.exe', '.dll',
    '.so', '.dylib', '.pyc', '.pyo', '.lock'
}

LANGUAGE_MAP = {
    '.ts': 'TypeScript', '.tsx': 'TypeScript', '.js': 'JavaScript', '.jsx': 'JavaScript',
    '.py': 'Python', '.java': 'Java', '.go': 'Go', '.cs': 'C#',
    '.sql': 'SQL', '.json': 'JSON', '.yaml': 'YAML', '.yml': 'YAML',
    '.md': 'Markdown', '.html': 'HTML', '.css': 'CSS'
}

class RepositoryScanner:
    @staticmethod
    def scan_directory(root_dir: str) -> List[Dict[str, Any]]:
        scanned_files = []

        for root, dirs, files in os.walk(root_dir):
            # Exclude ignored directories in place
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IGNORED_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir).replace('\\', '/')

                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    file_hash = hashlib.sha256(content.encode()).hexdigest()
                    size_bytes = os.path.getsize(full_path)
                    language = LANGUAGE_MAP.get(ext, 'Text')

                    scanned_files.append({
                        "path": rel_path,
                        "language": language,
                        "size_bytes": size_bytes,
                        "file_hash": file_hash,
                        "content": content
                    })
                except Exception:
                    continue

        return scanned_files
