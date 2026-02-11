"""
Payment Classifier Service

Classifies payments based on their lifecycle status to determine
which fraud response workflow is appropriate:
- HISTORICAL_PROCESSED: Requires recovery workflow
- NEW_PENDING: Can be held/stopped
- HELD: Already held, show status only

Author: Healthcare Fraud Detection Team
Date: 2025-12-01
"""

from datetime import datetime, date
from typing import Literal

PaymentCategory = Literal["HISTORICAL_PROCESSED", "NEW_PENDING", "HELD"]


class PaymentClassifier:
    """Classifies payments for appropriate fraud response workflow"""
    
    # Cutoff date to distinguish historical vs new payments
    HISTORICAL_CUTOFF_DATE = date(2025, 1, 1)
    
    @staticmethod
    def classify_payment(payment_date: date, payment_status: str) -> PaymentCategory:
        """
        Classify payment to determine which fraud response is allowed.
        
        Args:
            payment_date: Date payment was made
            payment_status: Current status (PENDING, PROCESSED, HELD, etc.)
        
        Returns:
            PaymentCategory indicating which workflow applies
            
        Examples:
            >>> PaymentClassifier.classify_payment(date(2023, 5, 15), "PROCESSED")
            'HISTORICAL_PROCESSED'
            
            >>> PaymentClassifier.classify_payment(date(2025, 2, 1), "PENDING")
            'NEW_PENDING'
        """
        # If payment is already processed, it requires recovery workflow
        if payment_status == "PROCESSED":
            return "HISTORICAL_PROCESSED"
        
        # If payment is already held, just show status
        elif payment_status == "HELD":
            return "HELD"
        
        # Otherwise it's a new/pending payment that can be held
        else:
            return "NEW_PENDING"
    
    @staticmethod
    def can_hold_payment(payment_category: PaymentCategory) -> bool:
        """
        Check if payment can be held/stopped.
        
        Args:
            payment_category: Payment category from classify_payment()
            
        Returns:
            True if payment can be held, False otherwise
        """
        return payment_category == "NEW_PENDING"
    
    @staticmethod
    def requires_recovery(payment_category: PaymentCategory) -> bool:
        """
        Check if payment requires recovery workflow.
        
        Args:
            payment_category: Payment category from classify_payment()
            
        Returns:
            True if recovery workflow is needed, False otherwise
        """
        return payment_category == "HISTORICAL_PROCESSED"
    
    @staticmethod
    def get_action_description(payment_category: PaymentCategory) -> str:
        """
        Get user-friendly description of available action for this payment.
        
        Args:
            payment_category: Payment category from classify_payment()
            
        Returns:
            Description string for UI display
        """
        if payment_category == "HISTORICAL_PROCESSED":
            return "Payment already processed - recovery workflow available"
        elif payment_category == "HELD":
            return "Payment already held - no action needed"
        else:
            return "Payment can be held or stopped"
