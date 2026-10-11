# Agent Architecture & Tool Suite

## Agent Engine
CodePilot AI uses an autonomous agent engine built on a controlled tool calling loop (`AgentEngine`).

### Safety Policies
1. **Loop Guard**: Maximum 5 tool execution steps per user interaction.
2. **Timeout Guard**: 30-second hard execution limit per step.
3. **Write Protection**: The agent can only issue **read** operations and propose diff patches. No automatic code modification or execution on the host machine is permitted.

### Registered Tools
- `search_repository(query, language)`: Performs hybrid vector + keyword search.
- `get_file(file_path, start_line, end_line)`: Fetches file content with line ranges.
- `get_symbol(symbol_name)`: Looks up function/class definition across indexed AST.
- `get_related_files(file_path)`: Uses import/call graph to retrieve related files.
- `find_callers(symbol_name)`: Lists all functions/files calling a specific symbol.
- `get_git_diff(commit_a, commit_b)`: Compares repository changes.
- `run_static_analysis(file_path)`: Checks code smells, security risks, and type issues.
