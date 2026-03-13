#!/usr/bin/env python3
"""
Execute the cron job instructions automatically.
This is what the agent (me) should run when triggered by the cron job.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return output."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=300)
        print(f"Output: {result.stdout[:500]}...")
        if result.stderr:
            print(f"Errors: {result.stderr[:500]}...")
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False, "", "Timeout"
    except Exception as e:
        print(f"Command failed: {e}")
        return False, "", str(e)

def main():
    print("=== EXECUTING CRON JOB INSTRUCTIONS ===")
    
    # Change to workspace directory
    workspace = Path("/home/node/.openclaw/workspaces/ops/disability-ai-collective")
    os.chdir(workspace)
    
    # Step 1: Run orchestrator to get metadata
    print("\n--- Step 1: Getting article metadata ---")
    success, output, error = run_command("python3 automation/cron_article_orchestrator_with_discovery.py")
    
    if not success:
        print(f"Failed to get metadata: {error}")
        return
    
    # Parse JSON output
    try:
        # Find JSON in output
        json_start = output.find('{')
        json_end = output.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            print("No JSON found in output")
            return
            
        json_str = output[json_start:json_end]
        data = json.loads(json_str)
        
        if data.get('status') != 'success':
            print(f"Orchestrator failed: {data.get('message', 'Unknown error')}")
            return
            
        print(f"Title: {data['metadata']['title']}")
        print(f"Author: {data['metadata']['author']}")
        
        # Save metadata for later use
        with open('temp_metadata.json', 'w') as f:
            json.dump(data, f, indent=2)
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Output was: {output[:500]}...")
        return
    
    print("\n=== Cron job execution would continue with:")
    print("1. LLM content generation (requires agent API access)")
    print("2. Image generation")
    print("3. Article file creation")
    print("4. Git commit and push")
    print("\nSince I AM the agent, I should execute these steps directly.")
    
    # The rest would be executed by me (the agent) manually
    # For true automation, we need the full_automation_orchestrator.py to work
    
    print("\nFor true automation, we need to:")
    print("1. Fix full_automation_orchestrator.py to handle LLM API calls")
    print("2. Update cron job to run that script directly")
    print("3. Remove the agent from the loop")

if __name__ == "__main__":
    main()