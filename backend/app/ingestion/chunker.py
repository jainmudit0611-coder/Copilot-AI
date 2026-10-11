from typing import List, Dict, Any
from app.ingestion.parser import CodeParser

class IntelligentChunker:
    @staticmethod
    def chunk_file(file_path: str, language: str, content: str, max_chunk_lines: int = 50) -> List[Dict[str, Any]]:
        chunks = []
        lines = content.splitlines()
        symbols = CodeParser.extract_symbols(content, language)

        if symbols:
            # Code-aware symbol chunking
            for sym in symbols:
                start = sym["start_line"]
                end = sym["end_line"]
                chunk_lines = lines[start - 1:end]
                chunk_content = "\n".join(chunk_lines)

                chunks.append({
                    "file_path": file_path,
                    "language": language,
                    "start_line": start,
                    "end_line": end,
                    "symbol_name": sym["name"],
                    "symbol_type": sym["symbol_type"],
                    "content": chunk_content
                })
        else:
            # Fallback line-based sliding window chunking
            total_lines = len(lines)
            if total_lines == 0:
                return []

            step = max(1, max_chunk_lines // 2)
            for start in range(1, total_lines + 1, step):
                end = min(total_lines, start + max_chunk_lines - 1)
                chunk_lines = lines[start - 1:end]
                chunk_content = "\n".join(chunk_lines)

                chunks.append({
                    "file_path": file_path,
                    "language": language,
                    "start_line": start,
                    "end_line": end,
                    "symbol_name": None,
                    "symbol_type": None,
                    "content": chunk_content
                })
                if end == total_lines:
                    break

        return chunks
