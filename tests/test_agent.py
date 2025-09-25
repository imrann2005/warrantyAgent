import unittest
import sys
import os

# Add the root directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.graph import app

class TestWarrantyAgent(unittest.TestCase):

    def test_active_warranty_lookup(self):
        """
        Tests a query for a product that is currently under warranty.
        """
        # 1. Input
        # This query contains all the necessary details for the main logic path.
        user_query = "What is the warranty status for customer CUST1001, order_id ORD98765 and product QuantumBook Pro 15?"
        
        initial_state = {
            "user_query": user_query,
            "chat_history": []
        }

        # 2. Execution
        # Invoke the agent graph with the initial state.
        final_state = app.invoke(initial_state)

        # 3. Expected Output
        # Based on the data (Order Date: 2024-08-01, Warranty: 24 months),
        # the warranty expires on 2026-08-01 and should be active now.
        expected_response = "The warranty is Active. It expires on 2026-08-01."
        
        # 4. Assertion
        # Check if the agent's final response matches the expected outcome.
        self.assertEqual(final_state.get('response'), expected_response)

if __name__ == '__main__':
    unittest.main()