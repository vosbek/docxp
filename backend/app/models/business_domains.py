"""
Business Domain Taxonomy for DocXP Enterprise
Hierarchical classification system for enterprise business domains and processes
"""

from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.models.base import Base

class DomainCategory(Enum):
    """Top-level domain categories"""
    CORE_BUSINESS = "core_business"
    SUPPORTING_OPERATIONS = "supporting_operations"  
    INFRASTRUCTURE = "infrastructure"
    COMPLIANCE_GOVERNANCE = "compliance_governance"
    CUSTOMER_FACING = "customer_facing"
    INTEGRATION = "integration"

class BusinessSubdomain(Enum):
    """Detailed business subdomains"""
    # Core Business
    CLAIMS_PROCESSING = "claims_processing"
    POLICY_MANAGEMENT = "policy_management"
    UNDERWRITING = "underwriting"
    PREMIUM_CALCULATION = "premium_calculation"
    ACTUARIAL_ANALYSIS = "actuarial_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    
    # Supporting Operations
    PAYMENT_PROCESSING = "payment_processing"
    BILLING_INVOICING = "billing_invoicing"
    COMMISSION_MANAGEMENT = "commission_management"
    ACCOUNTING_FINANCE = "accounting_finance"
    HUMAN_RESOURCES = "human_resources"
    VENDOR_MANAGEMENT = "vendor_management"
    
    # Customer Facing
    CUSTOMER_MANAGEMENT = "customer_management"
    CUSTOMER_SERVICE = "customer_service"
    SALES_MANAGEMENT = "sales_management"
    MARKETING_CAMPAIGNS = "marketing_campaigns"
    SELF_SERVICE_PORTAL = "self_service_portal"
    MOBILE_SERVICES = "mobile_services"
    
    # Infrastructure
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    WORKFLOW_MANAGEMENT = "workflow_management"
    DOCUMENT_MANAGEMENT = "document_management"
    NOTIFICATION_SYSTEM = "notification_system"
    REPORTING_ANALYTICS = "reporting_analytics"
    DATA_MANAGEMENT = "data_management"
    SYSTEM_ADMINISTRATION = "system_administration"
    
    # Compliance & Governance
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    AUDIT_TRAIL = "audit_trail"
    DATA_PRIVACY = "data_privacy"
    SECURITY_MONITORING = "security_monitoring"
    RISK_COMPLIANCE = "risk_compliance"
    BUSINESS_CONTINUITY = "business_continuity"
    
    # Integration
    EXTERNAL_SYSTEMS = "external_systems"
    DATA_INTEGRATION = "data_integration"
    API_MANAGEMENT = "api_management"
    LEGACY_INTEGRATION = "legacy_integration"
    THIRD_PARTY_SERVICES = "third_party_services"

# SQLAlchemy Models

class DomainTaxonomy(Base):
    """
    Hierarchical business domain taxonomy
    Supports multi-level domain classification
    """
    __tablename__ = "domain_taxonomy"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Hierarchy
    parent_domain_id = Column(String(100), ForeignKey("domain_taxonomy.domain_id"))
    category = Column(String(50), nullable=False)  # DomainCategory enum
    subdomain = Column(String(100))  # BusinessSubdomain enum
    level = Column(Integer, default=0)  # 0=category, 1=subdomain, 2=specific
    
    # Domain details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    business_purpose = Column(Text)
    typical_components = Column(ARRAY(String))  # Common technology components
    key_stakeholders = Column(ARRAY(String))  # Business stakeholders
    
    # Classification metadata
    keywords = Column(ARRAY(String))  # Keywords for automatic classification
    patterns = Column(ARRAY(String))  # Code/filename patterns
    regulatory_scope = Column(ARRAY(String))  # SOX, GDPR, HIPAA, etc.
    
    # Relationships
    parent = relationship("DomainTaxonomy", remote_side="DomainTaxonomy.domain_id")
    children = relationship("DomainTaxonomy", back_populates="parent")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DomainClassificationRule(Base):
    """
    Rules for automatic domain classification
    ML and heuristic-based classification logic
    """
    __tablename__ = "domain_classification_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(String(100), unique=True, nullable=False)
    
    # Rule definition
    rule_name = Column(String(200), nullable=False)
    rule_type = Column(String(50), nullable=False)  # keyword, pattern, ml_model
    target_domain = Column(String(100), ForeignKey("domain_taxonomy.domain_id"), nullable=False)
    
    # Rule logic
    keywords = Column(ARRAY(String))  # Keyword matching
    file_patterns = Column(ARRAY(String))  # File path patterns
    code_patterns = Column(ARRAY(String))  # Code content patterns
    ml_model_path = Column(String(500))  # Path to ML model file
    
    # Rule metadata
    confidence_weight = Column(Float, default=1.0)  # 0.0 to 1.0
    priority = Column(Integer, default=100)  # Lower = higher priority
    is_active = Column(Boolean, default=True)
    validation_accuracy = Column(Float)  # Historical accuracy
    
    # Context
    created_by = Column(String(100))
    description = Column(Text)
    
    # Relationships
    target_domain_obj = relationship("DomainTaxonomy")
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DomainClassificationResult(Base):
    """
    Results of domain classification for code components
    Tracks classification history and accuracy
    """
    __tablename__ = "domain_classification_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Component being classified
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    file_path = Column(String(1000), nullable=False)
    component_name = Column(String(500))  # Class, method, JSP name
    component_type = Column(String(100))  # "class", "method", "jsp", "action"
    
    # Classification results
    primary_domain = Column(String(100), ForeignKey("domain_taxonomy.domain_id"), nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    secondary_domains = Column(JSON)  # Additional domains with scores
    
    # Classification metadata
    classification_method = Column(String(100))  # "ml_model", "heuristic", "manual"
    rules_applied = Column(ARRAY(String))  # Rule IDs that contributed
    model_version = Column(String(50))  # ML model version if applicable
    
    # Manual override
    manual_override = Column(Boolean, default=False)
    override_reason = Column(Text)
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    
    # Relationships
    primary_domain_obj = relationship("DomainTaxonomy")
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Schemas

class DomainTaxonomySchema(BaseModel):
    """Pydantic schema for DomainTaxonomy"""
    domain_id: str
    parent_domain_id: Optional[str] = None
    category: DomainCategory
    subdomain: Optional[BusinessSubdomain] = None
    level: int = 0
    name: str
    description: Optional[str] = None
    business_purpose: Optional[str] = None
    typical_components: Optional[List[str]] = []
    key_stakeholders: Optional[List[str]] = []
    keywords: Optional[List[str]] = []
    patterns: Optional[List[str]] = []
    regulatory_scope: Optional[List[str]] = []

    class Config:
        use_enum_values = True

class DomainClassificationRuleSchema(BaseModel):
    """Pydantic schema for DomainClassificationRule"""
    rule_id: str
    rule_name: str
    rule_type: str
    target_domain: str
    keywords: Optional[List[str]] = []
    file_patterns: Optional[List[str]] = []
    code_patterns: Optional[List[str]] = []
    ml_model_path: Optional[str] = None
    confidence_weight: Optional[float] = 1.0
    priority: Optional[int] = 100
    is_active: Optional[bool] = True
    validation_accuracy: Optional[float] = None
    created_by: Optional[str] = None
    description: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}

class DomainClassificationResultSchema(BaseModel):
    """Pydantic schema for DomainClassificationResult"""
    repository_id: str
    file_path: str
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    primary_domain: str
    confidence_score: float
    secondary_domains: Optional[Dict[str, float]] = {}
    classification_method: str
    rules_applied: Optional[List[str]] = []
    model_version: Optional[str] = None
    manual_override: Optional[bool] = False
    override_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}

# Domain Taxonomy Data

ENTERPRISE_DOMAIN_TAXONOMY = {
    # Core Business Domains
    "core_business": {
        "name": "Core Business Operations",
        "description": "Primary business functions that generate revenue",
        "category": DomainCategory.CORE_BUSINESS,
        "children": {
            "claims_processing": {
                "name": "Claims Processing",
                "subdomain": BusinessSubdomain.CLAIMS_PROCESSING,
                "keywords": ["claim", "settlement", "adjudication", "coverage", "deductible", "payout"],
                "patterns": ["*claim*", "*settlement*", "*adjudic*"],
                "typical_components": ["ClaimService", "SettlementAction", "claim.jsp"],
                "business_purpose": "Process insurance claims from submission to settlement"
            },
            "policy_management": {
                "name": "Policy Management", 
                "subdomain": BusinessSubdomain.POLICY_MANAGEMENT,
                "keywords": ["policy", "contract", "premium", "renewal", "endorsement", "coverage"],
                "patterns": ["*policy*", "*contract*", "*premium*", "*renewal*"],
                "typical_components": ["PolicyService", "ContractAction", "policy.jsp"],
                "business_purpose": "Manage insurance policies throughout their lifecycle"
            },
            "underwriting": {
                "name": "Underwriting",
                "subdomain": BusinessSubdomain.UNDERWRITING,
                "keywords": ["underwrite", "risk", "assessment", "approval", "decline", "quote"],
                "patterns": ["*underwrite*", "*risk*", "*quote*", "*approve*"],
                "typical_components": ["UnderwritingService", "RiskAssessment", "quote.jsp"],
                "business_purpose": "Assess and price insurance risks"
            }
        }
    },
    
    # Supporting Operations
    "supporting_operations": {
        "name": "Supporting Operations",
        "description": "Operations that support core business functions",
        "category": DomainCategory.SUPPORTING_OPERATIONS,
        "children": {
            "payment_processing": {
                "name": "Payment Processing",
                "subdomain": BusinessSubdomain.PAYMENT_PROCESSING,
                "keywords": ["payment", "transaction", "billing", "invoice", "receipt", "refund"],
                "patterns": ["*payment*", "*billing*", "*invoice*", "*transaction*"],
                "typical_components": ["PaymentService", "BillingAction", "payment.jsp"],
                "business_purpose": "Process financial transactions and payments"
            },
            "commission_management": {
                "name": "Commission Management", 
                "subdomain": BusinessSubdomain.COMMISSION_MANAGEMENT,
                "keywords": ["commission", "agent", "broker", "compensation", "incentive"],
                "patterns": ["*commission*", "*agent*", "*broker*", "*comp*"],
                "typical_components": ["CommissionService", "AgentAction", "commission.jsp"],
                "business_purpose": "Calculate and manage agent/broker commissions"
            }
        }
    },
    
    # Customer Facing
    "customer_facing": {
        "name": "Customer Facing Services",
        "description": "Direct customer interaction and service functions",
        "category": DomainCategory.CUSTOMER_FACING,
        "children": {
            "customer_management": {
                "name": "Customer Management",
                "subdomain": BusinessSubdomain.CUSTOMER_MANAGEMENT,
                "keywords": ["customer", "client", "member", "contact", "profile", "account"],
                "patterns": ["*customer*", "*client*", "*member*", "*contact*"],
                "typical_components": ["CustomerService", "ContactAction", "customer.jsp"],
                "business_purpose": "Manage customer information and relationships"
            },
            "self_service_portal": {
                "name": "Self Service Portal",
                "subdomain": BusinessSubdomain.SELF_SERVICE_PORTAL,
                "keywords": ["portal", "self", "service", "online", "web", "dashboard"],
                "patterns": ["*portal*", "*dashboard*", "*online*", "*self*"],
                "typical_components": ["PortalService", "DashboardAction", "portal.jsp"],
                "business_purpose": "Enable customer self-service capabilities"
            }
        }
    },
    
    # Infrastructure
    "infrastructure": {
        "name": "Infrastructure Services",
        "description": "Technical infrastructure and system services",
        "category": DomainCategory.INFRASTRUCTURE,
        "children": {
            "authentication": {
                "name": "Authentication & Security",
                "subdomain": BusinessSubdomain.AUTHENTICATION,
                "keywords": ["auth", "login", "security", "credential", "password", "token"],
                "patterns": ["*auth*", "*login*", "*security*", "*credential*"],
                "typical_components": ["AuthService", "LoginAction", "login.jsp"],
                "business_purpose": "Authenticate and authorize system access"
            },
            "workflow_management": {
                "name": "Workflow Management",
                "subdomain": BusinessSubdomain.WORKFLOW_MANAGEMENT,
                "keywords": ["workflow", "approval", "routing", "queue", "task", "process"],
                "patterns": ["*workflow*", "*approval*", "*queue*", "*task*"],
                "typical_components": ["WorkflowService", "ApprovalAction", "workflow.jsp"],
                "business_purpose": "Manage business process workflows"
            },
            "reporting_analytics": {
                "name": "Reporting & Analytics",
                "subdomain": BusinessSubdomain.REPORTING_ANALYTICS,
                "keywords": ["report", "analytics", "dashboard", "metrics", "kpi", "statistics"],
                "patterns": ["*report*", "*analytics*", "*metrics*", "*stats*"],
                "typical_components": ["ReportService", "AnalyticsAction", "report.jsp"],
                "business_purpose": "Generate reports and business analytics"
            }
        }
    },
    
    # Compliance & Governance
    "compliance_governance": {
        "name": "Compliance & Governance",
        "description": "Regulatory compliance and governance functions",
        "category": DomainCategory.COMPLIANCE_GOVERNANCE,
        "children": {
            "regulatory_compliance": {
                "name": "Regulatory Compliance",
                "subdomain": BusinessSubdomain.REGULATORY_COMPLIANCE,
                "keywords": ["compliance", "regulatory", "sox", "gdpr", "audit", "regulation"],
                "patterns": ["*compliance*", "*regulatory*", "*audit*", "*sox*"],
                "typical_components": ["ComplianceService", "AuditAction", "compliance.jsp"],
                "regulatory_scope": ["SOX", "GDPR", "HIPAA", "PCI-DSS"],
                "business_purpose": "Ensure regulatory compliance and governance"
            },
            "audit_trail": {
                "name": "Audit Trail",
                "subdomain": BusinessSubdomain.AUDIT_TRAIL,
                "keywords": ["audit", "trail", "log", "tracking", "history", "forensic"],
                "patterns": ["*audit*", "*trail*", "*log*", "*tracking*"],
                "typical_components": ["AuditService", "TrailAction", "audit.jsp"],
                "business_purpose": "Maintain audit trails for compliance"
            }
        }
    }
}

# Utility Functions

def load_domain_taxonomy() -> Dict[str, Any]:
    """Load the complete domain taxonomy structure"""
    return ENTERPRISE_DOMAIN_TAXONOMY

def get_domain_keywords(domain_id: str) -> List[str]:
    """Get keywords for a specific domain"""
    taxonomy = load_domain_taxonomy()
    
    def find_domain(data: Dict[str, Any], target_id: str) -> Optional[Dict[str, Any]]:
        if target_id in data:
            return data[target_id]
        
        for key, value in data.items():
            if isinstance(value, dict) and "children" in value:
                result = find_domain(value["children"], target_id)
                if result:
                    return result
        return None
    
    domain = find_domain(taxonomy, domain_id)
    return domain.get("keywords", []) if domain else []

def get_domain_patterns(domain_id: str) -> List[str]:
    """Get file patterns for a specific domain"""
    taxonomy = load_domain_taxonomy()
    
    def find_domain(data: Dict[str, Any], target_id: str) -> Optional[Dict[str, Any]]:
        if target_id in data:
            return data[target_id]
        
        for key, value in data.items():
            if isinstance(value, dict) and "children" in value:
                result = find_domain(value["children"], target_id)
                if result:
                    return result
        return None
    
    domain = find_domain(taxonomy, domain_id)
    return domain.get("patterns", []) if domain else []

def get_all_domain_ids() -> List[str]:
    """Get all domain IDs from taxonomy"""
    taxonomy = load_domain_taxonomy()
    domain_ids = []
    
    def extract_ids(data: Dict[str, Any]):
        for key, value in data.items():
            domain_ids.append(key)
            if isinstance(value, dict) and "children" in value:
                extract_ids(value["children"])
    
    extract_ids(taxonomy)
    return domain_ids