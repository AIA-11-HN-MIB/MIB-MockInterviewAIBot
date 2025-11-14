# Phase 2: DI Container & Settings

**Phase ID**: Phase 2
**Duration**: 1-2 hours
**Dependencies**: Phase 1 (adapter signatures fixed)
**Risk Level**: Low

---

## Context

DI container has placeholder methods `speech_to_text_port()` and `text_to_speech_port()` but no implementation. Need mock/real toggle logic based on settings flags.

**Current State**:
- Methods defined at lines 270-329 in `container.py`
- Stub implementations exist (return None or raise NotImplementedError)
- Settings has flags: `use_mock_stt`, `use_mock_tts`, Azure config fields

**Goal**: Complete implementation with configuration-driven adapter selection.

---

## Overview

Implement speech service DI methods with:
1. Mock/real adapter selection based on `use_mock_stt`/`use_mock_tts` flags
2. Azure API key validation (raise ValueError if missing)
3. Singleton caching (`_stt_port`, `_tts_port` instance variables)
4. Error handling with descriptive messages

---

## Key Insights

### DI Pattern Consistency

Container already implements similar logic for LLM and vector search:
```python
def llm_port(self) -> LLMPort:
    if self._llm_port is None:
        if self.settings.use_mock_llm:
            self._llm_port = MockLLMAdapter()
        else:
            if not self.settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self._llm_port = OpenAIAdapter(...)
    return self._llm_port
```

**Apply same pattern** to speech services for consistency.

### Settings Validation Strategy

**Two-stage validation**:
1. **At DI time**: Validate API keys when real adapter requested
2. **At runtime**: Validate per-request params (audio format, voice name)

**Rationale**: Fail fast on config issues, provide clear error messages.

---

## Requirements

### Functional
- ✅ `speech_to_text_port()` returns MockSTTAdapter if `use_mock_stt=True`
- ✅ `speech_to_text_port()` returns AzureSTTAdapter if `use_mock_stt=False` (validates API key)
- ✅ `text_to_speech_port()` returns MockTTSAdapter if `use_mock_tts=True`
- ✅ `text_to_speech_port()` returns AzureTTSAdapter if `use_mock_tts=False` (validates API key)
- ✅ Singletons cached (only one instance per container)
- ✅ Missing API key raises ValueError with clear message

### Non-Functional
- ✅ Consistent error messages across all adapters
- ✅ Logging at INFO level when initializing adapters
- ✅ Settings defaults allow mock mode without configuration

---

## Architecture

### Container Singleton Pattern

```python
class Container:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._llm_port: LLMPort | None = None
        self._vector_search_port: VectorSearchPort | None = None
        self._stt_port: SpeechToTextPort | None = None  # ADD
        self._tts_port: TextToSpeechPort | None = None  # ADD

    def speech_to_text_port(self) -> SpeechToTextPort:
        """Lazy initialization with caching."""
        if self._stt_port is None:
            self._stt_port = self._create_stt_adapter()
        return self._stt_port

    def _create_stt_adapter(self) -> SpeechToTextPort:
        """Factory method for STT adapter selection."""
        if self.settings.use_mock_stt:
            return MockSTTAdapter()
        else:
            return self._create_azure_stt_adapter()
```

### Error Handling Hierarchy

```
ValueError (config errors - fail fast at DI time)
 ├─ "AZURE_SPEECH_KEY not configured"
 ├─ "AZURE_SPEECH_REGION not configured"
 └─ "Unsupported STT provider: {provider}"

RuntimeError (Azure SDK errors - handled at adapter layer)
 ├─ "Speech recognition failed: {details}"
 └─ "Speech synthesis canceled: {reason}"
```

---

## Implementation Steps

### Step 1: Update Container Instance Variables (5 min)

**File**: `src/infrastructure/dependency_injection/container.py`

**Changes** (lines 70-74):
```python
def __init__(self, settings: Settings):
    self.settings = settings
    self._llm_port: LLMPort | None = None
    self._vector_search_port: VectorSearchPort | None = None
    self._stt_port: SpeechToTextPort | None = None  # ADD
    self._tts_port: TextToSpeechPort | None = None  # ADD
```

### Step 2: Implement `speech_to_text_port()` (20 min)

**Replace existing stub** (lines 270-298):

```python
def speech_to_text_port(self) -> SpeechToTextPort:
    """Get speech-to-text port implementation.

    Returns:
        Configured STT service (mock or Azure)

    Raises:
        ValueError: If Azure Speech API key or region is not configured
    """
    if self._stt_port is None:
        # Use mock adapter if configured
        if self.settings.use_mock_stt:
            logger.info("Initializing MockSTTAdapter (development mode)")
            self._stt_port = MockSTTAdapter()
        else:
            # Use Azure Speech SDK
            logger.info("Initializing AzureSpeechToTextAdapter")

            # Validate configuration
            if not self.settings.azure_speech_key:
                raise ValueError(
                    "AZURE_SPEECH_KEY not configured. "
                    "Set environment variable or use USE_MOCK_STT=true for development."
                )
            if not self.settings.azure_speech_region:
                raise ValueError(
                    "AZURE_SPEECH_REGION not configured. "
                    "Set environment variable (e.g., 'eastus') or use USE_MOCK_STT=true."
                )

            # Import adapter (lazy import to avoid Azure SDK dependency in mock mode)
            from ...adapters.speech.azure_stt_adapter import AzureSpeechToTextAdapter

            self._stt_port = AzureSpeechToTextAdapter(
                api_key=self.settings.azure_speech_key,
                region=self.settings.azure_speech_region,
                language=self.settings.azure_speech_language,
            )

            logger.info(
                f"Azure STT initialized (region={self.settings.azure_speech_region}, "
                f"language={self.settings.azure_speech_language})"
            )

    return self._stt_port
```

### Step 3: Implement `text_to_speech_port()` (20 min)

**Replace existing stub** (lines 300-329):

```python
def text_to_speech_port(self) -> TextToSpeechPort:
    """Get text-to-speech port implementation.

    Returns:
        Configured TTS service (mock or Azure)

    Raises:
        ValueError: If Azure Speech API key or region is not configured
    """
    if self._tts_port is None:
        # Use mock adapter if configured
        if self.settings.use_mock_tts:
            logger.info("Initializing MockTTSAdapter (development mode)")
            self._tts_port = MockTTSAdapter()
        else:
            # Use Azure Speech SDK
            logger.info("Initializing AzureTTSAdapter")

            # Validate configuration
            if not self.settings.azure_speech_key:
                raise ValueError(
                    "AZURE_SPEECH_KEY not configured. "
                    "Set environment variable or use USE_MOCK_TTS=true for development."
                )
            if not self.settings.azure_speech_region:
                raise ValueError(
                    "AZURE_SPEECH_REGION not configured. "
                    "Set environment variable (e.g., 'eastus') or use USE_MOCK_TTS=true."
                )

            # Import adapter (lazy import)
            from ...adapters.speech.azure_tts_adapter import AzureTTSAdapter

            self._tts_port = AzureTTSAdapter(
                subscription_key=self.settings.azure_speech_key,
                region=self.settings.azure_speech_region,
                default_voice=self.settings.azure_speech_voice,
            )

            logger.info(
                f"Azure TTS initialized (region={self.settings.azure_speech_region}, "
                f"voice={self.settings.azure_speech_voice})"
            )

    return self._tts_port
```

### Step 4: Add Logging Import (2 min)

**File**: `src/infrastructure/dependency_injection/container.py`

**Add at top** (after existing imports):
```python
import logging

logger = logging.getLogger(__name__)
```

### Step 5: Settings Validation (Optional) (10 min)

**File**: `src/infrastructure/config/settings.py`

**Add validation method**:
```python
def validate_speech_services(self) -> None:
    """Validate speech service configuration.

    Raises:
        ValueError: If real adapters requested but config incomplete
    """
    if not self.use_mock_stt:
        if not self.azure_speech_key:
            raise ValueError("AZURE_SPEECH_KEY required when USE_MOCK_STT=false")
        if not self.azure_speech_region:
            raise ValueError("AZURE_SPEECH_REGION required when USE_MOCK_STT=false")

    if not self.use_mock_tts:
        if not self.azure_speech_key:
            raise ValueError("AZURE_SPEECH_KEY required when USE_MOCK_TTS=false")
        if not self.azure_speech_region:
            raise ValueError("AZURE_SPEECH_REGION required when USE_MOCK_TTS=false")
```

**Call in `get_settings()`**:
```python
@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.print_loaded_env_file()
    # settings.validate_speech_services()  # Optional: Fail fast at startup
    return settings
```

**Note**: Validation at DI time (Step 2-3) is preferred over startup validation. Allows running without Azure keys if only text mode used.

---

## Todo

### Implementation Tasks
- [ ] Add `_stt_port` and `_tts_port` instance variables to `Container.__init__`
- [ ] Implement `speech_to_text_port()` with mock/real toggle
- [ ] Validate `azure_speech_key` and `azure_speech_region` in STT method
- [ ] Implement `text_to_speech_port()` with mock/real toggle
- [ ] Validate `azure_speech_key` and `azure_speech_region` in TTS method
- [ ] Add logging import and logger statements
- [ ] (Optional) Add `validate_speech_services()` method to Settings

### Testing Tasks
- [ ] Test mock adapter selection (`use_mock_stt=True` → MockSTTAdapter)
- [ ] Test real adapter selection (`use_mock_stt=False` → AzureSpeechToTextAdapter)
- [ ] Test missing API key raises ValueError with clear message
- [ ] Test singleton caching (second call returns same instance)
- [ ] Test logging output includes region and language/voice

---

## Success Criteria

### Must Have
- ✅ `speech_to_text_port()` returns correct adapter based on `use_mock_stt` flag
- ✅ `text_to_speech_port()` returns correct adapter based on `use_mock_tts` flag
- ✅ Missing API key raises ValueError (not runtime error)
- ✅ Error messages include guidance (suggest mock mode)

### Should Have
- ✅ Singleton caching works (only one adapter instance)
- ✅ Logging at INFO level on adapter initialization
- ✅ Lazy imports (Azure SDK only imported when needed)

### Nice to Have
- ✅ Settings validation method (optional, for strict mode)
- ✅ Environment variable examples in error messages

---

## Risks

### Low Risks
1. **Import Errors**
   - **Risk**: Azure SDK not installed when real adapter requested
   - **Mitigation**: Lazy import with try/except, clear error message
   - **Fallback**: Document Azure SDK as optional dependency

2. **Singleton Issues**
   - **Risk**: Multiple container instances create duplicate adapters
   - **Mitigation**: Use `@lru_cache` on `get_container()` (already exists)
   - **Verification**: Test with `assert container.stt_port() is container.stt_port()`

---

## Security

### API Key Handling
- ✅ API keys loaded from environment variables only
- ✅ No logging of API key values (log region/voice only)
- ✅ Settings validation doesn't expose key in error messages

### Error Messages
- ✅ Error messages include env var name (`AZURE_SPEECH_KEY`), not value
- ✅ Suggest mock mode as fallback (reduces key exposure risk)

---

## Next Steps

After Phase 2 completion:
1. **Test with Real Azure API Key**: Manually verify Azure adapters initialize correctly
2. **Phase 3**: Implement WebSocket audio chunk handling
3. **Documentation**: Update `.env.example` with Azure Speech config

---

## References

- [Azure Speech SDK Installation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/quickstarts/setup-platform?pivots=programming-language-python)
- [DI Container Pattern](https://github.com/ets-labs/python-dependency-injector)
- [Lazy Singleton Pattern](https://refactoring.guru/design-patterns/singleton/python/example)
