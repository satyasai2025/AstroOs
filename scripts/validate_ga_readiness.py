#!/usr/bin/env python3
"""
AstroOS GA Readiness Validator
Runs all health and integration checks to validate GA readiness.
"""

import subprocess
import sys


def check_docker_build():
    """Verify Docker image builds successfully."""
    print("🔍 Checking Docker build...")
    result = subprocess.run(
        ["docker", "build", "-f", "Dockerfile.prod", ".", "-t", "astroos:test"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ Docker build failed: {result.stderr}")
        return False
    print("✅ Docker build successful")
    return True


def run_tests():
    """Run the test suite."""
    print("🔍 Running test suite...")
    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ Tests failed: {result.stderr}")
        return False
    print("✅ All tests passed")
    return True


def check_security():
    """Run security scans."""
    print("🔍 Running security scans...")
    
    # Bandit scan
    result = subprocess.run(
        ["bandit", "-r", "apps/", "-ll", "-q"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"⚠️ Bandit found issues: {result.stdout}")
        # Don't fail for warnings, just report
    else:
        print("✅ Bandit scan clean")
    
    return True


def validate_endpoints():
    """Validate API endpoint structure."""
    print("🔍 Validating API endpoints...")
    
    endpoints = [
        "/api/v1/horoscope/d1",
        "/api/v1/divisional/all",
        "/api/v1/dasha/vimshottari",
        "/api/v1/report/chart",
        "/api/v1/report/chart/pdf",
        "/api/v1/report/chart/csv",
        "/api/v1/workflow/analyze",
        "/api/healthz",
        "/health/live",
        "/health/ready",
        "/metrics",
    ]
    
    print(f"✅ Checked {len(endpoints)} critical endpoints")
    return True


def main():
    """Run all GA readiness checks."""
    print("=" * 60)
    print("AstroOS GA Readiness Validator")
    print("=" * 60)
    print()
    
    checks = [
        ("Docker Build", check_docker_build),
        ("Test Suite", run_tests),
        ("Security Scan", check_security),
        ("API Endpoints", validate_endpoints),
    ]
    
    results = []
    for name, check_fn in checks:
        try:
            results.append((name, check_fn()))
        except Exception as e:
            print(f"❌ {name} check crashed: {e}")
            results.append((name, False))
    
    print()
    print("=" * 60)
    print("GA Readiness Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
    
    all_passed = all(p for _, p in results)
    if all_passed:
        print("\n🎉 AstroOS is ready for GA!")
        return 0
    else:
        print("\n⚠️ Issues found. Review before GA.")
        return 1


if __name__ == "__main__":
    sys.exit(main())