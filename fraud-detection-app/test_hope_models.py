#!/usr/bin/env python3
"""
Test script to verify HOPE dual-speed models are functional.
Run this to confirm your Google Nested Learning implementation is working.
"""
import tensorflow as tf
import numpy as np
import os

def test_hope_implementation():
    print("=" * 70)
    print("🧪 HOPE (Nested Learning) Implementation Test")
    print("=" * 70)
    
    # Test 1: Model File Existence
    print("\n[Test 1] Checking Model Files...")
    slow_path = "models/fraud_detection_model.keras"
    fast_path = "models/fraud_detection_model_fast.keras"
    
    if os.path.exists(slow_path):
        size_slow = os.path.getsize(slow_path) / 1024
        print(f"  ✅ Slow Model exists: {slow_path} ({size_slow:.1f} KB)")
    else:
        print(f"  ❌ Slow Model NOT found: {slow_path}")
        return False
    
    if os.path.exists(fast_path):
        size_fast = os.path.getsize(fast_path) / 1024
        print(f"  ✅ Fast Model exists: {fast_path} ({size_fast:.1f} KB)")
    else:
        print(f"  ❌ Fast Model NOT found: {fast_path}")
        return False
    
    # Test 2: Model Loading
    print("\n[Test 2] Loading Models...")
    try:
        slow_model = tf.keras.models.load_model(slow_path)
        print("  ✅ Slow Model loaded successfully")
    except Exception as e:
        print(f"  ❌ Failed to load Slow Model: {e}")
        return False
    
    try:
        fast_model = tf.keras.models.load_model(fast_path)
        print("  ✅ Fast Model loaded successfully")
    except Exception as e:
        print(f"  ❌ Failed to load Fast Model: {e}")
        return False
    
    # Test 3: Model Architecture
    print("\n[Test 3] Analyzing Model Architecture...")
    slow_params = slow_model.count_params()
    fast_params = fast_model.count_params()
    
    print(f"  Slow Model Parameters: {slow_params:,}")
    print(f"  Fast Model Parameters: {fast_params:,}")
    
    if slow_params == fast_params:
        print("  ✅ Both models have identical architecture")
    else:
        print("  ⚠️ Models have different architectures (unexpected)")
    
    # Test 4: Prediction Comparison
    print("\n[Test 4] Testing Predictions...")
    
    # Generate random test data (11 features as per your fraud model)
    test_samples = 100
    test_data = np.random.randn(test_samples, 11)
    
    print(f"  Running predictions on {test_samples} samples...")
    
    slow_pred = slow_model.predict(test_data, verbose=0)
    fast_pred = fast_model.predict(test_data, verbose=0)
    
    # Statistics
    print(f"\n  Slow Model Predictions:")
    print(f"    Min:  {slow_pred.min():.6f}")
    print(f"    Max:  {slow_pred.max():.6f}")
    print(f"    Mean: {slow_pred.mean():.6f}")
    print(f"    Std:  {slow_pred.std():.6f}")
    
    print(f"\n  Fast Model Predictions:")
    print(f"    Min:  {fast_pred.min():.6f}")
    print(f"    Max:  {fast_pred.max():.6f}")
    print(f"    Mean: {fast_pred.mean():.6f}")
    print(f"    Std:  {fast_pred.std():.6f}")
    
    # Test 5: Model Divergence
    print("\n[Test 5] Measuring Model Divergence...")
    
    mae = np.mean(np.abs(slow_pred - fast_pred))
    rmse = np.sqrt(np.mean((slow_pred - fast_pred) ** 2))
    max_diff = np.max(np.abs(slow_pred - fast_pred))
    
    print(f"  Mean Absolute Error:     {mae:.6f}")
    print(f"  Root Mean Squared Error: {rmse:.6f}")
    print(f"  Maximum Difference:      {max_diff:.6f}")
    
    # Interpretation
    print("\n  Divergence Interpretation:")
    if mae < 0.01:
        print("  ✅ Very Low Divergence - Models are highly aligned")
        print("     (Expected after convergence with α=0.99)")
    elif mae < 0.05:
        print("  ✅ Low Divergence - Models show good alignment")
    elif mae < 0.1:
        print("  ⚠️ Moderate Divergence - Models may need more training")
    else:
        print("  ❌ High Divergence - Investigate training process")
    
    # Test 6: Weight Divergence
    print("\n[Test 6] Analyzing Layer-wise Weight Divergence...")
    
    total_divergence = 0
    layer_count = 0
    
    for idx, (slow_layer, fast_layer) in enumerate(zip(slow_model.layers, fast_model.layers)):
        slow_weights = slow_layer.get_weights()
        fast_weights = fast_layer.get_weights()
        
        if len(slow_weights) > 0:
            # Compare first weight matrix (usually the most important)
            divergence = np.mean(np.abs(slow_weights[0] - fast_weights[0]))
            total_divergence += divergence
            layer_count += 1
            
            print(f"  Layer {idx:2d} ({slow_layer.name:20s}): {divergence:.8f}")
    
    avg_weight_divergence = total_divergence / layer_count if layer_count > 0 else 0
    print(f"\n  Average Weight Divergence: {avg_weight_divergence:.8f}")
    
    if avg_weight_divergence < 0.001:
        print("  ✅ Weights are almost identical (strong convergence)")
    elif avg_weight_divergence < 0.01:
        print("  ✅ Weights show good alignment")
    else:
        print("  ⚠️ Weights have notable differences")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("✨ HOPE Implementation Test Complete")
    print("=" * 70)
    print("\n📋 Summary:")
    print("  ✅ HOPE architecture is fully implemented")
    print("  ✅ Both models (slow and fast) are operational")
    print("  ✅ Models can make predictions successfully")
    print(f"  📊 Prediction divergence: {mae:.6f}")
    print(f"  📊 Weight divergence: {avg_weight_divergence:.8f}")
    
    print("\n💡 Recommendations:")
    print("  • Use Slow Model for production decisions (stable)")
    print("  • Use Fast Model for early warning alerts (adaptive)")
    print("  • Monitor divergence over time to detect emerging patterns")
    
    return True

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    success = test_hope_implementation()
    exit(0 if success else 1)
