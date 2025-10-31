# Transcription Workflow

This flowchart details the complete transcription process in Shrutik, including task assignment, transcription submission, consensus building, and quality control.

## 📝 Complete Transcription Process

```mermaid
flowchart TD
    START([User Requests Transcription Task]) --> AUTH{User Authenticated?}
    
    AUTH -->|No| LOGIN[Redirect to Login]
    LOGIN --> AUTH
    AUTH -->|Yes| REQ_TASK[Request Transcription Task]
    
    REQ_TASK --> TASK_PARAMS[Specify Task Parameters]
    TASK_PARAMS --> FIND_CHUNKS[Find Available Chunks]
    
    FIND_CHUNKS --> FILTER[Apply Filters]
    FILTER --> EXCLUDE[Exclude User's Previous Work]
    EXCLUDE --> AVAILABLE{Chunks Available?}
    
    AVAILABLE -->|No| NO_CHUNKS[No Chunks Available]
    NO_CHUNKS --> SUGGEST[Suggest Alternatives]
    SUGGEST --> END_NO_WORK([End - No Work])
    
    AVAILABLE -->|Yes| SELECT[Select Random Chunks]
    SELECT --> CREATE_SESSION[Create Transcription Session]
    CREATE_SESSION --> LOAD_AUDIO[Load Audio Files]
    
    LOAD_AUDIO --> OPTIMIZE[Optimize Audio Delivery]
    OPTIMIZE --> PRESENT[Present Chunks to User]
    
    PRESENT --> USER_WORK[User Transcribes Audio]
    USER_WORK --> TRANSCRIBE{Transcription Action}
    
    TRANSCRIBE -->|Skip Chunk| SKIP_CHUNK[Record Skip Reason]
    TRANSCRIBE -->|Transcribe| ENTER_TEXT[Enter Transcription Text]
    TRANSCRIBE -->|Submit All| VALIDATE_SUBMISSION[Validate Submission]
    
    SKIP_CHUNK --> UPDATE_SKIP[Update Skip Metadata]
    UPDATE_SKIP --> NEXT_CHUNK{More Chunks?}
    
    ENTER_TEXT --> QUALITY_RATE[Rate Audio Quality]
    QUALITY_RATE --> CONFIDENCE[Set Confidence Level]
    CONFIDENCE --> SAVE_DRAFT[Save Draft Locally]
    SAVE_DRAFT --> NEXT_CHUNK
    
    NEXT_CHUNK -->|Yes| PRESENT
    NEXT_CHUNK -->|No| VALIDATE_SUBMISSION
    
    VALIDATE_SUBMISSION --> CHECK_REQUIRED{Required Fields?}
    CHECK_REQUIRED -->|Missing| SHOW_ERRORS[Show Validation Errors]
    SHOW_ERRORS --> USER_WORK
    
    CHECK_REQUIRED -->|Complete| SUBMIT[Submit Transcriptions]
    SUBMIT --> PROCESS_SUBMISSION[Process Submission]
    
    PROCESS_SUBMISSION --> VALIDATE_SESSION{Valid Session?}
    VALIDATE_SESSION -->|No| SESSION_ERROR[Session Error]
    SESSION_ERROR --> ERROR_RECOVERY[Error Recovery]
    
    VALIDATE_SESSION -->|Yes| CHECK_DUPLICATES{Check Duplicates}
    CHECK_DUPLICATES -->|Found| DUPLICATE_ERROR[Duplicate Error]
    DUPLICATE_ERROR --> ERROR_RECOVERY
    
    CHECK_DUPLICATES -->|None| SAVE_TRANSCRIPTIONS[Save Transcriptions]
    SAVE_TRANSCRIPTIONS --> UPDATE_STATS[Update User Stats]
    UPDATE_STATS --> TRIGGER_CONSENSUS[Trigger Consensus Calculation]
    
    TRIGGER_CONSENSUS --> SUCCESS[Show Success Message]
    SUCCESS --> CLEANUP_SESSION[Cleanup Session]
    CLEANUP_SESSION --> NEXT_ACTION{User Next Action}
    
    NEXT_ACTION -->|Continue| REQ_TASK
    NEXT_ACTION -->|View Progress| DASHBOARD[Go to Dashboard]
    NEXT_ACTION -->|Logout| LOGOUT[Logout User]
    
    ERROR_RECOVERY --> RETRY{Retry Submission?}
    RETRY -->|Yes| SUBMIT
    RETRY -->|No| SAVE_DRAFT
    
    DASHBOARD --> END_SUCCESS([End - Success])
    LOGOUT --> END_SUCCESS

    %% Background Consensus Process
    TRIGGER_CONSENSUS -.-> BG_CONSENSUS[Background Consensus Process]
    BG_CONSENSUS -.-> COLLECT_TRANSCRIPTIONS[Collect All Transcriptions for Chunk]
    COLLECT_TRANSCRIPTIONS -.-> CALCULATE_SIMILARITY[Calculate Text Similarity]
    CALCULATE_SIMILARITY -.-> WEIGHT_QUALITY[Weight by Quality Scores]
    WEIGHT_QUALITY -.-> DETERMINE_CONSENSUS[Determine Consensus Text]
    DETERMINE_CONSENSUS -.-> UPDATE_CONSENSUS[Update Consensus in Database]
    UPDATE_CONSENSUS -.-> NOTIFY_CONTRIBUTORS[Notify Contributors]

    %% Styling
    classDef userAction fill:#e3f2fd
    classDef process fill:#e8f5e8
    classDef decision fill:#fff3e0
    classDef error fill:#ffebee
    classDef success fill:#e0f2f1
    classDef background fill:#f3e5f5

    class START,USER_WORK,TRANSCRIBE,NEXT_ACTION userAction
    class REQ_TASK,FIND_CHUNKS,SELECT,LOAD_AUDIO,SAVE_TRANSCRIPTIONS process
    class AUTH,AVAILABLE,CHECK_REQUIRED,VALIDATE_SESSION,CHECK_DUPLICATES decision
    class SESSION_ERROR,DUPLICATE_ERROR,SHOW_ERRORS error
    class SUCCESS,NOTIFY_CONTRIBUTORS success
    class BG_CONSENSUS,COLLECT_TRANSCRIPTIONS,CALCULATE_SIMILARITY,WEIGHT_QUALITY background
```

## 🎯 Task Assignment Algorithm

```mermaid
flowchart LR
    subgraph "Task Request Parameters"
        LANG[Language Preference]
        QTY[Quantity Requested]
        SKIP[Skip List]
        DIFFICULTY[Difficulty Level]
    end
    
    subgraph "Filtering Process"
        ALL_CHUNKS[All Available Chunks]
        FILTER_LANG[Filter by Language]
        FILTER_USER[Exclude User's Work]
        FILTER_SKIP[Exclude Skip List]
        FILTER_STATUS[Filter by Status]
        PRIORITIZE[Prioritize by Need]
    end
    
    subgraph "Selection Strategy"
        RANDOM[Random Selection]
        BALANCED[Balance Difficulty]
        QUALITY[Quality Distribution]
        FINAL[Final Chunk List]
    end
    
    LANG --> FILTER_LANG
    QTY --> RANDOM
    SKIP --> FILTER_SKIP
    DIFFICULTY --> BALANCED
    
    ALL_CHUNKS --> FILTER_LANG
    FILTER_LANG --> FILTER_USER
    FILTER_USER --> FILTER_SKIP
    FILTER_SKIP --> FILTER_STATUS
    FILTER_STATUS --> PRIORITIZE
    
    PRIORITIZE --> RANDOM
    RANDOM --> BALANCED
    BALANCED --> QUALITY
    QUALITY --> FINAL
```

## 📊 Consensus Algorithm

```mermaid
flowchart TD
    CHUNK[Audio Chunk] --> COLLECT[Collect All Transcriptions]
    COLLECT --> COUNT{Transcription Count}
    
    COUNT -->|< 3| NEED_MORE[Need More Transcriptions]
    COUNT -->|≥ 3| ANALYZE[Analyze Transcriptions]
    
    ANALYZE --> SIMILARITY[Calculate Text Similarity]
    SIMILARITY --> CLUSTER[Group Similar Transcriptions]
    CLUSTER --> WEIGHT[Apply Quality Weights]
    
    WEIGHT --> SCORE[Calculate Consensus Scores]
    SCORE --> THRESHOLD{Above Threshold?}
    
    THRESHOLD -->|No| NEED_MORE
    THRESHOLD -->|Yes| SELECT_CONSENSUS[Select Consensus Text]
    
    SELECT_CONSENSUS --> VALIDATE_CONSENSUS[Validate Consensus Quality]
    VALIDATE_CONSENSUS --> MARK_COMPLETE[Mark Chunk as Complete]
    
    NEED_MORE --> PRIORITY[Increase Priority for Assignment]
    MARK_COMPLETE --> UPDATE_CONTRIBUTORS[Update Contributor Stats]
    
    %% Consensus Calculation Details
    subgraph "Similarity Calculation"
        LEVENSHTEIN[Levenshtein Distance]
        SEMANTIC[Semantic Similarity]
        PHONETIC[Phonetic Matching]
        COMBINED[Combined Score]
    end
    
    SIMILARITY --> LEVENSHTEIN
    SIMILARITY --> SEMANTIC
    SIMILARITY --> PHONETIC
    LEVENSHTEIN --> COMBINED
    SEMANTIC --> COMBINED
    PHONETIC --> COMBINED
    COMBINED --> CLUSTER
```

## 🔄 Quality Control Process

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant Q as Quality Engine
    participant DB as Database
    participant N as Notification

    U->>F: Submit Transcription
    F->>B: Send Transcription Data
    B->>DB: Save Transcription
    
    B->>Q: Trigger Quality Check
    Q->>DB: Get Related Transcriptions
    Q->>Q: Calculate Quality Metrics
    
    alt Quality Issues Detected
        Q->>DB: Flag for Review
        Q->>N: Notify Moderators
    else Quality Acceptable
        Q->>Q: Update Quality Score
    end
    
    Q->>B: Quality Assessment Complete
    B->>F: Update UI Status
    F->>U: Show Completion Status
    
    Note over Q: Background Consensus Process
    Q->>Q: Check Consensus Threshold
    
    alt Consensus Reached
        Q->>DB: Update Consensus Text
        Q->>N: Notify Contributors
    else Need More Transcriptions
        Q->>DB: Increase Chunk Priority
    end
```

## 📈 Progress Tracking

### Individual User Progress
```mermaid
graph LR
    subgraph "User Metrics"
        TOTAL[Total Transcriptions]
        ACCURACY[Accuracy Rate]
        SPEED[Average Speed]
        QUALITY[Quality Score]
    end
    
    subgraph "Achievements"
        BADGES[Achievement Badges]
        LEVELS[Experience Levels]
        STREAKS[Contribution Streaks]
        RANKINGS[Leaderboards]
    end
    
    TOTAL --> BADGES
    ACCURACY --> LEVELS
    SPEED --> RANKINGS
    QUALITY --> STREAKS
```

### System-wide Progress
```mermaid
graph TD
    subgraph "Dataset Metrics"
        CHUNKS_TOTAL[Total Audio Chunks]
        CHUNKS_TRANSCRIBED[Transcribed Chunks]
        CONSENSUS_REACHED[Consensus Achieved]
        QUALITY_VALIDATED[Quality Validated]
    end
    
    subgraph "Language Coverage"
        LANG_SUPPORTED[Supported Languages]
        DIALECT_COVERAGE[Dialect Coverage]
        SPEAKER_DIVERSITY[Speaker Diversity]
        DOMAIN_COVERAGE[Domain Coverage]
    end
    
    CHUNKS_TOTAL --> CHUNKS_TRANSCRIBED
    CHUNKS_TRANSCRIBED --> CONSENSUS_REACHED
    CONSENSUS_REACHED --> QUALITY_VALIDATED
    
    QUALITY_VALIDATED --> LANG_SUPPORTED
    LANG_SUPPORTED --> DIALECT_COVERAGE
    DIALECT_COVERAGE --> SPEAKER_DIVERSITY
    SPEAKER_DIVERSITY --> DOMAIN_COVERAGE
```

## 🎯 Optimization Strategies

### Performance Optimizations
- **Caching**: Cache frequently accessed chunks and user data
- **Preloading**: Preload next chunks while user works on current ones
- **CDN**: Optimize audio delivery through CDN
- **Compression**: Compress audio for faster loading

### User Experience Optimizations
- **Smart Assignment**: Assign chunks based on user expertise and preferences
- **Progress Indicators**: Clear progress tracking and feedback
- **Keyboard Shortcuts**: Efficient transcription interface
- **Auto-save**: Prevent data loss with automatic saving

### Quality Optimizations
- **Difficulty Balancing**: Mix easy and challenging chunks
- **Context Provision**: Provide helpful context and hints
- **Real-time Feedback**: Immediate quality feedback
- **Consensus Weighting**: Weight transcriptions by contributor reliability

## 🚨 Error Handling & Recovery

### Common Error Scenarios
1. **Session Timeout**
   - Auto-save work in progress
   - Seamless session renewal
   - Recovery of unsaved work

2. **Network Interruption**
   - Offline work capability
   - Automatic retry mechanisms
   - Queue submissions for later

3. **Audio Loading Issues**
   - Fallback audio formats
   - Progressive loading
   - Error reporting and alternatives

4. **Consensus Conflicts**
   - Human review escalation
   - Weighted voting systems
   - Quality threshold adjustments

### Recovery Mechanisms
```mermaid
flowchart LR
    ERROR[Error Detected] --> CLASSIFY{Error Classification}
    
    CLASSIFY -->|Temporary| AUTO_RETRY[Automatic Retry]
    CLASSIFY -->|User Error| USER_GUIDANCE[User Guidance]
    CLASSIFY -->|System Error| ESCALATE[Escalate to Support]
    
    AUTO_RETRY --> SUCCESS{Retry Success?}
    SUCCESS -->|Yes| CONTINUE[Continue Process]
    SUCCESS -->|No| USER_GUIDANCE
    
    USER_GUIDANCE --> RESOLVED{Issue Resolved?}
    RESOLVED -->|Yes| CONTINUE
    RESOLVED -->|No| ESCALATE
    
    ESCALATE --> SUPPORT[Support Intervention]
    SUPPORT --> CONTINUE
```

---

This comprehensive transcription workflow ensures high-quality data collection while providing an engaging and efficient experience for contributors.