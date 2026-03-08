#!/usr/bin/env python3
"""
Daily Automation Script for Disability-AI Collective
Runs morning research and evening development cycles
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import subprocess

def run_morning_research():
    """Run morning research cycle"""
    print("🌅 Starting morning research cycle...")
    
    # Run the test research bot
    script_path = Path(__file__).parent / "test_research_bot.py"
    result = subprocess.run([sys.executable, str(script_path)], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Morning research cycle completed successfully")
        return True
    else:
        print(f"❌ Morning research cycle failed: {result.stderr}")
        return False

def run_evening_development():
    """Run evening development cycle"""
    print("🌙 Starting evening development cycle...")
    
    # Run accessibility audit
    script_path = Path(__file__).parent.parent / "accessibility" / "simple_check.py"
    result = subprocess.run([sys.executable, str(script_path)], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Accessibility audit completed successfully")
        
        # Additional evening tasks could go here:
        # - Generate weekly summary
        # - Update website statistics
        # - Send notifications
        
        return True
    else:
        print(f"❌ Evening development cycle failed: {result.stderr}")
        return False

def git_commit_and_push(cycle_type):
    """Commit and push changes to git"""
    try:
        repo_root = Path(__file__).parent.parent
        
        # Add all changes
        subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
        
        # Generate commit message
        today = datetime.now().strftime('%Y-%m-%d')
        commit_message = f"Automated {cycle_type} cycle {today}: Disability-AI research updates"
        
        # Commit
        subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_root, check=True)
        
        print(f"✅ Git commit successful: {commit_message}")
        
        # Note: Push would be enabled when remote repository is configured
        # subprocess.run(["git", "push"], cwd=repo_root, check=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False

def main():
    """Main automation script"""
    if len(sys.argv) < 2:
        print("Usage: daily_automation.py [morning|evening|full]")
        sys.exit(1)
    
    cycle_type = sys.argv[1]
    success = True
    
    if cycle_type == "morning":
        success = run_morning_research()
        if success:
            git_commit_and_push("morning")
    
    elif cycle_type == "evening":
        success = run_evening_development()
        if success:
            git_commit_and_push("evening")
    
    elif cycle_type == "full":
        success = run_morning_research()
        if success:
            git_commit_and_push("morning")
            # Wait a bit before evening cycle
            import time
            time.sleep(2)
            success = run_evening_development()
            if success:
                git_commit_and_push("evening")
    
    else:
        print(f"Unknown cycle type: {cycle_type}")
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()