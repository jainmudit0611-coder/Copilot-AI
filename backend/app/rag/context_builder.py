from typing import List, Dict, Any

class ContextBuilder:
    @staticmethod
    def assemble_context(chunks: List[Dict[str, Any]], max_chars: int = 12000) -> str:
        formatted_blocks = []
        current_chars = 0

        for chunk in chunks:
            block = f"--- FILE: {chunk['file_path']} (Lines {chunk['start_line']}-{chunk['end_line']}) ---\n"
            if chunk.get("symbol_name"):
                block += f"// Symbol: {chunk['symbol_type']} {chunk['symbol_name']}\n"
            block += chunk["content"] + "\n\n"

            if current_chars + len(block) > max_chars:
                break

            formatted_blocks.append(block)
            current_chars += len(block)

        return "".join(formatted_blocks)
