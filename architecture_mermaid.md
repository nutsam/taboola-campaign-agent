flowchart TD
    A[User Interface: Chat/Input] -->|User Message| B[Conversation Manager: State Tracking & Routing]
    A <-->|Iterative Feedback| B
    A -->|File Upload| FP[File Processor: CSV/JSON/Excel Processing & Schema Validation]
    FP -->|Processed Campaign Data| F[Migration Module: Import, Map Fields via Platform Adapter]
    FP -->|Validation Results| H[Response Generator: Natural Language Output]
    B -->|Collect Inputs| D[Data Processor: Validate & Store Inputs e.g., URL, CPA, Budget]
    B -->|Optimization Request| E[Optimization Suggestion Engine: ML/Analytics for Campaign Suggestions]
    B -->|Migration Request| F
    B -->|Error Feedback| I[Error Handler: Manage Invalid Inputs, API Errors]
    D -->|Store Session Data| J[Session Storage: Temporary User Data]
    D -->|Query Historical Data| G
    E -->|Fetch Similar Campaigns| G[Databases/APIs: Taboola DB, Historical Campaigns, External APIs e.g., Facebook]
    F -->|Import Data| G
    E -->|Suggestions| H
    F -->|Migration Results| H
    D -->|Processed Data| H
    I -->|Error Messages| H
    B -->|Direct Feedback| H
    H -->|Response| A
    subgraph "Core AI Logic"
        B
        D
        E
        F
        FP
        I
        J
    end
    subgraph "External Integrations"
        G
    end