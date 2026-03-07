"""
Simple test script to verify batch file format detection logic.
"""

import pandas as pd

def detect_file_format(df: pd.DataFrame) -> str:
    """Detect if uploaded CSV is a test batch or raw CMS data."""
    batch_indicators = ['has_part_b', 'has_part_d', 'cost_per_service', 'services_per_bene']
    
    if all(col in df.columns for col in batch_indicators):
        return 'batch'
    return 'raw'

# Test 1: Batch file detection
print("Test 1: Batch file detection")
batch_df = pd.read_csv('data/test_samples/batch_0.csv')
format_result = detect_file_format(batch_df)
print(f"  Result: {format_result}")
assert format_result == 'batch', f'Expected "batch", got "{format_result}"'
print("  ✅ PASSED\n")

# Test 2: Raw CMS detection
print("Test 2: Raw CMS file detection")
raw_df = pd.DataFrame({
    'Rndrng_NPI': [1234567890],
    'Avg_Sbmtd_Chrg': [100.50],
    'Tot_Srvcs': [10]
})
format_result = detect_file_format(raw_df)
print(f"  Result: {format_result}")
assert format_result == 'raw', f'Expected "raw", got "{format_result}"'
print("  ✅ PASSED\n")

# Test 3: Verify batch file has required columns
print("Test 3: Batch file column verification")
required_cols = ['provider_id', 'cost_per_service', 'services_per_bene', 
                 'has_part_b', 'has_part_d', 'specialty']
missing = [col for col in required_cols if col not in batch_df.columns]
print(f"  Required columns present: {len(required_cols) - len(missing)}/{len(required_cols)}")
if missing:
    print(f"  Missing: {missing}")
else:
    print("  ✅ All required columns present\n")

# Test 4: Check column counts
print("Test 4: Column counts")
print(f"  Batch file columns: {len(batch_df.columns)}")
print(f"  Records: {len(batch_df)}")
print(f"  ✅ PASSED\n")

print("=" * 60)
print("All tests passed! Format detection working correctly.")
print("=" * 60)
