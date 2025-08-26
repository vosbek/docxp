// DocXP Neo4j Knowledge Graph Initialization Script
// Sets up constraints, indexes, and initial schema for enterprise code analysis

// ====================
// CONSTRAINTS
// ====================

// Unique constraints for node identification
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:CodeEntity) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT repository_id_unique IF NOT EXISTS FOR (n:Repository) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (n:Project) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT file_id_unique IF NOT EXISTS FOR (n:File) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT class_id_unique IF NOT EXISTS FOR (n:Class) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT method_id_unique IF NOT EXISTS FOR (n:Method) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT interface_id_unique IF NOT EXISTS FOR (n:Interface) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT business_rule_id_unique IF NOT EXISTS FOR (n:BusinessRule) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT technology_component_id_unique IF NOT EXISTS FOR (n:TechnologyComponent) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT jsp_page_id_unique IF NOT EXISTS FOR (n:JSPPage) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT struts_action_id_unique IF NOT EXISTS FOR (n:StrutsAction) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT api_endpoint_id_unique IF NOT EXISTS FOR (n:APIEndpoint) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT database_table_id_unique IF NOT EXISTS FOR (n:DatabaseTable) REQUIRE n.id IS UNIQUE;

// ====================
// INDEXES FOR PERFORMANCE
// ====================

// Primary lookup indexes
CREATE INDEX entity_id_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.id);
CREATE INDEX repository_id_index IF NOT EXISTS FOR (n:Repository) ON (n.id);
CREATE INDEX business_rule_id_index IF NOT EXISTS FOR (n:BusinessRule) ON (n.id);
CREATE INDEX technology_component_name_index IF NOT EXISTS FOR (n:TechnologyComponent) ON (n.name);

// Search and analysis indexes
CREATE INDEX file_path_index IF NOT EXISTS FOR (n:File) ON (n.path);
CREATE INDEX file_name_index IF NOT EXISTS FOR (n:File) ON (n.name);
CREATE INDEX class_name_index IF NOT EXISTS FOR (n:Class) ON (n.name);
CREATE INDEX method_name_index IF NOT EXISTS FOR (n:Method) ON (n.name);
CREATE INDEX interface_name_index IF NOT EXISTS FOR (n:Interface) ON (n.name);

// Business analysis indexes
CREATE INDEX business_rule_type_index IF NOT EXISTS FOR (n:BusinessRule) ON (n.rule_type);
CREATE INDEX business_rule_domain_index IF NOT EXISTS FOR (n:BusinessRule) ON (n.domain);

// Technology mapping indexes
CREATE INDEX technology_type_index IF NOT EXISTS FOR (n:TechnologyComponent) ON (n.technology_type);
CREATE INDEX framework_name_index IF NOT EXISTS FOR (n:Framework) ON (n.name);

// Web component indexes
CREATE INDEX jsp_path_index IF NOT EXISTS FOR (n:JSPPage) ON (n.path);
CREATE INDEX struts_action_name_index IF NOT EXISTS FOR (n:StrutsAction) ON (n.action_name);
CREATE INDEX api_endpoint_path_index IF NOT EXISTS FOR (n:APIEndpoint) ON (n.endpoint_path);

// Database schema indexes
CREATE INDEX database_table_name_index IF NOT EXISTS FOR (n:DatabaseTable) ON (n.table_name);
CREATE INDEX database_schema_index IF NOT EXISTS FOR (n:DatabaseTable) ON (n.schema_name);

// Temporal indexes for change tracking
CREATE INDEX created_at_index IF NOT EXISTS FOR (n) ON (n.created_at);
CREATE INDEX updated_at_index IF NOT EXISTS FOR (n) ON (n.updated_at);

// Pattern analysis indexes
CREATE INDEX pattern_type_index IF NOT EXISTS FOR (n:CodeEntity) ON (n.pattern_type);
CREATE INDEX complexity_score_index IF NOT EXISTS FOR (n) ON (n.complexity_score);

// ====================
// INITIAL SCHEMA VALIDATION
// ====================

// Create a test node to validate schema
MERGE (test:SystemStatus {id: 'schema_initialized'})
SET test.initialized_at = datetime(),
    test.version = '1.0.0',
    test.description = 'DocXP Knowledge Graph Schema Initialized'
RETURN test.initialized_at as initialization_time;

// ====================
// UTILITY PROCEDURES (if APOC is available)
// ====================

// Note: These procedures require APOC plugin
// Uncomment if APOC is installed and configured

/*
// Create procedure to batch import nodes
CALL apoc.periodic.iterate(
  "UNWIND range(1,1000) as id RETURN id",
  "CREATE (:TestNode {id: id})",
  {batchSize:100, parallel:true}
);

// Create procedure to analyze graph statistics
CALL apoc.meta.stats() YIELD labels, relTypesCount, nodeCount, relCount
RETURN labels, relTypesCount, nodeCount, relCount;
*/

// ====================
// VERIFICATION QUERIES
// ====================

// Verify constraints were created
SHOW CONSTRAINTS;

// Verify indexes were created
SHOW INDEXES;

// Display schema overview
CALL db.schema.visualization();

// ====================
// SAMPLE DATA STRUCTURE (for reference)
// ====================

/*
// Example of expected node structure:

(:Repository {
  id: "repo_123",
  name: "legacy-banking-system",
  url: "https://github.com/company/legacy-banking-system",
  language: "Java",
  framework: "Struts",
  created_at: datetime(),
  analysis_status: "pending"
})

(:Class {
  id: "class_AccountService",
  name: "AccountService",
  package: "com.bank.service",
  file_path: "/src/main/java/com/bank/service/AccountService.java",
  methods_count: 15,
  complexity_score: 7.2,
  business_domain: "account_management"
})

(:Method {
  id: "method_withdrawFunds",
  name: "withdrawFunds",
  class_name: "AccountService",
  parameters: ["accountId", "amount"],
  return_type: "TransactionResult",
  complexity_score: 4.1,
  business_rule_type: "validation"
})

(:JSPPage {
  id: "jsp_account_details",
  path: "/WEB-INF/pages/account/details.jsp",
  name: "details.jsp",
  struts_actions: ["viewAccount", "editAccount"],
  business_functions: ["display_account", "edit_account"]
})

(:StrutsAction {
  id: "action_AccountDetailsAction",
  action_name: "viewAccount",
  class_name: "AccountDetailsAction",
  forward_mappings: {
    "success": "/WEB-INF/pages/account/details.jsp",
    "error": "/WEB-INF/pages/error.jsp"
  },
  business_process: "account_inquiry"
})
*/