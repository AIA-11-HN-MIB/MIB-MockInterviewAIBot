# Code Review: Phase 1 Speech Integration

**Reviewer**: Code Review Agent
**Date**: 2025-11-12
**Branch**: feat/EA-10-do-interview
**Plan**: Phase 1 - Speech Integration Foundation

---

## Code Review Summary

### Scope
- **Files reviewed**: 9 implementation files + 3 configuration files
  - Port interfaces (2): `speech_to_text_port.py`, `text_to_speech_port.py`
  - DTOs (1): `audio_dto.py`
  - Mock adapters (2): `mock_stt_adapter.py`, `mock_tts_adapter.py`
  - Azure adapters (3): `azure_stt_adapter.py`, `azure_tts_adapter.py`, `__init__.py`
  - Configuration (2): `settings.py`, `container.py`
- **Lines analyzed**: ~1,200 LOC
- **Review focus**: Phase 1 implementation (ports, DTOs, mock/Azure adapters, DI)

### Updated Plans
- Plan file needs task status update (see Recommended Actions below)

### Overall Assessment

**Quality**: Good - Implementation follows Clean Architecture principles with proper separation of concerns. Code is readable, well-documented, and properly structured.

**Completeness**: 90% complete - Missing critical tests (0 test files found for speech components), Azure SDK not installed, caching not fully implemented.

**Architecture Compliance**: Excellent - Strong adherence to Clean Architecture, dependency inversion, and SOLID principles.

---

## Critical Issues

### C1: Missing Test Coverage (Blocker)
**Severity**: CRITICAL
**Impact**: Violates success criteria (>=80% coverage), prevents validation

**Files**: No test files found for speech components
**Expected**: Tests for all adapters (mock and Azure), voice metrics calculation, error handling

**Details**:
- Success criteria requires >=80% unit test coverage
- No tests found for: `mock_stt_adapter.py`, `mock_tts_adapter.py`, `azure_stt_adapter.py`, `azure_tts_adapter.py`
- Voice metrics calculation logic untested (critical for interview evaluation)
- Error handling paths untested

**Recommendation**:
Create test files:
```
tests/unit/adapters/mock/test_mock_stt_adapter.py
tests/unit/adapters/mock/test_mock_tts_adapter.py
tests/unit/adapters/speech/test_azure_stt_adapter.py
tests/unit/adapters/speech/test_azure_tts_adapter.py
tests/unit/application/dto/test_audio_dto.py
```

**Priority**: Must fix before Phase 2

---

### C2: Azure SDK Not Installed (Blocker)
**Severity**: CRITICAL
**Impact**: Azure adapters fail to import, DI container crashes in production mode

**File**: Runtime environment
**Error**:
```
ModuleNotFoundError: No module named 'azure'
```

**Details**:
- `azure-cognitiveservices-speech>=1.31.0` defined in `pyproject.toml` (line 45) but not installed
- Import test fails: `from src.adapters.speech import AzureSpeechToTextAdapter`
- Production mode (`use_mock_stt=False`) will crash

**Recommendation**:
```bash
pip install azure-cognitiveservices-speech>=1.31.0
# Or reinstall all dependencies
pip install -e ".[dev]"
```

**Priority**: Must fix before integration testing

---

### C3: Type Safety Issues
**Severity**: HIGH
**Impact**: Type checking fails, potential runtime errors

**Mypy errors** (6 type issues):

1. **audio_dto.py:36** - Missing type parameters for `dict`
   ```python
   # Current (line 36)
   metadata: dict = Field(default_factory=dict, description="Additional metadata")

   # Fix
   metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
   ```

2. **azure_tts_adapter.py:231, 246** - Missing type parameters for `tuple`
   ```python
   # Current (lines 231, 246)
   def _get_from_cache(self, cache_key: tuple) -> bytes | None:
   def _add_to_cache(self, cache_key: tuple, audio_bytes: bytes) -> None:

   # Fix
   def _get_from_cache(self, cache_key: tuple[str, str, float]) -> bytes | None:
   def _add_to_cache(self, cache_key: tuple[str, str, float], audio_bytes: bytes) -> None:
   ```

3. **azure_tts_adapter.py:185** - Returning `Any` from function declared to return `bytes`
   ```python
   # Line 184-185 (in _synthesize_sync)
   audio_bytes = result.audio_data  # Type: Any from Azure SDK
   return audio_bytes  # Error: returning Any instead of bytes

   # Fix: Add explicit cast
   return bytes(audio_bytes)
   ```

**Priority**: Fix before commit

---

## High Priority Findings

### H1: Incomplete Caching Implementation
**Severity**: HIGH
**Impact**: Performance NFR not met (TTS latency >1s for repeated questions)

**File**: `azure_tts_adapter.py`
**Lines**: 231-257

**Details**:
- Caching methods are no-ops (always return None/pass)
- Comments say "In production, implement proper caching"
- Violates NFR1: TTS latency <1s for 100-word text (repeated questions)
- `cache_size` parameter accepted but unused (misleading API)

**Current code**:
```python
def _get_from_cache(self, cache_key: tuple) -> bytes | None:
    """Get audio from LRU cache.
    Note: In production, implement proper caching (Redis, memcached, etc.)
    For now, returns None (no caching implemented)
    """
    return None  # ❌ No-op
```

**Recommendation**:
Use `functools.lru_cache` for in-memory caching (simple, effective for dev/staging):
```python
from functools import lru_cache

class AzureTextToSpeechAdapter(TextToSpeechPort):
    def __init__(self, ..., cache_size: int = 128):
        ...
        # Use lru_cache for synthesize method
        self._synthesize_cached = lru_cache(maxsize=cache_size)(self._synthesize_sync)

    async def synthesize_speech(self, text: str, voice: str, speed: float) -> bytes:
        cache_key = (text, voice, speed)
        # Use cached version
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(
            None, self._synthesize_cached, text, voice, speed
        )
        return audio_bytes
```

**Alternative**: Implement Redis cache for production (add to Phase 7 - Production Readiness)

**Priority**: Implement basic LRU cache now, Redis later

---

### H2: Error Handling Gaps
**Severity**: HIGH
**Impact**: Poor user experience, debugging difficulty

**Files**: `azure_stt_adapter.py`, `azure_tts_adapter.py`

**Issues**:

1. **azure_stt_adapter.py:182-184** - Generic exception catch without proper error context
   ```python
   except Exception as e:
       logger.error(f"Error during speech recognition: {str(e)}")
       raise  # ❌ Loses Azure-specific error details
   ```

   **Fix**: Wrap in domain exception with context
   ```python
   except speechsdk.CancellationDetailsException as e:
       raise SpeechRecognitionError(f"Azure STT failed: {e.error_details}") from e
   except Exception as e:
       raise SpeechRecognitionError(f"Unexpected STT error: {str(e)}") from e
   ```

2. **Missing retry logic** - NFR3 requires "3 attempts with exponential backoff"
   - No retry mechanism implemented in either adapter
   - Network failures = immediate error (poor UX)

   **Fix**: Add tenacity decorator
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
   def _transcribe_sync(self, audio_bytes: bytes, language: str) -> dict[str, Any]:
       ...
   ```

3. **Missing graceful degradation** - NFR3: "Fall back to mock if Azure fails"
   - DI container doesn't implement fallback logic
   - Production outage = complete service failure

   **Recommendation**: Add to container.py:
   ```python
   def speech_to_text_port(self) -> SpeechToTextPort:
       if self._stt_port is None:
           if self.settings.use_mock_stt:
               self._stt_port = MockSTTAdapter()
           else:
               try:
                   # Azure adapter initialization
                   self._stt_port = AzureSpeechToTextAdapter(...)
               except Exception as e:
                   logger.error(f"Azure STT failed, falling back to mock: {e}")
                   self._stt_port = MockSTTAdapter()  # Graceful degradation
       return self._stt_port
   ```

**Priority**: Add retry logic and domain exceptions before Phase 2

---

### H3: Voice Metrics Calculation Questionable
**Severity**: MEDIUM-HIGH
**Impact**: Interview evaluation accuracy

**File**: `azure_stt_adapter.py`
**Lines**: 186-257

**Issues**:

1. **Intonation formula lacks justification** (line 220):
   ```python
   intonation_score = min(confidence + (duration_seconds / 30.0) * 0.1, 1.0)
   ```
   - Why `duration / 30`? Magic number
   - Assumes longer speech = better intonation (not always true)
   - No prosody data extraction (Azure provides pitch/rate via JSON result, but not used)

2. **Azure prosody data unused** (lines 201-212):
   ```python
   json_result = result.properties.get(
       speechsdk.PropertyId.SpeechServiceResponse_JsonResult
   )
   # ❌ Only extracts confidence, ignores prosody (pitch, rate, emphasis)
   ```

   **Fix**: Parse actual prosody data
   ```python
   if json_result:
       data = json.loads(json_result)
       # Extract prosody from detailed result
       prosody = data.get("NBest", [{}])[0].get("Prosody", {})
       pitch_variance = prosody.get("PitchVariance", 0.5)  # Use actual data
       intonation_score = pitch_variance  # Direct mapping
   ```

3. **Fluency calculation oversimplified** (lines 226-235):
   - Only considers WPM (words per minute)
   - Ignores pauses, filler words, repetitions (Azure doesn't provide these directly)
   - Optimal range (120-180 WPM) hardcoded without source

**Recommendation**:
- Document formulas in docstring with sources
- Add unit tests with known-good/bad audio samples
- Create baseline validation dataset (compare to human evaluators)

**Priority**: Medium - works for MVP, improve in Phase 3 (Enhanced Evaluation)

---

### H4: Missing Language Detection Implementation
**Severity**: MEDIUM
**Impact**: Port contract violation, misleading API

**File**: `azure_stt_adapter.py`
**Lines**: 96-110

**Details**:
```python
async def detect_language(self, audio_bytes: bytes) -> str | None:
    """Detect language from audio bytes."""
    # Azure SDK has language detection, but for simplicity return default
    # In production, implement proper language detection
    return self.default_language  # ❌ Not implemented
```

- Port interface promises language detection
- Implementation always returns default (violates contract)
- Azure SDK supports auto-detection via `AutoDetectSourceLanguageConfig`

**Recommendation**:
Either:
1. **Implement properly** using Azure's auto-detection:
   ```python
   auto_detect_config = speechsdk.AutoDetectSourceLanguageConfig(
       languages=["en-US", "vi-VN", "zh-CN"]
   )
   recognizer = speechsdk.SpeechRecognizer(
       speech_config=self.speech_config,
       auto_detect_source_language_config=auto_detect_config,
       audio_config=audio_config,
   )
   result = recognizer.recognize_once()
   detected_lang = result.properties.get(speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult)
   ```

2. **Remove from port** if not needed for MVP (violates YAGNI)

**Priority**: Decide in Phase 2 - either implement or remove

---

## Medium Priority Improvements

### M1: Mock Adapter Determinism Issue
**Severity**: MEDIUM
**Impact**: Test flakiness, non-reproducible results

**File**: `mock_stt_adapter.py`
**Lines**: 98-100

**Details**:
```python
def _generate_voice_metrics(self, audio_size: int, word_count: int):
    # Use audio size as seed for consistent metrics per audio
    if self.seed is None:
        random.seed(audio_size)  # ❌ Sets global random state
```

**Problem**:
- Modifies global `random` module state (side effect)
- Affects other code using `random` in same process
- Tests may interfere with each other

**Fix**: Use instance-local Random
```python
class MockSTTAdapter(SpeechToTextPort):
    def __init__(self, seed: int | None = None):
        self.seed = seed
        self._rng = random.Random(seed)  # ✅ Instance-local RNG

    def _generate_voice_metrics(self, audio_size: int, word_count: int):
        if self.seed is None:
            self._rng.seed(audio_size)

        intonation_score = 0.5 + (self._rng.random() * 0.3) + ...
```

**Priority**: Fix before writing tests (prevents test pollution)

---

### M2: Configuration Validation Missing
**Severity**: MEDIUM
**Impact**: Cryptic errors at runtime instead of startup

**File**: `container.py`
**Lines**: 274-283

**Details**:
```python
if not self.settings.azure_speech_key:
    raise ValueError("Azure Speech API key not configured")
if not self.settings.azure_speech_region:
    raise ValueError("Azure Speech region not configured")
```

**Issues**:
- Validation happens lazily (on first use, not startup)
- If `use_mock_stt=True` initially, then toggled to `False`, crash occurs mid-operation
- No validation for other Azure configs (voice name, language)

**Recommendation**:
Add validation to Settings class:
```python
# settings.py
from pydantic import field_validator

class Settings(BaseSettings):
    ...

    @field_validator("azure_speech_key")
    @classmethod
    def validate_azure_key(cls, v, info):
        use_mock = info.data.get("use_mock_stt", True)
        if not use_mock and not v:
            raise ValueError("azure_speech_key required when use_mock_stt=False")
        return v
```

**Priority**: Medium - add to Phase 2 (before production use)

---

### M3: Logging Improvements Needed
**Severity**: LOW-MEDIUM
**Impact**: Debugging difficulty, missing metrics

**Files**: All adapters

**Issues**:

1. **Missing request IDs** - Can't trace request through logs
   ```python
   logger.info(f"Transcribed {len(text)} chars")  # ❌ No context
   ```

   **Fix**: Add interview_id/session_id to logs
   ```python
   logger.info(f"Transcribed {len(text)} chars", extra={"interview_id": interview_id})
   ```

2. **No performance metrics logged** - Can't validate NFR1 (latency <2s STT, <1s TTS)
   ```python
   # Add timing logs
   import time
   start = time.perf_counter()
   result = recognizer.recognize_once()
   duration_ms = (time.perf_counter() - start) * 1000
   logger.info(f"STT latency: {duration_ms:.0f}ms", extra={"metric": "stt_latency"})
   ```

3. **Sensitive data in logs** - Audio bytes size logged (OK), but avoid logging text in production
   ```python
   logger.info(f"Synthesized {len(text)} chars → {len(audio_bytes)} bytes")
   # Better: logger.info(f"TTS synthesis completed", extra={"text_chars": len(text), "audio_bytes": len(audio_bytes)})
   ```

**Priority**: Low - improve iteratively

---

### M4: SSML Generation Hardcoded
**Severity**: LOW-MEDIUM
**Impact**: Limited TTS expressiveness

**File**: `azure_tts_adapter.py`
**Lines**: 201-229

**Details**:
```python
def _build_ssml(self, text: str, voice: str, speed: float) -> str:
    # Only supports speed adjustment
    ssml = f"""
    <speak version="1.0" ...>
        <voice name="{voice}">
            <prosody rate="{speed_str}">
                {text}
            </prosody>
        </voice>
    </speak>
    """
```

**Limitations**:
- Only `rate` (speed) supported, no pitch/volume control
- No support for emphasis, pauses, breaks
- Can't add emotional tone (important for interview questions)

**Recommendation** (for Phase 6 - Summary Generation):
Add SSML builder utility:
```python
class SSMLBuilder:
    def add_emphasis(self, text: str, level: str = "strong") -> str:
        return f'<emphasis level="{level}">{text}</emphasis>'

    def add_break(self, time_ms: int) -> str:
        return f'<break time="{time_ms}ms"/>'
```

**Priority**: Low - defer to Phase 6 (nice-to-have for MVP)

---

## Low Priority Suggestions

### L1: Code Duplication in Adapters
**Severity**: LOW
**Impact**: Maintainability

**Files**: `azure_stt_adapter.py`, `azure_tts_adapter.py`

**Duplication**:
- Similar config validation (lines 274-283 in container.py)
- Identical error handling patterns
- Repeated Azure SDK setup

**Recommendation**: Extract to base class (future refactor)
```python
class AzureAdapterBase:
    def __init__(self, api_key: str, region: str):
        self._validate_config(api_key, region)
        self.speech_config = speechsdk.SpeechConfig(api_key, region)

    def _validate_config(self, api_key: str, region: str) -> None:
        if not api_key:
            raise ValueError(f"{self.__class__.__name__}: API key required")
        ...
```

**Priority**: Low - DRY violation but not urgent

---

### L2: Magic Numbers in Calculations
**Severity**: LOW
**Impact**: Code readability

**Files**: `mock_stt_adapter.py`, `azure_stt_adapter.py`

**Examples**:
```python
# mock_stt_adapter.py:103
size_factor = min(audio_size / 100000, 1.0)  # Why 100KB?

# azure_stt_adapter.py:220
intonation_score = min(confidence + (duration_seconds / 30.0) * 0.1, 1.0)  # Why 30?

# azure_stt_adapter.py:228
if 120 <= speaking_rate_wpm <= 180:  # Why 120-180?
```

**Recommendation**: Extract to named constants
```python
# At top of file
OPTIMAL_WPM_MIN = 120  # Based on research: https://...
OPTIMAL_WPM_MAX = 180
INTONATION_DURATION_FACTOR = 30.0  # Calibrated for 30-second samples
```

**Priority**: Low - improves readability, not critical

---

### L3: Missing Docstring Examples
**Severity**: LOW
**Impact**: Developer experience

**Files**: All port interfaces

**Current**:
```python
async def transcribe_audio(self, audio_bytes: bytes, language: str = "en-US") -> dict[str, Any]:
    """Transcribe audio bytes to text with voice metrics.

    Args: ...
    Returns: ...
    """
```

**Recommendation**: Add usage examples
```python
async def transcribe_audio(...) -> dict[str, Any]:
    """Transcribe audio bytes to text with voice metrics.

    Example:
        >>> with open("answer.wav", "rb") as f:
        ...     audio = f.read()
        >>> result = await stt.transcribe_audio(audio)
        >>> result["text"]
        'FastAPI is a modern web framework...'
        >>> result["voice_metrics"]["confidence_score"]
        0.95

    Args: ...
    """
```

**Priority**: Low - nice-to-have for documentation

---

## Positive Observations

1. **Excellent Clean Architecture adherence**
   - Port interfaces properly abstract implementations
   - Dependency inversion correctly implemented
   - Domain layer has zero adapter dependencies

2. **Comprehensive docstrings**
   - All public methods documented
   - Return types clearly specified
   - Arg descriptions provided

3. **Good error handling structure**
   - Azure-specific errors caught and logged
   - Cancellation reasons inspected
   - Fallback values for metric calculation failures

4. **Mock adapters well-designed**
   - Realistic voice metrics simulation
   - Proper WAV file generation (headers, PCM data)
   - Deterministic behavior (testable)

5. **Configuration flexibility**
   - Individual mock flags per adapter (use_mock_stt, use_mock_tts)
   - Sensible defaults
   - Environment-based configuration

6. **Code style consistency**
   - Ruff checks pass (all files)
   - Line length respected (100 chars)
   - Import order correct

---

## Recommended Actions

### Immediate (Before Phase 2)

1. **Fix type safety issues** (C3)
   - Add type parameters: `dict[str, Any]`, `tuple[str, str, float]`
   - Cast `audio_bytes` to `bytes` in azure_tts_adapter.py:185
   - Run `mypy` to verify

2. **Install Azure SDK** (C2)
   ```bash
   pip install azure-cognitiveservices-speech>=1.31.0
   ```

3. **Create test files** (C1)
   - Start with mock adapter tests (easier, no API calls)
   - Mock Azure SDK for Azure adapter tests
   - Target 80% coverage

4. **Fix mock adapter random seeding** (M1)
   - Use instance-local `Random()` instead of global state

5. **Add retry logic** (H2)
   - Install `tenacity`: `pip install tenacity`
   - Decorate `_transcribe_sync` and `_synthesize_sync`

6. **Update phase1-speech-integration.md**
   - Mark completed tasks (Ports, DTOs, Adapters, Config)
   - Mark incomplete tasks (Tests, Validation, Documentation)
   - Add new tasks discovered during review

### Short-term (Phase 2-3)

7. **Implement basic LRU caching** (H1)
   - Use `functools.lru_cache` for in-memory cache
   - Defer Redis to production phase

8. **Add domain exceptions** (H2)
   - Create `SpeechRecognitionError`, `SpeechSynthesisError` in `domain/exceptions.py`
   - Wrap Azure errors in domain exceptions

9. **Add graceful degradation** (H2)
   - Fallback to mock adapters on Azure initialization failure
   - Log fallback events for monitoring

10. **Decide on language detection** (H4)
    - Either implement using `AutoDetectSourceLanguageConfig`
    - Or remove from port interface (YAGNI)

### Long-term (Phase 6-7)

11. **Validate voice metrics** (H3)
    - Create baseline dataset (human evaluations)
    - Compare computed scores to human scores
    - Tune formulas based on data

12. **Add Redis caching** (H1)
    - Replace in-memory LRU with Redis
    - Configure TTL, eviction policy

13. **Extract base class** (L1)
    - Reduce duplication in Azure adapters
    - Create `AzureAdapterBase` utility

---

## Metrics

### Code Quality
- **Type Coverage**: 95% (6 type issues out of ~150 type hints)
- **Test Coverage**: 0% (no tests for speech components)
- **Linting Issues**: 0 (ruff checks pass)
- **Architecture Compliance**: 100% (full Clean Architecture adherence)

### Implementation Status
- ✅ Port interfaces defined (100%)
- ✅ DTOs created (100%)
- ✅ Mock adapters implemented (100%)
- ✅ Azure adapters implemented (95% - missing retry/fallback)
- ✅ DI container wired (100%)
- ✅ Configuration added (100%)
- ❌ Unit tests (0% - blocking)
- ❌ Integration tests (0% - blocking)
- ⚠️ Caching (20% - stubs only)

### Success Criteria Review
From phase1-speech-integration.md:

- ✅ **STT adapter returns text + 3 voice metrics** - PASS
- ⚠️ **TTS adapter generates audio <1s for 100-word text** - UNVERIFIED (no caching = likely FAIL)
- ✅ **Mock adapters simulate realistic voice metrics** - PASS (deterministic)
- ⚠️ **Voice metrics calculation <500ms** - UNVERIFIED (no performance tests)
- ❌ **Unit test coverage >=80%** - FAIL (0% coverage)
- ❌ **Integration tests pass with real Azure Speech SDK** - FAIL (SDK not installed)

**Phase 1 Status**: 60% complete (implementation done, validation missing)

---

## Unresolved Questions

1. **Voice metrics validation**: How will we validate intonation/fluency scores against human evaluators? Need baseline dataset.

2. **Caching strategy**: In-memory LRU sufficient for MVP? When to migrate to Redis?

3. **Language detection**: Is multi-language support needed for MVP? If yes, implement now; if no, remove port method.

4. **Error fallback UX**: Should users be notified when Azure fails and mock is used? Or silent fallback?

5. **Performance benchmarking**: What's the plan to measure STT/TTS latency in production? Add APM/metrics?

6. **Audio format handling**: Phase 1 assumes WAV/PCM 16kHz. Phase 2 WebSocket will use WebM Opus. Who handles conversion? (Answer: Phase 2 - add audio converter utility)

---

## Conclusion

**Phase 1 implementation quality is GOOD**, with strong architecture and clean code. However, **critical gaps in testing and validation** prevent completion.

**Blocking issues**:
- No unit tests (violates 80% coverage requirement)
- Azure SDK not installed (runtime crashes)
- Type safety issues (mypy failures)

**Recommended path forward**:
1. Fix type issues (30 min)
2. Install Azure SDK (5 min)
3. Write mock adapter tests (2-3 hours)
4. Write Azure adapter tests with mocked SDK (3-4 hours)
5. Add retry logic and error handling (1-2 hours)
6. Implement basic LRU caching (1 hour)
7. Update plan task status

**Estimated time to complete Phase 1**: 8-12 hours

**Risk level**: MEDIUM - Implementation solid, but validation gap could hide bugs in voice metrics calculation or Azure SDK integration.

Once tests pass and coverage >=80%, Phase 1 can be marked COMPLETE and Phase 2 (WebSocket Protocol) can begin.

---

**Review Signature**: Code Review Agent
**Next Review**: After test implementation (before Phase 2 start)
