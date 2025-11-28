import unittest
import pandas as pd
import numpy as np
from src.services.semantic_search import SemanticSearchEngine

class TestSemanticSearch(unittest.TestCase):
    def setUp(self):
        # Create mock data
        data = {
            'provider_id': [1001, 1002, 1003],
            'Prscrbr_First_Name': ['John', 'Jane', 'Bob'],
            'Prscrbr_Last_Org_Name': ['Doe', 'Smith', 'Jones'],
            'specialty': ['Cardiology', 'Dermatology', 'General Practice'],
            'risk_score': [0.85, 0.1, 0.4],
            'cost_per_service': [150.0, 50.0, 80.0],
            'services_per_bene': [12.5, 2.0, 4.0]
        }
        self.df = pd.DataFrame(data)
        self.engine = SemanticSearchEngine(model_name='all-MiniLM-L6-v2')
        self.engine.set_data(self.df)
        self.engine._ensure_indexed()

    def test_search_structure(self):
        results = self.engine.search("heart doctor", k=1)
        self.assertTrue(len(results) > 0)
        result = results[0]
        
        # Check keys
        expected_keys = {'npi', 'similarity', 'name', 'specialty', 'risk_score', 'risk_status', 'cost_per_service'}
        self.assertTrue(expected_keys.issubset(result.keys()))
        
        # Check values
        self.assertEqual(result['npi'], '1001')
        self.assertEqual(result['name'], 'John Doe')
        self.assertEqual(result['specialty'], 'Cardiology')
        self.assertEqual(result['risk_status'], 'High')
        self.assertEqual(result['cost_per_service'], 150.0)
        self.assertIsInstance(result['similarity'], float)

    def test_search_relevance(self):
        # "skin" should match Dermatology (Jane Smith)
        results = self.engine.search("skin problems", k=1)
        self.assertEqual(results[0]['name'], 'Jane Smith')
        self.assertEqual(results[0]['specialty'], 'Dermatology')

if __name__ == '__main__':
    unittest.main()
