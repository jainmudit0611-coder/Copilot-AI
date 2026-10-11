import re
from typing import List, Dict, Any

class GraphBuilder:
    @staticmethod
    def extract_relationships(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        relationships = []
        path_to_file = {f["path"]: f for f in files}

        for file in files:
            content = file["content"]
            source_path = file["path"]
            language = file["language"]

            if language in ("TypeScript", "JavaScript"):
                # Matches import statements: import ... from './services/orderService'
                matches = re.findall(r'from\s+[\'"]([^\'"]+)[\'"]', content)
                for imported in matches:
                    relationships.append({
                        "source_file_path": source_path,
                        "source_symbol": "import",
                        "target_symbol": imported,
                        "relationship_type": "IMPORTS"
                    })

            elif language == "Python":
                # Matches import statements: from backend.routes import order_routes
                matches = re.findall(r'from\s+([a-zA-Z0-9_\.]+)\s+import', content)
                for imported in matches:
                    relationships.append({
                        "source_file_path": source_path,
                        "source_symbol": "import",
                        "target_symbol": imported,
                        "relationship_type": "IMPORTS"
                    })

        return relationships
