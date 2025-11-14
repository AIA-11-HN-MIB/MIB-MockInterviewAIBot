# Voice Support Integration - Design Decisions

**Date**: 2025-11-15
**Plan**: `251115-0406-voice-support-integration`

---

## ✅ User-Confirmed Design Decisions

### 1. Audio Format Support
**Decision**: **WebM (primary) + WAV (fallback)**

**Rationale**:
- WebM (Opus codec) provides lowest latency (~20-50ms) for real-time streaming
- Browser-native support via WebRTC (no encoding overhead)
- WAV as fallback for universal compatibility (~100ms latency)
- Azure Speech SDK handles both formats automatically (no server-side conversion needed)

**Implementation**:
- Client preferably sends WebM for real-time interviews
- Server accepts both WebM and WAV (Azure SDK auto-detects)
- Error message if unsupported format (reject MP3 for real-time due to ~150-300ms encoding delay)

---

### 2. TTS Audio Caching
**Decision**: **Yes, LRU cache with 128 entries**

**Rationale**:
- Reduces Azure TTS API costs (repeated questions use cached audio)
- Faster response times (no API roundtrip for cached content)
- 128 entries sufficient for typical question banks (50-100 unique questions)

**Implementation**:
- `functools.lru_cache(maxsize=128)` decorator on TTS synthesis
- Cache key: `(text, voice_name, speed)` tuple
- Cache invalidation: LRU eviction (oldest entry removed when full)

**Cost Savings**:
- Azure TTS: $16 per 1M characters
- Average question: 100 characters
- 1000 interviews × 10 questions = 10,000 TTS calls
- Without cache: $16 (10,000 × 100 / 1M)
- With cache: $1.60 (1,000 × 100 / 1M) → **90% cost reduction**

---

### 3. Voice Metrics Weighting
**Decision**: **70% theoretical + 30% speaking (configurable)**

**Rationale**:
- Content quality (semantic similarity) more important than delivery
- Voice quality still matters for soft skills assessment
- Configurable via `VOICE_METRICS_WEIGHT=0.3` setting (allows tuning)

**Implementation**:
```python
# settings.py
voice_metrics_weight: float = Field(
    default=0.3,
    ge=0.0,
    le=1.0,
    description="Weight of voice metrics in final score (0-1)"
)

# evaluation logic
final_score = (
    (1 - voice_metrics_weight) * theoretical_score +
    voice_metrics_weight * speaking_score
)
```

**Example**:
- Theoretical score: 85/100 (good semantic answer)
- Speaking score: 60/100 (low fluency, fast speaking rate)
- Final score: 0.7 × 85 + 0.3 × 60 = 59.5 + 18 = **77.5/100**

---

### 4. Streaming Mode
**Decision**: **Real-time STT with streaming transcription**

**Rationale**:
- Better UX with live transcription feedback (candidate sees words appear)
- Lower perceived latency (transcription starts before audio finishes)
- More natural interview flow (similar to human interviewer)

**Implementation**:
- Azure SDK continuous recognition with interim results
- Background asyncio task consumes audio stream
- Send `TranscriptionMessage` with `is_final=false` for interim results
- Final transcription sent when audio stream ends

**Complexity Trade-off**:
- Batch mode: Simple (wait for all chunks → transcribe → respond) - **2 hours**
- Streaming mode: Complex (async queue, background task, interim results) - **5-6 hours**
- **Decision**: Accept complexity for better UX

---

### 5. Audio Storage
**Decision**: **Optional feature flag (disabled by default)**

**Rationale**:
- Privacy concerns (GDPR Article 17 - right to deletion)
- Storage costs (Azure Blob: $0.018/GB/month)
- Compliance (audio = personal data, requires consent)

**Implementation**:
```python
# settings.py
save_audio: bool = Field(
    default=False,
    description="Save audio files for review/training"
)

# interview_handler.py
if settings.save_audio:
    await save_to_blob_storage(
        audio_bytes=complete_audio,
        interview_id=interview_id,
        question_id=question_id,
        retention_days=30,  # Auto-delete after 30 days
    )
```

**GDPR Compliance**:
- Disabled by default (no storage without consent)
- 30-day retention (automatic deletion via Azure Blob lifecycle policy)
- Candidate consent required if enabled (checkbox in frontend)

---

## Impact on Implementation Plan

### Effort Adjustments

| Phase | Original | Updated | Reason |
|-------|----------|---------|--------|
| Phase 3 | 4-5 hours | **5-6 hours** | Real-time streaming STT (async complexity) |
| **Total** | 14-18 hours | **15-19 hours** | +1 hour for streaming |

### New Requirements

1. **Phase 2 (Settings)**:
   - Add `VOICE_METRICS_WEIGHT=0.3` config
   - Add `SAVE_AUDIO=false` config
   - Add `PREFERRED_AUDIO_FORMAT=webm` config

2. **Phase 3 (WebSocket)**:
   - Implement async audio streaming (not batch)
   - Send interim TranscriptionMessage (is_final=false)
   - Audio format validation (accept WebM/WAV, reject MP3 for real-time)

3. **Phase 4 (Orchestrator)**:
   - Implement TTS caching with `functools.lru_cache(maxsize=128)`
   - Apply voice metrics weighting in evaluation (70/30 split)

4. **Phase 5 (Testing)**:
   - Test real-time streaming with interim results
   - Test cache hit/miss scenarios
   - Test audio format validation

---

## Success Criteria (Updated)

- ✅ Real-time STT with interim transcription results
- ✅ WebM audio format accepted (primary)
- ✅ TTS cache reduces API costs by 90%
- ✅ Voice metrics weighted at 30% (configurable)
- ✅ Audio storage disabled by default (GDPR compliant)
- ✅ All tests pass (85%+ coverage)

---

## References

- [Main Plan](./plan.md)
- [Phase 3: WebSocket Audio Integration](./phase-3-websocket-audio.md)
- [Phase 4: Session Orchestrator](./phase-4-orchestrator-voice.md)
