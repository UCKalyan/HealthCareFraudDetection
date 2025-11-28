import sys
import os
import pandas as pd
import logging
import unittest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.semantic_search import SemanticSearchEngine

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestSemanticSearchScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create dummy data covering various scenarios
        data = {
            'provider_id': range(1, 11),
            'Prscrbr_First_Name': ['Doc' + str(i) for i in range(1, 11)],
            'Prscrbr_Last_Org_Name': ['Test' + str(i) for i in range(1, 11)],
            'specialty': [
                'Cardiology', 'Cardiology', 'Cardiology', 
                'Dermatology', 'Dermatology', 'Dermatology',
                'Pediatrics', 'Pediatrics', 'Pediatrics',
                'Anesthesiology'
            ],
            'risk_score': [
                0.9, 0.5, 0.1,  # Cardiology: High, Medium, Low
                0.9, 0.5, 0.1,  # Dermatology: High, Medium, Low
                0.9, 0.5, 0.1,  # Pediatrics: High, Medium, Low
                0.8             # Anesthesiology: High
            ],
            'cost_per_service': [
                100, 100, 100,
                200, 200, 200,
                50, 50, 50,
                500
            ],
            'services_per_bene': [10] * 10
        }
        cls.df = pd.DataFrame(data)
        cls.engine = SemanticSearchEngine()
        cls.engine.set_data(cls.df)
        cls.engine._ensure_indexed()

    def test_explicit_high_risk(self):
        """Test 'high risk cardiology' -> Expect High risk results"""
        results = self.engine.search("high risk cardiology", k=5)
        for r in results:
            self.assertEqual(r['risk_status'], 'High', f"Failed for {r['name']}")

    def test_explicit_medium_risk(self):
        """Test 'medium risk dermatology' -> Expect Medium risk results"""
        results = self.engine.search("medium risk dermatology", k=5)
        for r in results:
            self.assertEqual(r['risk_status'], 'Medium', f"Failed for {r['name']}")

    def test_explicit_low_risk(self):
        """Test 'low risk pediatrics' -> Expect Low risk results"""
        results = self.engine.search("low risk pediatrics", k=5)
        for r in results:
            self.assertEqual(r['risk_status'], 'Low', f"Failed for {r['name']}")

    def test_implicit_high_risk(self):
        """Test 'high cardiology' -> Expect High risk results"""
        results = self.engine.search("high cardiology", k=5)
        for r in results:
            self.assertEqual(r['risk_status'], 'High', f"Failed for {r['name']}")

    def test_implicit_medium_risk(self):
        """Test 'medium dermatology' -> Expect Medium risk results"""
        results = self.engine.search("medium dermatology", k=5)
        for r in results:
            self.assertEqual(r['risk_status'], 'Medium', f"Failed for {r['name']}")

    def test_implicit_low_risk(self):
        """Test 'low pediatrics' -> Expect Low risk results"""
        results = self.engine.search("low pediatrics", k=5)
        for r in results:
            self.assertEqual(r['risk_status'], 'Low', f"Failed for {r['name']}")

    def test_cost_query_negative(self):
        """Test 'high cost cardiology' -> Should NOT filter by risk (expect mixed)"""
        # Note: This test assumes that "high cost" should NOT trigger "high risk" filter.
        # Since we have High, Medium, Low cardiology providers, if we get non-High providers, it passes.
        results = self.engine.search("high cost cardiology", k=5)
        risk_statuses = {r['risk_status'] for r in results}
        # We expect at least one non-High result if the filter is NOT applied
        # (Assuming the semantic search returns relevant results, which might include the low risk ones)
        # Actually, "high cost" might semantically match the high cost providers?
        # But our dummy data has constant cost for cardiology.
        # So it should return all of them.
        self.assertTrue(len(risk_statuses) > 1, f"Expected mixed results, got: {risk_statuses}")

    def test_mixed_explicit_overrides(self):
        """Test 'high risk high cost' -> Expect High risk results"""
        results = self.engine.search("high risk high cost", k=5)
        for r in results:
            self.assertEqual(r['risk_status'], 'High', f"Failed for {r['name']}")

if __name__ == "__main__":
    unittest.main()
