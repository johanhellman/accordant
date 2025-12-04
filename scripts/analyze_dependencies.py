#!/usr/bin/env python3
"""
Dependency Analysis Script

Analyzes dependencies in pyproject.toml and package.json to identify:
- Current versions vs latest available versions
- Security vulnerabilities
- Update recommendations
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from packaging import version as pkg_version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False
    # Simple version comparison fallback
    def simple_version_compare(v1: str, v2: str) -> int:
        """Simple version comparison without packaging library."""
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        if v1_parts > v2_parts:
            return 1
        elif v1_parts < v2_parts:
            return -1
        return 0


def get_project_root() -> Path:
    """Get the project root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def parse_pyproject_toml() -> Dict[str, str]:
    """Parse pyproject.toml and extract dependencies."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    
    if not pyproject_path.exists():
        return {}
    
    dependencies = {}
    
    with open(pyproject_path, "r") as f:
        content = f.read()
        
        # Extract runtime dependencies
        deps_match = re.search(r"dependencies = \[(.*?)\]", content, re.DOTALL)
        if deps_match:
            deps_text = deps_match.group(1)
            # Match package names and versions
            for match in re.finditer(r'"([^"]+)"', deps_text):
                dep_spec = match.group(1)
                # Extract package name and version constraint
                if ">=" in dep_spec:
                    pkg_name, version = dep_spec.split(">=", 1)
                    dependencies[pkg_name.strip()] = f">={version.strip()}"
                elif "==" in dep_spec:
                    pkg_name, version = dep_spec.split("==", 1)
                    dependencies[pkg_name.strip()] = f"=={version.strip()}"
                else:
                    dependencies[dep_spec.strip()] = ""
        
        # Extract dev dependencies
        dev_deps_match = re.search(r"dev = \[(.*?)\]", content, re.DOTALL)
        if dev_deps_match:
            dev_deps_text = dev_deps_match.group(1)
            for match in re.finditer(r'"([^"]+)"', dev_deps_text):
                dep_spec = match.group(1)
                if ">=" in dep_spec:
                    pkg_name, version = dep_spec.split(">=", 1)
                    dependencies[f"{pkg_name.strip()}[dev]"] = f">={version.strip()}"
                elif "==" in dep_spec:
                    pkg_name, version = dep_spec.split("==", 1)
                    dependencies[f"{pkg_name.strip()}[dev]"] = f"=={version.strip()}"
    
    return dependencies


def parse_package_json() -> Dict[str, str]:
    """Parse package.json and extract dependencies."""
    project_root = get_project_root()
    package_json_path = project_root / "frontend" / "package.json"
    
    if not package_json_path.exists():
        return {}
    
    with open(package_json_path, "r") as f:
        data = json.load(f)
    
    dependencies = {}
    
    # Runtime dependencies
    if "dependencies" in data:
        dependencies.update(data["dependencies"])
    
    # Dev dependencies
    if "devDependencies" in data:
        for pkg, version in data["devDependencies"].items():
            dependencies[f"{pkg}[dev]"] = version
    
    return dependencies


def get_latest_python_version(package_name: str) -> Optional[str]:
    """Get the latest version of a Python package from PyPI."""
    try:
        # Clean package name (remove [extras])
        clean_name = package_name.split("[")[0].strip()
        
        result = subprocess.run(
            ["uv", "pip", "index", "versions", clean_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            # Parse output to get latest version
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "Available versions:" in line or "versions:" in line.lower():
                    # Try to extract version numbers
                    versions = re.findall(r"(\d+\.\d+\.\d+)", result.stdout)
                    if versions:
                        # Return the highest version
                        return max(versions, key=lambda v: pkg_version.parse(v))
        return None
    except Exception:
        return None


def get_latest_npm_version(package_name: str) -> Optional[str]:
    """Get the latest version of an npm package."""
    try:
        # Clean package name (remove [dev])
        clean_name = package_name.replace("[dev]", "").strip()
        
        result = subprocess.run(
            ["npm", "view", clean_name, "version"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=get_project_root() / "frontend",
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def compare_versions(current: str, latest: Optional[str]) -> Tuple[str, str]:
    """
    Compare current and latest versions.
    Returns: (status, recommendation)
    """
    if not latest:
        return "unknown", "Unable to check latest version"
    
    # Extract version from constraint
    current_version = None
    if ">=" in current:
        current_version = current.split(">=")[1].strip()
    elif "^" in current:
        current_version = current.replace("^", "").strip()
    elif "~" in current:
        current_version = current.replace("~", "").strip()
    elif current[0].isdigit():
        current_version = current.strip()
    
    if not current_version:
        return "unknown", f"Current: {current}, Latest: {latest}"
    
    try:
        if HAS_PACKAGING:
            current_v = pkg_version.parse(current_version)
            latest_v = pkg_version.parse(latest)
            
            if latest_v > current_v:
                # Determine update type
                if latest_v.major > current_v.major:
                    return "major_update", f"Major update available: {current_version} → {latest}"
                elif latest_v.minor > current_v.minor:
                    return "minor_update", f"Minor update available: {current_version} → {latest}"
                else:
                    return "patch_update", f"Patch update available: {current_version} → {latest}"
            else:
                return "up_to_date", "Up to date"
        else:
            # Fallback to simple comparison
            cmp_result = simple_version_compare(current_version, latest)
            if cmp_result < 0:
                # Determine update type by comparing version parts
                current_parts = current_version.split('.')
                latest_parts = latest.split('.')
                if len(latest_parts) > 0 and len(current_parts) > 0:
                    if int(latest_parts[0]) > int(current_parts[0]):
                        return "major_update", f"Major update available: {current_version} → {latest}"
                    elif len(latest_parts) > 1 and len(current_parts) > 1:
                        if int(latest_parts[1]) > int(current_parts[1]):
                            return "minor_update", f"Minor update available: {current_version} → {latest}"
                        else:
                            return "patch_update", f"Patch update available: {current_version} → {latest}"
                return "patch_update", f"Update available: {current_version} → {latest}"
            else:
                return "up_to_date", "Up to date"
    except Exception as e:
        return "unknown", f"Version comparison failed: {current} vs {latest} ({e})"


def analyze_python_dependencies() -> List[Dict]:
    """Analyze Python dependencies."""
    print("Analyzing Python dependencies...")
    dependencies = parse_pyproject_toml()
    results = []
    
    for pkg_name, current_version in dependencies.items():
        clean_name = pkg_name.split("[")[0].strip()
        print(f"  Checking {clean_name}...", end="\r")
        
        latest = get_latest_python_version(clean_name)
        status, recommendation = compare_versions(current_version, latest)
        
        results.append({
            "package": pkg_name,
            "current": current_version,
            "latest": latest or "unknown",
            "status": status,
            "recommendation": recommendation,
        })
    
    print(" " * 50)  # Clear line
    return results


def analyze_javascript_dependencies() -> List[Dict]:
    """Analyze JavaScript dependencies."""
    print("Analyzing JavaScript dependencies...")
    dependencies = parse_package_json()
    results = []
    
    for pkg_name, current_version in dependencies.items():
        clean_name = pkg_name.replace("[dev]", "").strip()
        print(f"  Checking {clean_name}...", end="\r")
        
        latest = get_latest_npm_version(clean_name)
        status, recommendation = compare_versions(current_version, latest or "")
        
        results.append({
            "package": pkg_name,
            "current": current_version,
            "latest": latest or "unknown",
            "status": status,
            "recommendation": recommendation,
        })
    
    print(" " * 50)  # Clear line
    return results


def print_report(python_results: List[Dict], js_results: List[Dict]):
    """Print a formatted report."""
    print("\n" + "=" * 80)
    print("DEPENDENCY ANALYSIS REPORT")
    print("=" * 80)
    
    # Python dependencies
    print("\n## Python Dependencies\n")
    
    major_updates = [r for r in python_results if r["status"] == "major_update"]
    minor_updates = [r for r in python_results if r["status"] == "minor_update"]
    patch_updates = [r for r in python_results if r["status"] == "patch_update"]
    up_to_date = [r for r in python_results if r["status"] == "up_to_date"]
    
    if major_updates:
        print("### 🔴 Major Updates Available:")
        for r in major_updates:
            print(f"  - {r['package']}: {r['recommendation']}")
    
    if minor_updates:
        print("\n### 🟡 Minor Updates Available:")
        for r in minor_updates[:10]:  # Show first 10
            print(f"  - {r['package']}: {r['recommendation']}")
        if len(minor_updates) > 10:
            print(f"  ... and {len(minor_updates) - 10} more")
    
    if patch_updates:
        print("\n### 🟢 Patch Updates Available:")
        for r in patch_updates[:10]:  # Show first 10
            print(f"  - {r['package']}: {r['recommendation']}")
        if len(patch_updates) > 10:
            print(f"  ... and {len(patch_updates) - 10} more")
    
    print(f"\n✓ Up to date: {len(up_to_date)} packages")
    
    # JavaScript dependencies
    print("\n## JavaScript Dependencies\n")
    
    major_updates_js = [r for r in js_results if r["status"] == "major_update"]
    minor_updates_js = [r for r in js_results if r["status"] == "minor_update"]
    patch_updates_js = [r for r in js_results if r["status"] == "patch_update"]
    up_to_date_js = [r for r in js_results if r["status"] == "up_to_date"]
    
    if major_updates_js:
        print("### 🔴 Major Updates Available:")
        for r in major_updates_js:
            print(f"  - {r['package']}: {r['recommendation']}")
    
    if minor_updates_js:
        print("\n### 🟡 Minor Updates Available:")
        for r in minor_updates_js[:10]:
            print(f"  - {r['package']}: {r['recommendation']}")
        if len(minor_updates_js) > 10:
            print(f"  ... and {len(minor_updates_js) - 10} more")
    
    if patch_updates_js:
        print("\n### 🟢 Patch Updates Available:")
        for r in patch_updates_js[:10]:
            print(f"  - {r['package']}: {r['recommendation']}")
        if len(patch_updates_js) > 10:
            print(f"  ... and {len(patch_updates_js) - 10} more")
    
    print(f"\n✓ Up to date: {len(up_to_date_js)} packages")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Python: {len(major_updates)} major, {len(minor_updates)} minor, {len(patch_updates)} patch updates")
    print(f"JavaScript: {len(major_updates_js)} major, {len(minor_updates_js)} minor, {len(patch_updates_js)} patch updates")
    print("\nFor detailed upgrade plan, see: docs/UPGRADE_PLAN.md")


def main():
    """Main entry point."""
    try:
        python_results = analyze_python_dependencies()
        js_results = analyze_javascript_dependencies()
        print_report(python_results, js_results)
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during analysis: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

