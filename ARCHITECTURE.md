# 🍔 deburger - Architecture Design

**Version:** 2.0 (Cloud Cost Analyzer)  
**Last Updated:** 2026-05-21

## 🎯 Vision

deburger prevents expensive code from reaching production by analyzing code changes and predicting cloud costs BEFORE deployment. Multi-cloud support (AWS, GCP, Azure), multi-language (Python, JavaScript, Go), production-ready.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Developer Workflow                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Git Hook (Entry Point)                   │
│  • Pre-commit / Pre-push                                     │
│  • Triggers analysis on changed files                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     CLI Interface Layer                      │
│  deburger check / diff / optimize / watch                    │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────────┐  ┌─────────────┐
│  Code        │  │  Cost            │  │  Config     │
│  Analyzer    │  │  Calculator      │  │  Manager    │
│              │  │                  │  │             │
│ • AST Parse  │  │ • Pricing APIs   │  │ • Load YAML │
│ • Pattern    │  │ • Cost Models    │  │ • Validate  │
│   Detection  │  │ • Multi-cloud    │  │ • Env Vars  │
└──────────────┘  └──────────────────┘  └─────────────┘
        │                   │
        └───────────┬───────┘
                    ▼
        ┌───────────────────────┐
        │  Cloud Provider       │
        │  Plugin System        │
        │                       │
        │  ┌─────┐ ┌─────┐     │
        │  │ AWS │ │ GCP │ ... │
        │  └─────┘ └─────┘     │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Optimization Engine  │
        │  • Generate Fixes     │
        │  • Calculate Savings  │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Storage Layer        │
        │  • SQLite (local)     │
        │  • PostgreSQL (opt)   │
        └───────────────────────┘
```

---

## 📦 Core Components

### 1. Code Analyzer Engine

**Purpose:** Analyze source code to detect expensive patterns

**Technology:** AST-based parsing (not regex)

**Supported Languages:**
- Python: `ast` module
- JavaScript/TypeScript: `@babel/parser` or `esprima`
- Go: `go/parser` package

**Detects:**
```python
# N+1 Query Detection
for item in items:
    db.get(item.id)  # ❌ Expensive!

# Sequential Async
await fetch1()
await fetch2()  # ❌ Should be parallel

# Over-provisioning
Lambda(memory=1024)  # ❌ Uses only 200MB
```

**Interface:**
```python
class CodeAnalyzer:
    def analyze(self, file_path: str, language: str) -> List[Issue]:
        """Analyze code and return detected issues"""
        
    def parse_ast(self, code: str, language: str) -> AST:
        """Parse code into AST"""
        
    def detect_patterns(self, ast: AST) -> List[Pattern]:
        """Find expensive patterns in AST"""
```

---

### 2. Cloud Provider Plugin System

**Purpose:** Pluggable architecture for different cloud providers

**Design Pattern:** Plugin architecture with abstract base class

**Structure:**
```python
# Base class
class CloudProvider(ABC):
    name: str  # "aws", "gcp", "azure"
    
    @abstractmethod
    async def calculate_cost(self, resource: Resource) -> Cost:
        """Calculate cost for a resource"""
    
    @abstractmethod
    async def get_pricing(self, region: str) -> PricingData:
        """Fetch current pricing from provider API"""
    
    @abstractmethod
    def optimize(self, issue: Issue) -> Optimization:
        """Generate optimization suggestion"""

# Concrete implementations
class AWSProvider(CloudProvider):
    name = "aws"
    
    def calculate_cost(self, resource):
        # AWS-specific logic
        if resource.type == "lambda":
            return self._calc_lambda_cost(resource)
        elif resource.type == "rds":
            return self._calc_rds_cost(resource)
        
class GCPProvider(CloudProvider):
    name = "gcp"
    # GCP-specific implementation

class AzureProvider(CloudProvider):
    name = "azure"
    # Azure-specific implementation
```

**Plugin Registry:**
```python
class PluginRegistry:
    _providers: Dict[str, CloudProvider] = {}
    
    @classmethod
    def register(cls, provider: CloudProvider):
        cls._providers[provider.name] = provider
    
    @classmethod
    def get(cls, name: str) -> CloudProvider:
        return cls._providers[name]
```

---

### 3. Cost Calculation Engine

**Purpose:** Calculate actual costs from code patterns

**Pricing Data Sources:**
- AWS: AWS Price List API
- GCP: Google Cloud Billing API  
- Azure: Azure Rate Card API

**Caching Strategy:**
- Fetch pricing daily (prices don't change often)
- Store in local SQLite cache
- Configurable refresh interval

**Cost Models:**

```python
@dataclass
class CostBreakdown:
    resource_type: str  # "lambda", "rds", "storage"
    base_cost: Decimal
    usage_cost: Decimal
    data_transfer_cost: Decimal
    total: Decimal
    currency: str = "USD"
    period: str = "monthly"

class CostCalculator:
    def __init__(self, provider: CloudProvider):
        self.provider = provider
        self.pricing_cache = PricingCache()
    
    async def calculate(
        self, 
        resource: Resource,
        traffic: TrafficEstimate
    ) -> CostBreakdown:
        """Calculate total cost for resource"""
        
        pricing = await self.pricing_cache.get(
            provider=self.provider.name,
            region=resource.region,
            resource_type=resource.type
        )
        
        # Calculate based on usage
        if resource.type == "lambda":
            return self._calc_lambda(resource, pricing, traffic)
        elif resource.type == "database":
            return self._calc_database(resource, pricing, traffic)
        # ...
```

**Traffic Estimation:**
```python
@dataclass
class TrafficEstimate:
    requests_per_day: int
    avg_response_time_ms: int
    peak_multiplier: float = 3.0
    
    @property
    def monthly_requests(self) -> int:
        return self.requests_per_day * 30
    
    @property
    def peak_requests_per_second(self) -> float:
        return (self.requests_per_day / 86400) * self.peak_multiplier
```

---

### 4. Optimization Suggestion Engine

**Purpose:** Generate fix suggestions and calculate savings

**Approach:**
1. Detect issue pattern
2. Generate code fix
3. Calculate cost before/after
4. Show savings

**Example:**

```python
class OptimizationEngine:
    def generate_fix(self, issue: Issue) -> Optimization:
        if issue.type == "n_plus_one_query":
            return self._fix_n_plus_one(issue)
        elif issue.type == "sequential_async":
            return self._fix_sequential_async(issue)
        # ...
    
    def _fix_n_plus_one(self, issue: Issue) -> Optimization:
        # Parse code
        tree = ast.parse(issue.code)
        
        # Find the loop
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Generate optimized query
                optimized = self._generate_bulk_query(node)
                
                return Optimization(
                    issue=issue,
                    original_code=issue.code,
                    fixed_code=optimized,
                    explanation="Replaced N+1 queries with single bulk query",
                    savings_monthly=Decimal("8400.00"),
                    confidence=0.95
                )
```

---

### 5. Configuration System

**No hardcoded values - everything configurable**

**Configuration Hierarchy:**
1. Default config (in code)
2. Global config (~/.deburger/config.yml)
3. Project config (.deburger.yml)
4. Environment variables
5. CLI arguments

**Configuration Schema:**

```yaml
# .deburger.yml
version: "2.0"

# Cloud provider configuration
providers:
  aws:
    enabled: true
    region: us-east-1
    profile: default  # AWS CLI profile
    pricing_region: us-east-1
    
  gcp:
    enabled: false
    project_id: ${GCP_PROJECT_ID}
    region: us-central1
    
  azure:
    enabled: false
    subscription_id: ${AZURE_SUBSCRIPTION_ID}
    region: eastus

# Cost thresholds
budget:
  monthly_limit: 10000  # USD
  alert_threshold: 0.8  # Alert at 80%
  block_threshold: 1.0  # Block at 100%
  
  # Per-deployment limits
  deployment:
    max_increase_dollars: 500
    max_increase_percent: 20

# Traffic estimates (for cost calculation)
traffic:
  requests_per_day: 100000
  avg_response_time_ms: 200
  peak_multiplier: 3.0

# Analysis settings
analysis:
  languages:
    - python
    - javascript
    - typescript
    - go
  
  ignore_patterns:
    - "node_modules/**"
    - "venv/**"
    - "*.test.js"
    - "test_*.py"
  
  # Which issues to detect
  detect:
    n_plus_one_queries: true
    sequential_async: true
    over_provisioned_resources: true
    missing_caching: true
    large_responses: true

# Git hook behavior
hooks:
  pre_commit:
    enabled: true
    block_on_exceed: true
    show_fixes: true
  
  pre_push:
    enabled: true
    require_approval: true

# Optimization settings
optimize:
  auto_apply: false  # Require confirmation
  create_branch: true  # Create optimization branch
  run_tests_after: true

# Team settings
team:
  enable_leaderboard: true
  track_per_developer: true
  
# Storage
storage:
  backend: sqlite  # or "postgresql"
  path: ~/.deburger/data.db
  
  # Optional PostgreSQL
  postgresql:
    host: ${DB_HOST}
    port: 5432
    database: deburger
    user: ${DB_USER}
    password: ${DB_PASSWORD}

# Logging
logging:
  level: INFO
  file: ~/.deburger/logs/deburger.log
  rotation: 10MB
```

**Config Validation:**
```python
from pydantic import BaseSettings, Field, validator

class CloudProviderConfig(BaseModel):
    enabled: bool = False
    region: str
    
class AWSConfig(CloudProviderConfig):
    profile: Optional[str] = "default"
    pricing_region: str = "us-east-1"

class BudgetConfig(BaseModel):
    monthly_limit: Decimal = Field(gt=0)
    alert_threshold: float = Field(ge=0, le=1)
    block_threshold: float = Field(ge=0, le=1)
    
    class DeploymentLimits(BaseModel):
        max_increase_dollars: Decimal
        max_increase_percent: float
    
    deployment: DeploymentLimits

class Config(BaseSettings):
    version: str = "2.0"
    providers: Dict[str, CloudProviderConfig]
    budget: BudgetConfig
    # ...
    
    @validator('version')
    def check_version(cls, v):
        if v != "2.0":
            raise ValueError(f"Unsupported config version: {v}")
        return v
    
    class Config:
        env_file = ".env"
        env_prefix = "DEBURGER_"
```

---

### 6. Storage Layer

**Purpose:** Track costs, history, and developer stats

**Database Schema:**

```sql
-- Cost tracking
CREATE TABLE deployments (
    id UUID PRIMARY KEY,
    commit_hash VARCHAR(40) NOT NULL,
    branch VARCHAR(255),
    author VARCHAR(255),
    timestamp TIMESTAMPTZ NOT NULL,
    provider VARCHAR(20),  -- aws, gcp, azure
    
    -- Costs
    estimated_monthly_cost DECIMAL(10,2),
    previous_monthly_cost DECIMAL(10,2),
    cost_increase DECIMAL(10,2),
    
    -- Metadata
    files_changed INT,
    issues_detected INT,
    optimizations_applied INT,
    blocked BOOLEAN DEFAULT FALSE,
    
    UNIQUE(commit_hash, provider)
);

CREATE INDEX idx_deployments_timestamp ON deployments(timestamp);
CREATE INDEX idx_deployments_author ON deployments(author);

-- Individual issues
CREATE TABLE issues (
    id UUID PRIMARY KEY,
    deployment_id UUID REFERENCES deployments(id),
    
    file_path TEXT NOT NULL,
    line_number INT,
    issue_type VARCHAR(50),  -- n_plus_one, sequential_async, etc.
    severity VARCHAR(20),    -- low, medium, high, critical
    
    -- Cost impact
    estimated_monthly_cost DECIMAL(10,2),
    
    -- Code
    original_code TEXT,
    fixed_code TEXT,
    
    -- Status
    status VARCHAR(20),  -- detected, fixed, ignored
    applied_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_issues_deployment ON issues(deployment_id);
CREATE INDEX idx_issues_type ON issues(issue_type);

-- Savings tracking
CREATE TABLE optimizations (
    id UUID PRIMARY KEY,
    issue_id UUID REFERENCES issues(id),
    deployment_id UUID REFERENCES deployments(id),
    
    type VARCHAR(50),
    savings_monthly DECIMAL(10,2),
    applied_by VARCHAR(255),
    applied_at TIMESTAMPTZ,
    
    verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMPTZ
);

-- Developer leaderboard
CREATE TABLE developer_stats (
    developer VARCHAR(255) PRIMARY KEY,
    total_savings DECIMAL(12,2) DEFAULT 0,
    deployments_count INT DEFAULT 0,
    issues_fixed INT DEFAULT 0,
    rank INT,
    
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Pricing cache
CREATE TABLE pricing_cache (
    provider VARCHAR(20),
    region VARCHAR(50),
    resource_type VARCHAR(50),
    pricing_data JSONB,
    
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    PRIMARY KEY (provider, region, resource_type)
);
```

**Repository Pattern:**

```python
class DeploymentRepository:
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, deployment: Deployment) -> UUID:
        """Save deployment record"""
        
    async def get(self, id: UUID) -> Deployment:
        """Get deployment by ID"""
        
    async def get_by_commit(self, commit: str) -> Optional[Deployment]:
        """Find deployment by commit hash"""
        
    async def get_history(
        self, 
        author: Optional[str] = None,
        limit: int = 100
    ) -> List[Deployment]:
        """Get deployment history"""

class IssueRepository:
    async def create_batch(self, issues: List[Issue]) -> List[UUID]:
        """Bulk create issues"""
        
    async def get_by_deployment(self, deployment_id: UUID) -> List[Issue]:
        """Get all issues for deployment"""
        
    async def mark_fixed(self, issue_id: UUID, fixed_code: str):
        """Mark issue as fixed"""

class StatsRepository:
    async def update_developer_stats(self, developer: str):
        """Recalculate developer statistics"""
        
    async def get_leaderboard(self, limit: int = 10) -> List[DeveloperStats]:
        """Get top developers by savings"""
```

---

## 🔌 Extension Points

### Custom Analyzers

```python
# Custom analyzer plugin
class CustomAnalyzer(BaseAnalyzer):
    name = "custom_analyzer"
    languages = ["python"]
    
    def detect(self, ast: AST, context: Context) -> List[Issue]:
        # Custom detection logic
        pass

# Register
AnalyzerRegistry.register(CustomAnalyzer())
```

### Custom Cost Models

```python
class CustomCostModel(BaseCostModel):
    def calculate(self, resource: Resource) -> Cost:
        # Custom cost calculation
        pass
```

---

## 🚀 Performance Requirements

**Analysis Speed:**
- Single file: <100ms
- Full codebase (1000 files): <30s
- Git hook: <10s total

**Optimization:**
- Parallel file analysis
- Incremental analysis (only changed files)
- AST caching
- Pricing data caching

**Memory:**
- Max 500MB RAM usage
- Stream large files
- Limit concurrent analysis

---

## 🔒 Security

**Credentials:**
- Never store credentials in config files
- Use environment variables
- Support cloud provider credential chains (AWS profiles, GCP ADC, etc.)
- Optional credential encryption

**Data:**
- All data stored locally by default
- Optional remote PostgreSQL
- No data sent to external services (except cloud pricing APIs)
- Anonymize developer data in exports

---

## 📊 Monitoring & Observability

**Metrics to track:**
- Analysis duration
- Issues detected per deployment
- Savings generated
- False positive rate
- Plugin load times

**Logging:**
- Structured logging (JSON)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Separate log files per component
- Log rotation

---

## 🎯 Success Metrics

**Product Metrics:**
- Average savings per deployment
- False positive rate <10%
- Analysis time <10s for 90% of deployments
- Developer adoption rate

**Business Metrics:**
- Total savings across all users
- Cost prevented (blocked deployments)
- Time saved (auto-optimization)

---

## 🚧 Future Enhancements

**Phase 2:**
- Real-time monitoring (not just pre-commit)
- Web dashboard
- Slack/Discord notifications
- More cloud providers (Cloudflare, DigitalOcean)
- More languages (Rust, Java, Ruby, PHP)

**Phase 3:**
- ML-based cost prediction
- Auto-scaling recommendations
- FinOps reporting
- Multi-team management
- SaaS offering

---

## 📚 Technology Stack

**Core:**
- Python 3.9+ (type hints, async)
- Typer (CLI)
- Rich (terminal UI)
- Pydantic (config validation)
- SQLAlchemy (ORM)

**Analysis:**
- ast (Python parsing)
- esprima / @babel/parser (JS parsing)
- go/parser (Go parsing)

**Cloud SDKs:**
- boto3 (AWS)
- google-cloud-sdk (GCP)
- azure-sdk (Azure)

**Database:**
- SQLite (default)
- PostgreSQL (optional)
- Alembic (migrations)

**Testing:**
- pytest
- pytest-asyncio
- pytest-cov
- hypothesis (property testing)

**CI/CD:**
- GitHub Actions
- Pre-commit hooks

---

## 🏁 Implementation Phases

**Phase 1: MVP (Weeks 1-4)**
- Basic architecture
- AWS support only
- Python analysis only
- Git hook integration
- SQLite storage
- CLI commands

**Phase 2: Multi-cloud (Weeks 5-6)**
- GCP support
- Azure support
- Multi-language (JS, Go)
- Enhanced optimizations

**Phase 3: Production (Weeks 7-8)**
- CI/CD integration
- Comprehensive testing
- Documentation
- Performance optimization

**Phase 4: Scale (Weeks 9+)**
- PostgreSQL support
- Team features
- Web dashboard
- SaaS launch

---

This architecture is:
✅ **Modular** - Easy to extend
✅ **Pluggable** - Support new clouds/languages
✅ **Configurable** - No hardcoded values
✅ **Production-ready** - Proper error handling, logging, testing
✅ **Multi-platform** - Works with AWS, GCP, Azure
✅ **Scalable** - Can handle large codebases

Ready to implement! 🍔
