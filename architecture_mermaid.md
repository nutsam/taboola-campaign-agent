flowchart TD
    A[User Interface: Chat/Input] -->|User Message| B[Conversation Manager: State Tracking & Routing]
    A <-->|Iterative Feedback| B
    B -->|Collect Inputs| D[Data Processor: Validate & Store Inputs e.g., URL, CPA, Budget]
    B -->|Optimization Request| E[Optimization Suggestion Engine: ML/Analytics for Campaign Suggestions]
    B -->|Migration Request| F[Migration Module: Import, Map Fields via Platform Adapter]
    B -->|Error Feedback| I[Error Handler: Manage Invalid Inputs, API Errors]
    D -->|Store Session Data| J[Session Storage: Temporary User Data]
    D -->|Query Historical Data| G
    E -->|Fetch Similar Campaigns| G[Databases/APIs: Taboola DB, Historical Campaigns, External APIs e.g., Facebook]
    F -->|Import Data| G
    E -->|Suggestions| H[Response Generator: Natural Language Output]
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
        I
        J
    end
    subgraph "External Integrations"
        G
    end