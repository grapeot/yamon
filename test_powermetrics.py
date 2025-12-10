#!/usr/bin/env python3
"""Test script to check powermetrics output format"""

import subprocess
import sys
from yamon.apple_api import AppleAPICollector

print("Testing powermetrics collection...")
print("=" * 60)

# Test 1: Check if powermetrics is available
try:
    result = subprocess.run(['which', 'powermetrics'], capture_output=True, timeout=1)
    if result.returncode == 0:
        print("✓ powermetrics found")
    else:
        print("✗ powermetrics not found")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error checking powermetrics: {e}")
    sys.exit(1)

# Test 2: Try to run powermetrics
print("\nAttempting to run powermetrics...")
try:
    cmd = [
        'powermetrics',
        '-i', '1000',
        '-n', '1',
        '--samplers', 'cpu_power,gpu_power,ane_power'
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        timeout=5,
        text=True
    )
    
    print(f"Return code: {result.returncode}")
    
    if result.returncode == 0:
        print("\n✓ powermetrics succeeded!")
        print("\nOutput:")
        print("-" * 60)
        print(result.stdout)
        print("-" * 60)
        
        # Try to parse
        collector = AppleAPICollector()
        metrics = collector._parse_powermetrics_text(result.stdout)
        
        print("\nParsed metrics:")
        print(f"  CPU Power: {metrics.cpu_power} W")
        print(f"  GPU Power: {metrics.gpu_power} W")
        print(f"  ANE Power: {metrics.ane_power} W")
        print(f"  GPU Freq: {metrics.gpu_freq_mhz} MHz")
    else:
        print("\n✗ powermetrics failed")
        print("Error output:")
        print(result.stderr)
        print("\nNote: powermetrics requires sudo. Try:")
        print("  sudo python3 test_powermetrics.py")
        
except subprocess.TimeoutExpired:
    print("✗ powermetrics timed out")
except Exception as e:
    print(f"✗ Exception: {e}")
    import traceback
    traceback.print_exc()

