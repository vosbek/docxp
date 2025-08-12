"""
Customer Management System
Handles customer data and policy management
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

@dataclass
class Customer:
    """Customer entity with policy information"""
    id: str
    name: str
    email: str
    phone: str
    date_of_birth: datetime
    policies: List['Policy']
    risk_score: float = 0.0
    
    def calculate_age(self) -> int:
        """Calculate customer's current age"""
        today = datetime.now()
        return today.year - self.date_of_birth.year

@dataclass
class Policy:
    """Insurance policy details"""
    policy_number: str
    policy_type: str  # standard, premium, platinum
    start_date: datetime
    end_date: datetime
    premium_amount: float
    coverage_limit: float
    is_active: bool = True
    
    def days_until_renewal(self) -> int:
        """Calculate days until policy renewal"""
        return (self.end_date - datetime.now()).days
    
    def requires_renewal(self) -> bool:
        """Check if policy needs renewal within 30 days"""
        return self.days_until_renewal() <= 30

class CustomerService:
    """Service for managing customers and policies"""
    
    def __init__(self, database_connection):
        self.db = database_connection
        self.customers = {}
    
    def create_customer(self, customer_data: dict) -> Customer:
        """
        Create a new customer
        
        Business Rule: Customer must be 18 or older
        """
        dob = customer_data.get('date_of_birth')
        age = (datetime.now() - dob).days // 365
        
        if age < 18:
            raise ValueError("Customer must be 18 or older")
        
        customer = Customer(
            id=self._generate_id(),
            name=customer_data['name'],
            email=customer_data['email'],
            phone=customer_data['phone'],
            date_of_birth=dob,
            policies=[]
        )
        
        self.customers[customer.id] = customer
        return customer
    
    def add_policy(self, customer_id: str, policy_data: dict) -> Policy:
        """
        Add a policy to a customer
        
        Business Rules:
        - Customer can have maximum 5 active policies
        - Premium amount must be positive
        - Coverage limit must exceed premium by at least 10x
        """
        customer = self.customers.get(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        
        # Business Rule: Maximum policies check
        active_policies = [p for p in customer.policies if p.is_active]
        if len(active_policies) >= 5:
            raise ValueError("Customer has reached maximum number of active policies")
        
        premium = policy_data.get('premium_amount', 0)
        coverage = policy_data.get('coverage_limit', 0)
        
        # Business Rule: Premium validation
        if premium <= 0:
            raise ValueError("Premium amount must be positive")
        
        # Business Rule: Coverage validation
        if coverage < premium * 10:
            raise ValueError("Coverage limit must be at least 10x the premium")
        
        policy = Policy(
            policy_number=self._generate_policy_number(),
            policy_type=policy_data['policy_type'],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=365),
            premium_amount=premium,
            coverage_limit=coverage
        )
        
        customer.policies.append(policy)
        return policy
    
    def calculate_customer_risk(self, customer_id: str) -> float:
        """
        Calculate customer risk score
        
        Risk factors:
        - Age (younger = higher risk)
        - Number of claims
        - Payment history
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return 0.0
        
        risk_score = 0.0
        
        # Age factor
        age = customer.calculate_age()
        if age < 25:
            risk_score += 30
        elif age < 35:
            risk_score += 20
        elif age < 50:
            risk_score += 10
        
        # Policy factor
        if len(customer.policies) == 0:
            risk_score += 15  # New customer risk
        
        # Normalize to 0-100 scale
        customer.risk_score = min(risk_score, 100)
        return customer.risk_score
    
    def get_customers_for_renewal(self) -> List[Customer]:
        """Get list of customers with policies due for renewal"""
        renewal_customers = []
        
        for customer in self.customers.values():
            for policy in customer.policies:
                if policy.is_active and policy.requires_renewal():
                    renewal_customers.append(customer)
                    break
        
        return renewal_customers
    
    def _generate_id(self) -> str:
        """Generate unique customer ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _generate_policy_number(self) -> str:
        """Generate unique policy number"""
        import random
        return f"POL-{random.randint(100000, 999999)}"
