# Complete System Flow Diagram - Agentic AI Log Analysis Integration

## End-to-End Log Analysis Flow

```mermaid
graph TB
    subgraph "Log Sources"
        ECS_PROD[ECS Containers<br/>us-east-1 PROD]
        ECS_UAT[ECS Containers<br/>us-east-2 UAT]
        AKS_PROD[AKS PROD Cluster]
        AKS_UAT[AKS UAT Cluster]
    end

    subgraph "Log Collection Layer"
        CW[AWS CloudWatch<br/>/ecs/myapp]
        PYTHON_PROD[Python Script<br/>fetch-aks-prod-logs.py]
        PYTHON_UAT[Python Script<br/>fetch-aks-uat-logs.py]
        FILES_PROD[Local Files<br/>/var/log/aks-logs-prod]
        FILES_UAT[Local Files<br/>/var/log/aks-logs-uat]
    end

    subgraph "Filebeat Agent"
        FB[Filebeat<br/>- CloudWatch Input<br/>- File Input<br/>scan: 10s]
    end

    subgraph "Elasticsearch Cluster"
        ES[(Elasticsearch<br/>elasticsearch:9200)]
        IDX1[ecs-logs-prod-*]
        IDX2[ecs-logs-uat-*]
        IDX3[aks-logs-prod-*]
        IDX4[aks-logs-uat-*]
    end

    subgraph "Agentic AI Log Analysis System"
        ORCH[Orchestrator<br/>- Scheduled Daily<br/>- Manual Trigger]
        
        subgraph "Agent Pipeline"
            LF[Log Fetcher Agent<br/>Query ES with filters]
            EP[Error Parser Agent<br/>Classify & Group]
            RCA[RCA Analyzer Agent<br/>Root Cause Analysis]
            SG[Solution Generator Agent<br/>AI-Powered Solutions]
            EM[Email Sender Agent<br/>SMTP Alerts]
        end
    end

    subgraph "AI Provider"
        OPENAI[OpenAI GPT-4<br/>Intelligent Analysis]
    end

    subgraph "Alerting"
        EMAIL[Email Recipients<br/>team@company.com<br/>oncall@company.com]
    end

    subgraph "Monitoring"
        KIBANA[Kibana UI<br/>Visualization]
        LOGS[Structured Logs<br/>logs/analysis.log]
        RESULTS[Analysis Results<br/>results/*.json]
    end

    %% ECS Flow
    ECS_PROD --> CW
    ECS_UAT --> CW
    CW -->|Direct Read| FB

    %% AKS Flow
    AKS_PROD --> PYTHON_PROD
    AKS_UAT --> PYTHON_UAT
    PYTHON_PROD --> FILES_PROD
    PYTHON_UAT --> FILES_UAT
    FILES_PROD --> FB
    FILES_UAT --> FB

    %% Filebeat to Elasticsearch
    FB --> ES
    ES --> IDX1
    ES --> IDX2
    ES --> IDX3
    ES --> IDX4

    %% Elasticsearch to Kibana
    ES --> KIBANA

    %% Agentic AI Flow
    ORCH -->|Trigger| LF
    IDX1 -.->|Query| LF
    IDX2 -.->|Query| LF
    IDX3 -.->|Query| LF
    IDX4 -.->|Query| LF
    
    LF -->|Raw Logs| EP
    EP -->|Classified Errors| RCA
    RCA <-->|AI Analysis| OPENAI
    RCA -->|Root Causes| SG
    SG <-->|Solution Gen| OPENAI
    SG -->|Solutions| EM
    EM -->|SMTP| EMAIL

    %% Monitoring
    ORCH --> LOGS
    ORCH --> RESULTS

    style ORCH fill:#4CAF50,stroke:#2E7D32,color:#fff
    style LF fill:#2196F3,stroke:#1565C0,color:#fff
    style EP fill:#2196F3,stroke:#1565C0,color:#fff
    style RCA fill:#2196F3,stroke:#1565C0,color:#fff
    style SG fill:#2196F3,stroke:#1565C0,color:#fff
    style EM fill:#2196F3,stroke:#1565C0,color:#fff
    style OPENAI fill:#FF9800,stroke:#E65100,color:#fff
    style ES fill:#00BCD4,stroke:#006064,color:#fff
    style EMAIL fill:#F44336,stroke:#B71C1C,color:#fff
```

---

## Detailed Agent Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant LogFetcher
    participant Elasticsearch
    participant ErrorParser
    participant RCAAnalyzer
    participant OpenAI
    participant SolutionGen
    participant EmailSender
    participant SMTP

    User->>Orchestrator: Trigger Analysis<br/>(Scheduled or Manual)
    
    activate Orchestrator
    Orchestrator->>LogFetcher: fetch_logs(hours=24)
    
    activate LogFetcher
    LogFetcher->>Elasticsearch: Query indices<br/>(ecs-logs-*, aks-logs-*)
    Elasticsearch-->>LogFetcher: Return logs (ECS format)
    LogFetcher->>LogFetcher: Normalize to internal format
    LogFetcher-->>Orchestrator: Normalized logs
    deactivate LogFetcher
    
    Orchestrator->>ErrorParser: parse_logs(logs)
    
    activate ErrorParser
    ErrorParser->>ErrorParser: Classify errors<br/>(App/Infra/Security/Perf)
    ErrorParser->>ErrorParser: Group related errors
    ErrorParser->>ErrorParser: Detect patterns
    ErrorParser-->>Orchestrator: Classified errors + patterns
    deactivate ErrorParser
    
    Orchestrator->>RCAAnalyzer: analyze(error_groups, patterns)
    
    activate RCAAnalyzer
    RCAAnalyzer->>RCAAnalyzer: Temporal correlation
    RCAAnalyzer->>RCAAnalyzer: Service dependency analysis
    RCAAnalyzer->>OpenAI: AI-powered RCA request
    OpenAI-->>RCAAnalyzer: Root cause analysis
    RCAAnalyzer-->>Orchestrator: RCA results + confidence
    deactivate RCAAnalyzer
    
    Orchestrator->>SolutionGen: generate_solutions(rca_result)
    
    activate SolutionGen
    SolutionGen->>OpenAI: Generate remediation steps
    OpenAI-->>SolutionGen: Solution recommendations
    SolutionGen->>SolutionGen: Add preventive measures
    SolutionGen-->>Orchestrator: Complete solutions
    deactivate SolutionGen
    
    Orchestrator->>EmailSender: send_alert(analysis_result)
    
    activate EmailSender
    EmailSender->>EmailSender: Format HTML email
    EmailSender->>SMTP: Send email alert
    SMTP-->>EmailSender: Delivery confirmation
    EmailSender-->>Orchestrator: Email sent
    deactivate EmailSender
    
    Orchestrator->>Orchestrator: Save results to JSON
    Orchestrator-->>User: Analysis complete
    deactivate Orchestrator
```

---

## Data Flow Through Agents

```mermaid
graph LR
    subgraph "Input"
        RAW[Raw Logs from ES<br/>- ECS format<br/>- Multiple indices<br/>- Time filtered]
    end

    subgraph "Stage 1: Fetch"
        FETCH[Log Fetcher<br/>━━━━━━━━━━<br/>• Query ES<br/>• Pagination<br/>• Normalize]
        NORM[Normalized Logs<br/>━━━━━━━━━━<br/>timestamp, message,<br/>service, error_type]
    end

    subgraph "Stage 2: Parse"
        PARSE[Error Parser<br/>━━━━━━━━━━<br/>• Classify<br/>• Group<br/>• Detect patterns]
        CLASS[Classified Data<br/>━━━━━━━━━━<br/>error_groups,<br/>patterns,<br/>statistics]
    end

    subgraph "Stage 3: Analyze"
        ANALYZE[RCA Analyzer<br/>━━━━━━━━━━<br/>• Correlate<br/>• AI analysis<br/>• Rank causes]
        CAUSES[Root Causes<br/>━━━━━━━━━━<br/>causes,<br/>confidence,<br/>evidence]
    end

    subgraph "Stage 4: Solve"
        SOLVE[Solution Generator<br/>━━━━━━━━━━<br/>• AI solutions<br/>• Rule-based<br/>• Risk assess]
        SOL[Solutions<br/>━━━━━━━━━━<br/>actions,<br/>preventive,<br/>verification]
    end

    subgraph "Stage 5: Alert"
        ALERT[Email Sender<br/>━━━━━━━━━━<br/>• Format HTML<br/>• SMTP send<br/>• Retry logic]
        SENT[Email Alert<br/>━━━━━━━━━━<br/>Errors + RCA<br/>+ Solutions]
    end

    RAW --> FETCH
    FETCH --> NORM
    NORM --> PARSE
    PARSE --> CLASS
    CLASS --> ANALYZE
    ANALYZE --> CAUSES
    CAUSES --> SOLVE
    SOLVE --> SOL
    SOL --> ALERT
    ALERT --> SENT

    style FETCH fill:#2196F3,stroke:#1565C0,color:#fff
    style PARSE fill:#2196F3,stroke:#1565C0,color:#fff
    style ANALYZE fill:#2196F3,stroke:#1565C0,color:#fff
    style SOLVE fill:#2196F3,stroke:#1565C0,color:#fff
    style ALERT fill:#2196F3,stroke:#1565C0,color:#fff
```

---

## Index Pattern Filtering

```mermaid
graph TD
    subgraph "Elasticsearch Indices"
        ALL[All Indices<br/>*-logs-*]
        
        ECS_ALL[ECS Logs<br/>ecs-logs-*]
        ECS_PROD[ecs-logs-prod-*]
        ECS_UAT[ecs-logs-uat-*]
        
        AKS_ALL[AKS Logs<br/>aks-logs-*]
        AKS_PROD[aks-logs-prod-*]
        AKS_UAT[aks-logs-uat-*]
    end

    subgraph "Analysis Options"
        OPT1[Option 1:<br/>Analyze Everything]
        OPT2[Option 2:<br/>Only ECS]
        OPT3[Option 3:<br/>Only AKS]
        OPT4[Option 4:<br/>Only Production]
        OPT5[Option 5:<br/>Only UAT]
    end

    ALL --> OPT1
    ECS_ALL --> OPT2
    AKS_ALL --> OPT3
    
    ECS_PROD --> OPT4
    AKS_PROD --> OPT4
    
    ECS_UAT --> OPT5
    AKS_UAT --> OPT5

    style ALL fill:#4CAF50,stroke:#2E7D32,color:#fff
    style OPT1 fill:#FF9800,stroke:#E65100,color:#fff
    style OPT2 fill:#2196F3,stroke:#1565C0,color:#fff
    style OPT3 fill:#2196F3,stroke:#1565C0,color:#fff
    style OPT4 fill:#9C27B0,stroke:#4A148C,color:#fff
    style OPT5 fill:#9C27B0,stroke:#4A148C,color:#fff
```

---

## Execution Modes

```mermaid
graph TB
    subgraph "Scheduled Mode"
        SCHED[Daily Schedule<br/>Default: 02:00 AM]
        SCHED --> AUTO[Automatic Trigger]
        AUTO --> ANALYZE1[Analyze Last 24h]
        ANALYZE1 --> EMAIL1[Send Email Alert]
        EMAIL1 --> WAIT[Wait for Next Day]
        WAIT --> AUTO
    end

    subgraph "Manual Mode"
        MANUAL[Manual Trigger<br/>On-Demand]
        MANUAL --> CUSTOM[Custom Parameters]
        CUSTOM --> TIME[Time Range]
        CUSTOM --> SERVICE[Service Filter]
        CUSTOM --> SEVERITY[Severity Filter]
        TIME --> ANALYZE2[Run Analysis]
        SERVICE --> ANALYZE2
        SEVERITY --> ANALYZE2
        ANALYZE2 --> EMAIL2[Send Email Alert]
        EMAIL2 --> DONE[Complete]
    end

    style SCHED fill:#4CAF50,stroke:#2E7D32,color:#fff
    style MANUAL fill:#2196F3,stroke:#1565C0,color:#fff
```

---

## Configuration Flow

```mermaid
graph LR
    subgraph "Environment Variables"
        ENV[.env File<br/>━━━━━━━━━━<br/>ES_HOST<br/>ES_PORT<br/>OPENAI_API_KEY<br/>SMTP_HOST]
    end

    subgraph "YAML Configs"
        ES_YAML[elasticsearch.yaml<br/>━━━━━━━━━━<br/>Field mappings<br/>Query settings]
        AI_YAML[ai.yaml<br/>━━━━━━━━━━<br/>Model config<br/>Prompts]
        SMTP_YAML[smtp.yaml<br/>━━━━━━━━━━<br/>Email template<br/>Recipients]
    end

    subgraph "Runtime"
        AGENTS[Agents<br/>━━━━━━━━━━<br/>Load configs<br/>Initialize]
    end

    ENV --> ES_YAML
    ENV --> AI_YAML
    ENV --> SMTP_YAML
    
    ES_YAML --> AGENTS
    AI_YAML --> AGENTS
    SMTP_YAML --> AGENTS

    style ENV fill:#FF9800,stroke:#E65100,color:#fff
    style AGENTS fill:#4CAF50,stroke:#2E7D32,color:#fff
```

---

## Error Handling & Retry Flow

```mermaid
graph TD
    START[Agent Execution]
    START --> TRY[Try Operation]
    TRY --> SUCCESS{Success?}
    
    SUCCESS -->|Yes| NEXT[Continue to Next Stage]
    SUCCESS -->|No| CHECK{Retries<br/>Remaining?}
    
    CHECK -->|Yes| WAIT[Wait<br/>Exponential Backoff]
    WAIT --> RETRY[Retry Operation]
    RETRY --> TRY
    
    CHECK -->|No| FALLBACK{Fallback<br/>Available?}
    FALLBACK -->|Yes| USE_FALLBACK[Use Fallback<br/>e.g., Rule-based]
    FALLBACK -->|No| LOG_ERROR[Log Error]
    
    USE_FALLBACK --> NEXT
    LOG_ERROR --> DEGRADE[Graceful Degradation]
    DEGRADE --> NEXT

    style SUCCESS fill:#4CAF50,stroke:#2E7D32,color:#fff
    style CHECK fill:#FF9800,stroke:#E65100,color:#fff
    style FALLBACK fill:#2196F3,stroke:#1565C0,color:#fff
    style LOG_ERROR fill:#F44336,stroke:#B71C1C,color:#fff
```

---

## Summary

This system provides:

1. **Unified Analysis** across ECS and AKS logs
2. **Flexible Filtering** by environment, service, time
3. **AI-Powered Intelligence** with rule-based fallback
4. **Automated Alerting** via email
5. **Production-Ready** error handling and retry logic
6. **Comprehensive Logging** for observability
