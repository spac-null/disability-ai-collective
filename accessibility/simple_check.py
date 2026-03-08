#!/usr/bin/env python3
"""
Simple Accessibility Checker - No Dependencies
Basic WCAG compliance checking for Disability-AI Collective
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
import re

class SimpleAccessibilityChecker:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.accessibility_dir = self.repo_root / "accessibility"
        self.accessibility_dir.mkdir(exist_ok=True)
    
    def run_basic_audit(self):
        """Run basic accessibility audit"""
        print("♿ Starting basic accessibility audit...")
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wcag_version": "2.1 AA",
            "tests": {}
        }
        
        # Test HTML structure
        results["tests"]["html_structure"] = self.test_html_structure()
        
        # Test content accessibility
        results["tests"]["content_accessibility"] = self.test_content_accessibility()
        
        # Generate report
        self.generate_basic_report(results)
        
        print("✅ Basic accessibility audit complete")
        return results
    
    def test_html_structure(self):
        """Test basic HTML structure"""
        results = {"passed": True, "issues": []}
        
        # Check index.html
        index_file = self.repo_root / "index.html"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for main landmark
            if '<main' not in content and 'role="main"' not in content:
                results["passed"] = False
                results["issues"].append("index.html missing main landmark")
            
            # Check for skip links
            if 'skip-link' not in content and 'Skip to' not in content:
                results["issues"].append("index.html missing skip links (warning)")
            
            # Check for proper heading structure
            headings = re.findall(r'<h([1-6])[^>]*>', content)
            if headings:
                if headings[0] != '1':
                    results["issues"].append("index.html doesn't start with h1 heading")
        
        return results
    
    def test_content_accessibility(self):
        """Test content for basic accessibility issues"""
        results = {"passed": True, "issues": []}
        
        # Check all markdown files
        md_files = list(self.repo_root.glob("**/*.md"))
        
        for file_path in md_files:
            if file_path.name.startswith('.'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for images without alt text
                images = re.findall(r'!\[[^\]]*\]\([^)]+\)', content)
                for img in images:
                    alt_text = re.search(r'!\[([^\]]*)\]', img)
                    if not alt_text or not alt_text.group(1).strip():
                        results["passed"] = False
                        results["issues"].append(f"{file_path.name}: Image without alt text")
                
                # Check for non-descriptive links
                links = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
                for link_text, _ in links:
                    if link_text.lower().strip() in ['click here', 'here', 'link']:
                        results["issues"].append(f"{file_path.name}: Non-descriptive link text: '{link_text}'")
            
            except Exception as e:
                results["issues"].append(f"Error reading {file_path.name}: {str(e)}")
        
        return results
    
    def generate_basic_report(self, results):
        """Generate basic accessibility report"""
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_file = self.accessibility_dir / f"basic-accessibility-audit-{report_date}.md"
        
        total_issues = sum(len(test_result.get("issues", [])) for test_result in results["tests"].values())
        critical_issues = sum(1 for test_result in results["tests"].values() if not test_result.get("passed", True))
        
        report_content = f"""# Basic Accessibility Audit Report

**Date**: {datetime.now().strftime('%B %d, %Y')}  
**WCAG Version**: {results['wcag_version']}  
**Status**: {'✅ PASSED' if critical_issues == 0 else '⚠️ NEEDS ATTENTION'}  
**Total Issues**: {total_issues} (Critical: {critical_issues})

## Summary

This basic accessibility audit checks our website against fundamental WCAG 2.1 AA requirements.

## Test Results

### HTML Structure {'✅' if results['tests']['html_structure']['passed'] else '❌'}

"""
        
        if results["tests"]["html_structure"]["issues"]:
            report_content += "**Issues Found:**\n"
            for issue in results["tests"]["html_structure"]["issues"]:
                report_content += f"- {issue}\n"
        else:
            report_content += "*All HTML structure tests passed.*\n"
        
        report_content += f"""
### Content Accessibility {'✅' if results['tests']['content_accessibility']['passed'] else '❌'}

"""
        
        if results["tests"]["content_accessibility"]["issues"]:
            report_content += "**Issues Found:**\n"
            for issue in results["tests"]["content_accessibility"]["issues"]:
                report_content += f"- {issue}\n"
        else:
            report_content += "*All content accessibility tests passed.*\n"
        
        report_content += f"""
## Overall Assessment

{'✅ All critical accessibility requirements are met.' if critical_issues == 0 else f'❌ {critical_issues} critical accessibility issues need attention.'}

## Next Steps

{'Continue monitoring accessibility with each content update.' if critical_issues == 0 else 'Address the critical issues above to maintain WCAG 2.1 AA compliance.'}

---
*Report generated automatically on {results['timestamp']}*
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 Basic accessibility report saved: {report_file}")
        
        # Print summary to console
        print(f"\n📊 Audit Summary:")
        print(f"  Total Issues: {total_issues}")
        print(f"  Critical Issues: {critical_issues}")
        print(f"  Status: {'PASSED' if critical_issues == 0 else 'NEEDS ATTENTION'}")

def main():
    """Run basic accessibility audit"""
    checker = SimpleAccessibilityChecker()
    results = checker.run_basic_audit()
    
    # Exit with error code if critical issues found
    critical_issues = sum(1 for test_result in results["tests"].values() if not test_result.get("passed", True))
    if critical_issues > 0:
        print(f"❌ Accessibility audit failed with {critical_issues} critical issues")
        exit(1)
    else:
        print("✅ All accessibility tests passed!")
        exit(0)

if __name__ == "__main__":
    main()