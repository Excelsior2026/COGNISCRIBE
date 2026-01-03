# CogniScribe Enhancement Roadmap

**Last Updated**: January 3, 2026  
**Status**: Active Development

This roadmap outlines planned enhancements to CogniScribe, prioritized from most critical to future features.

## 🔴 Phase 1: Critical Infrastructure (Weeks 1-2)

### 1.1 Docker Compose with Ollama Integration ✅ **COMPLETED**
- **Issue**: [#4](https://github.com/Excelsior2026/COGNISCRIBE/issues/4)
- **Status**: ✅ Implemented
- **Effort**: 2-3 hours
- **Benefits**: One-command deployment, reproducible environments
- **Deliverables**:
  - [x] Enhanced docker-compose.yml with Ollama service
  - [x] Volume persistence for models
  - [x] Health checks for all services
  - [x] Automatic model pulling

### 1.2 PHI Detection and Prevention Layer 🚧 **IN PROGRESS**
- **Issue**: [#5](https://github.com/Excelsior2026/COGNISCRIBE/issues/5)
- **Status**: 🚧 Core implementation complete, integration pending
- **Priority**: 🔴 CRITICAL
- **Effort**: 1-2 days
- **Benefits**: Legal compliance, ethical AI deployment
- **Deliverables**:
  - [x] PHI detection module (`phi_detector.py`)
  - [ ] Integration with transcription pipeline
  - [ ] API endpoint modifications
  - [ ] User-facing error messages
  - [ ] Audit logging implementation
  - [ ] Documentation updates

### 1.3 Pydantic Settings Validation
- **Issue**: [#7](https://github.com/Excelsior2026/COGNISCRIBE/issues/7)
- **Status**: ⏳ Pending
- **Priority**: 🟡 HIGH
- **Effort**: 1 day
- **Benefits**: Fail-fast configuration, type safety
- **Tasks**:
  - [ ] Refactor `settings.py` to use Pydantic Settings
  - [ ] Add field validators
  - [ ] Generate `.env.example`
  - [ ] Update all imports
  - [ ] Add settings validation tests

### 1.4 Comprehensive Test Suite
- **Issue**: [#6](https://github.com/Excelsior2026/COGNISCRIBE/issues/6)
- **Status**: ⏳ Pending
- **Priority**: 🟡 HIGH
- **Effort**: 3-4 days
- **Target Coverage**: 80%+
- **Tasks**:
  - [ ] Set up pytest infrastructure
  - [ ] Add test fixtures (sample audio)
  - [ ] Unit tests for core functions
  - [ ] Integration tests with mocks
  - [ ] API endpoint tests
  - [ ] Configure coverage reporting

---

## 🟡 Phase 2: CI/CD and Quality (Weeks 3-4)

### 2.1 GitHub Actions CI/CD Pipeline
- **Issue**: [#8](https://github.com/Excelsior2026/COGNISCRIBE/issues/8)
- **Status**: ⏳ Pending
- **Priority**: 🟡 HIGH
- **Effort**: 2-3 days
- **Components**:
  - [ ] Linting & formatting (Ruff, Black, isort)
  - [ ] Type checking (mypy)
  - [ ] Security scanning (Bandit, Safety, Trivy)
  - [ ] Automated testing with coverage
  - [ ] Docker build validation
  - [ ] Release automation

### 2.2 Code Quality Tools Setup
- **Tasks**:
  - [ ] Create `.ruff.toml` configuration
  - [ ] Add `pyproject.toml` with tool configs
  - [ ] Configure mypy strict mode
  - [ ] Add pre-commit hooks
  - [ ] Create `requirements-dev.txt`

### 2.3 Documentation Improvements
- **Tasks**:
  - [ ] Create `CONTRIBUTING.md`
  - [ ] Add API usage examples
  - [ ] Document deployment patterns
  - [ ] Expand troubleshooting guide
  - [ ] Add architecture diagrams

---

## 🟠 Phase 3: Core Features (Weeks 5-7)

### 3.1 Speaker Diarization
- **Issue**: [#9](https://github.com/Excelsior2026/COGNISCRIBE/issues/9)
- **Status**: ⏳ Pending
- **Priority**: 🟠 MEDIUM
- **Effort**: 2-3 days
- **Value**: High for multi-speaker lectures
- **Tasks**:
  - [ ] Add `pyannote.audio` dependencies
  - [ ] Implement `SpeakerDiarizer` class
  - [ ] Integrate with pipeline
  - [ ] Update API parameters
  - [ ] Add speaker labels to output
  - [ ] Performance testing

### 3.2 Export Formats (Phased Rollout)
- **Issue**: [#10](https://github.com/Excelsior2026/COGNISCRIBE/issues/10)
- **Status**: ⏳ Pending
- **Priority**: 🟠 MEDIUM
- **Total Effort**: 5-6 days

#### 3.2.1 Markdown Export (⚡ Quick Win)
- **Effort**: 2 hours
- **Tasks**:
  - [ ] Implement markdown formatter
  - [ ] Add `/api/export/markdown` endpoint
  - [ ] Frontend download button

#### 3.2.2 PDF Export
- **Effort**: 1 day
- **Tasks**:
  - [ ] Choose PDF library (weasyprint)
  - [ ] Design professional template
  - [ ] Implement generation
  - [ ] Add `/api/export/pdf` endpoint

#### 3.2.3 Anki Deck Generation
- **Effort**: 1-2 days
- **Tasks**:
  - [ ] Add `genanki` dependency
  - [ ] Implement flashcard logic
  - [ ] Create `.apkg` builder
  - [ ] Add `/api/export/anki` endpoint

#### 3.2.4 Notion Integration
- **Effort**: 2-3 days
- **Tasks**:
  - [ ] Set up OAuth flow
  - [ ] Implement Notion API client
  - [ ] Design page structure
  - [ ] Add `/api/export/notion` endpoint

### 3.3 Batch Processing
- **Priority**: 🟠 MEDIUM
- **Effort**: 2-3 days
- **Tasks**:
  - [ ] Set up Celery + Redis
  - [ ] Implement job queue
  - [ ] Add `/api/batch-pipeline` endpoint
  - [ ] Job status polling API
  - [ ] Background worker management

---

## 🔵 Phase 4: Performance & UX (Weeks 8-10)

### 4.1 Caching Layer
- **Priority**: 🔵 LOW-MEDIUM
- **Effort**: 1-2 days
- **Tasks**:
  - [ ] Implement Redis caching by file hash
  - [ ] Add cache hit/miss metrics
  - [ ] Configure TTL policies
  - [ ] Cache invalidation logic

### 4.2 Progress Tracking
- **Priority**: 🔵 LOW-MEDIUM
- **Effort**: 2 days
- **Tasks**:
  - [ ] Implement WebSocket or SSE
  - [ ] Add progress callbacks to pipeline
  - [ ] Frontend progress UI
  - [ ] Handle connection interruptions

### 4.3 Advanced Features
- **Subject Auto-Detection** (1 day)
  - [ ] Implement zero-shot classification
  - [ ] Add to pipeline options
  
- **Confidence Scores** (1 day)
  - [ ] Return Whisper word-level confidence
  - [ ] Highlight low-confidence terms
  
- **Custom Summary Formats** (1-2 days)
  - [ ] Add format preferences API
  - [ ] Implement format templates
  - [ ] User preference storage

---

## 🔮 Phase 5: Production Readiness (Weeks 11-12)

### 5.1 Database Implementation
- **Decision**: Implement OR remove unused dependencies?
- **If Implementing**:
  - [ ] Design schema (users, transcriptions, preferences)
  - [ ] Set up migrations with Alembic
  - [ ] Implement data access layer
  - [ ] Add user authentication
  - [ ] Processing history API
- **If Removing**:
  - [ ] Remove SQLAlchemy, Postgres, Alembic deps
  - [ ] Update requirements.txt
  - [ ] Remove unused imports

### 5.2 Monitoring & Observability
- **Tasks**:
  - [ ] Add Prometheus metrics
  - [ ] Implement structured logging
  - [ ] Add request tracing
  - [ ] Set up Grafana dashboards
  - [ ] Configure alerting

### 5.3 Deployment Documentation
- **Tasks**:
  - [ ] Kubernetes manifests
  - [ ] AWS deployment guide
  - [ ] GCP deployment guide
  - [ ] Scaling considerations
  - [ ] Load testing results

---

## 📊 Success Metrics

### Phase 1 Success Criteria
- ✅ One-command deployment works
- ✅ PHI rejection functional
- ✅ 80%+ test coverage
- ✅ CI/CD passing all checks

### Phase 2 Success Criteria
- ✅ All PRs require passing CI
- ✅ Code quality gates enforced
- ✅ Documentation complete

### Phase 3 Success Criteria
- ✅ Speaker diarization accuracy >85%
- ✅ Export formats functional
- ✅ Batch processing handles 10+ files

### Phase 4 Success Criteria
- ✅ Cache hit rate >40%
- ✅ Processing time reduced 30%
- ✅ User satisfaction >4.5/5

---

## 🔧 Development Guidelines

### For Each Feature
1. Create GitHub issue with detailed spec
2. Write tests first (TDD approach)
3. Implement feature
4. Update documentation
5. Submit PR with passing CI
6. Code review and merge

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature branches
- `hotfix/*`: Critical fixes

### Commit Convention
```
type(scope): subject

body (optional)

footer (optional)
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

---

## 📝 Notes

### Deferred Features (Future Consideration)
- Mobile app support
- Integration with note-taking apps beyond Notion
- Video lecture support
- Real-time transcription
- Custom model fine-tuning
- Multi-language support

### Known Limitations
- Whisper struggles with heavy accents
- Medical terminology may be misspelled
- Diarization requires clear audio separation
- Large files (>500MB) may timeout

---

## 👥 Contributors

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to this roadmap.

## 💬 Feedback

Have suggestions for the roadmap? [Open an issue](https://github.com/Excelsior2026/COGNISCRIBE/issues/new) with the `roadmap` label.
