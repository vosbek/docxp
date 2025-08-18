#!/usr/bin/env python3
"""
DocXP Audit Helper Script

Simple utility to assist with audit log entries and GPT-5 review request creation.
Usage:
    python audit-helper.py log-change "Added podman-compose.yml" "infrastructure setup"
    python audit-helper.py create-review "session2" "Infrastructure implementation complete"
"""

import os
import sys
import datetime
from typing import List, Optional

def get_current_date():
    """Get current date in YYYY-MM-DD format"""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def append_to_audit_log(change_type: str, description: str, impact: Optional[str] = None):
    """Append a quick change entry to AUDIT.md"""
    timestamp = datetime.datetime.now().strftime("%H:%M")
    
    entry = f"\n### {timestamp} - {change_type}\n"
    entry += f"- {description}\n"
    if impact:
        entry += f"- Impact: {impact}\n"
    
    # Find the current session in AUDIT.md and append
    with open("AUDIT.md", "r") as f:
        content = f.read()
    
    # Simple append to end of file for now
    with open("AUDIT.md", "a") as f:
        f.write(entry)
    
    print(f"[OK] Added audit entry: {change_type} - {description}")

def create_review_request_template(session_name: str, summary: str):
    """Create a new GPT-5 review request template"""
    date = get_current_date()
    filename = f"GPT5_REVIEW_REQUESTS/review-{date}-{session_name}.md"
    
    template = f"""# GPT-5 Review Request - {session_name.title()}: {summary}

## Summary of Changes
[Brief overview of what was implemented in this session]

## Key Technical Decisions
1. **Decision Name**: Choice made and rationale
   - **Alternative Considered**: What else was evaluated
   - **Impact**: Expected effect on performance/architecture

## Implementation Details

### Files Modified
- **file1.py**: Description of changes made
- **file2.yml**: Configuration modifications

### New Components
- **Component Name**: Purpose and integration points

### Configuration Changes
- **Service Settings**: Infrastructure modifications made

## Performance Metrics
- **Search Latency**: p50/p95 measurements (target: p50 < 700ms, p95 < 1.2s)
- **Memory Usage**: Container resource consumption
- **Throughput**: Request processing rates
- **Bedrock Costs**: Token usage and $ per operation

## Questions for GPT-5
1. **Architecture Validation**: Are the implementation choices sound?
2. **Performance Concerns**: Any red flags in the metrics?
3. **Best Practices**: Suggestions for improvement?
4. **Risk Assessment**: Potential issues to watch for?

## Next Steps Planned
- [What will be implemented in the next session]

## Code Snippets (if needed)
```python
# Key implementation details for review
```

## Request Priority
- [ ] Architecture review
- [ ] Performance validation  
- [ ] Security assessment
- [ ] Best practices check
"""
    
    with open(filename, "w") as f:
        f.write(template)
    
    print(f"[OK] Created review request template: {filename}")
    print("[INFO] Edit the file to add specific details before sending to GPT-5")

def show_current_session_status():
    """Show current audit log status"""
    if not os.path.exists("AUDIT.md"):
        print("[ERROR] AUDIT.md not found. Run from project root directory.")
        return
    
    with open("AUDIT.md", "r") as f:
        content = f.read()
    
    # Count sessions
    session_count = content.count("## [")
    
    # Find latest session
    lines = content.split('\n')
    latest_session = "No sessions found"
    for line in lines:
        if line.startswith("## ["):
            latest_session = line.replace("## [", "").replace("]", "")
            break
    
    print("Audit Log Status:")
    print(f"   Sessions logged: {session_count}")
    print(f"   Latest session: {latest_session}")
    print(f"   File size: {len(content)} characters")

def main():
    if len(sys.argv) < 2:
        print("DocXP Audit Helper")
        print("\nUsage:")
        print("  python audit-helper.py log-change <type> <description> [impact]")
        print("  python audit-helper.py create-review <session-name> <summary>")
        print("  python audit-helper.py status")
        print("\nExamples:")
        print("  python audit-helper.py log-change 'Config Update' 'Added OpenSearch ulimits' 'Improved container health'")
        print("  python audit-helper.py create-review 'session2' 'Infrastructure setup complete'")
        print("  python audit-helper.py status")
        return
    
    command = sys.argv[1]
    
    if command == "log-change":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: log-change <type> <description> [impact]")
            return
        change_type = sys.argv[2]
        description = sys.argv[3]
        impact = sys.argv[4] if len(sys.argv) > 4 else None
        append_to_audit_log(change_type, description, impact)
    
    elif command == "create-review":
        if len(sys.argv) < 4:
            print("[ERROR] Usage: create-review <session-name> <summary>")
            return
        session_name = sys.argv[2]
        summary = sys.argv[3]
        create_review_request_template(session_name, summary)
    
    elif command == "status":
        show_current_session_status()
    
    else:
        print(f"[ERROR] Unknown command: {command}")
        print("Available commands: log-change, create-review, status")

if __name__ == "__main__":
    main()