"""
Sample Insurance Claim Processing System
This module handles insurance claim validation and processing
"""

from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

class ClaimStatus(Enum):
    """Enumeration of possible claim statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    PAID = "paid"

class ClaimValidator:
    """
    Validates insurance claims according to business rules
    
    Business Rules:
    - Claims must be submitted within 30 days of incident
    - Claim amount must not exceed policy limit
    - Customer must have active policy
    """
    
    MAX_DAYS_TO_SUBMIT = 30
    MIN_CLAIM_AMOUNT = 100
    MAX_CLAIM_AMOUNT = 1000000
    
    def __init__(self, policy_service):
        """Initialize validator with policy service dependency"""
        self.policy_service = policy_service
    
    def validate_claim(self, claim: Dict) -> tuple[bool, str]:
        """
        Validate a claim according to business rules
        
        Args:
            claim: Dictionary containing claim information
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Business Rule: Check claim amount
        amount = claim.get('amount', 0)
        if amount < self.MIN_CLAIM_AMOUNT:
            return False, f"Claim amount must be at least ${self.MIN_CLAIM_AMOUNT}"
        
        if amount > self.MAX_CLAIM_AMOUNT:
            return False, f"Claim amount exceeds maximum of ${self.MAX_CLAIM_AMOUNT}"
        
        # Business Rule: Check submission timeframe
        incident_date = claim.get('incident_date')
        if incident_date:
            days_elapsed = (datetime.now() - incident_date).days
            if days_elapsed > self.MAX_DAYS_TO_SUBMIT:
                return False, f"Claim must be submitted within {self.MAX_DAYS_TO_SUBMIT} days"
        
        # Business Rule: Verify active policy
        policy_number = claim.get('policy_number')
        if not self.policy_service.is_policy_active(policy_number):
            return False, "Policy is not active"
        
        return True, ""
    
    def calculate_deductible(self, claim_amount: float, policy_type: str) -> float:
        """
        Calculate deductible based on policy type and claim amount
        
        Business Rule: 
        - Standard policies have 10% deductible
        - Premium policies have 5% deductible
        - Platinum policies have 0% deductible
        """
        deductible_rates = {
            'standard': 0.10,
            'premium': 0.05,
            'platinum': 0.00
        }
        
        rate = deductible_rates.get(policy_type.lower(), 0.10)
        return claim_amount * rate

class ClaimProcessor:
    """Processes approved insurance claims"""
    
    def __init__(self, validator: ClaimValidator, payment_service):
        self.validator = validator
        self.payment_service = payment_service
        self.processed_claims = []
    
    def process_claim(self, claim: Dict) -> Dict:
        """
        Process a claim through the complete workflow
        
        Workflow:
        1. Validate claim
        2. Calculate payout
        3. Initiate payment
        4. Update claim status
        """
        result = {
            'claim_id': claim.get('id'),
            'status': ClaimStatus.PENDING.value,
            'payout_amount': 0,
            'message': ''
        }
        
        # Step 1: Validate
        is_valid, error_msg = self.validator.validate_claim(claim)
        if not is_valid:
            result['status'] = ClaimStatus.REJECTED.value
            result['message'] = error_msg
            return result
        
        # Step 2: Calculate payout
        claim_amount = claim.get('amount', 0)
        policy_type = claim.get('policy_type', 'standard')
        deductible = self.validator.calculate_deductible(claim_amount, policy_type)
        payout = claim_amount - deductible
        
        # Business Rule: Minimum payout threshold
        if payout < 50:
            result['status'] = ClaimStatus.REJECTED.value
            result['message'] = "Payout amount below minimum threshold"
            return result
        
        # Step 3: Process payment
        payment_success = self.payment_service.initiate_payment(
            claim.get('customer_id'),
            payout
        )
        
        if payment_success:
            result['status'] = ClaimStatus.PAID.value
            result['payout_amount'] = payout
            result['message'] = "Claim processed successfully"
            self.processed_claims.append(claim.get('id'))
        else:
            result['status'] = ClaimStatus.UNDER_REVIEW.value
            result['message'] = "Payment processing failed, claim under review"
        
        return result
    
    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        return {
            'total_processed': len(self.processed_claims),
            'processing_rate': self._calculate_processing_rate(),
            'average_payout': self._calculate_average_payout()
        }
    
    def _calculate_processing_rate(self) -> float:
        """Calculate claims processing rate"""
        # Implementation would calculate actual rate
        return 0.95
    
    def _calculate_average_payout(self) -> float:
        """Calculate average payout amount"""
        # Implementation would calculate actual average
        return 5000.0
