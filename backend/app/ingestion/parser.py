import re
from typing import List, Dict, Any

class CodeParser:
    @staticmethod
    def extract_symbols(content: str, language: str) -> List[Dict[str, Any]]:
        symbols = []
        lines = content.splitlines()

        if language == "Python":
            # Python def function / class extraction
            for i, line in enumerate(lines, 1):
                match_func = re.match(r'^\s*(async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(', line)
                if match_func:
                    symbols.append({
                        "name": match_func.group(2),
                        "symbol_type": "function",
                        "start_line": i,
                        "signature": line.strip()
                    })
                match_class = re.match(r'^\s*class\s+([a-zA-Z0-9_]+)', line)
                if match_class:
                    symbols.append({
                        "name": match_class.group(1),
                        "symbol_type": "class",
                        "start_line": i,
                        "signature": line.strip()
                    })

        elif language in ("TypeScript", "JavaScript"):
            # TS/JS function, class, export, interface extraction
            for i, line in enumerate(lines, 1):
                match_func = re.search(r'(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)', line)
                if match_func:
                    symbols.append({
                        "name": match_func.group(1),
                        "symbol_type": "function",
                        "start_line": i,
                        "signature": line.strip()
                    })
                match_class = re.search(r'(?:export\s+)?class\s+([a-zA-Z0-9_]+)', line)
                if match_class:
                    symbols.append({
                        "name": match_class.group(1),
                        "symbol_type": "class",
                        "start_line": i,
                        "signature": line.strip()
                    })
                match_const = re.search(r'(?:export\s+)?const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(', line)
                if match_const:
                    symbols.append({
                        "name": match_const.group(1),
                        "symbol_type": "function",
                        "start_line": i,
                        "signature": line.strip()
                    })

        # Calculate approximate end lines
        for idx, sym in enumerate(symbols):
            if idx < len(symbols) - 1:
                sym["end_line"] = max(sym["start_line"], symbols[idx + 1]["start_line"] - 1)
            else:
                sym["end_line"] = max(sym["start_line"], len(lines))

        return symbols
