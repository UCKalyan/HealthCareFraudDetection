try:
    import langgraph
    import langchain
    from src.workflows.fraud_graph import build_fraud_graph
    print("SUCCESS: LangGraph and Workflow imported successfully.")
except ImportError as e:
    print(f"ERROR: ImportError: {e}")
except Exception as e:
    print(f"ERROR: {e}")
