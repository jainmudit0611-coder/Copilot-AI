import os
import zipfile
import tempfile
import httpx
from typing import Optional

class RepositoryDownloader:
    @staticmethod
    async def download_github_zip(repo_url: str, token: Optional[str] = None) -> str:
        # Converts https://github.com/owner/repo -> https://api.github.com/repos/owner/repo/zipball/main
        parts = repo_url.rstrip('/').split('/')
        if len(parts) < 2:
            raise ValueError("Invalid GitHub repository URL")
        owner, repo = parts[-2], parts[-1]

        download_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/main"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        temp_dir = tempfile.mkdtemp(prefix="codepilot_repo_")
        zip_path = os.path.join(temp_dir, "repo.zip")

        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            resp = await client.get(download_url, headers=headers)
            resp.raise_for_status()
            with open(zip_path, "wb") as f:
                f.write(resp.content)

        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Check for zip traversal vulnerabilities
            for member in zip_ref.namelist():
                if member.startswith("/") or ".." in member:
                    raise ValueError(f"Malicious zip entry detected: {member}")
            zip_ref.extractall(extract_dir)

        # Return the unzipped root directory
        extracted_contents = os.listdir(extract_dir)
        if len(extracted_contents) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_contents[0])):
            return os.path.join(extract_dir, extracted_contents[0])
        return extract_dir
