# Phase 1: Adapter Signature Alignment

**Phase ID**: Phase 1
**Duration**: 2-3 hours
**Dependencies**: None
**Risk Level**: Low

---

## Context

Current adapters (Azure STT/TTS) don't match port interface signatures exactly, violating Liskov Substitution Principle and preventing polymorphism.

**Critical Issues**:
1. **TTS Signature Mismatch**:
   - Port: `synthesize_speech(text, voice, speed) → bytes`
   - Azure Adapter: `synthesize_speech(text, language, voice) → bytes` (extra `language` param)

2. **Available Voices Return Type**:
   - Port: `get_available_voices() → list[str]`
   - Azure Adapter: `list_available_voices(language) → list[dict]` (different name, params, return type)

3. **Mock Adapter Inconsistency**:
   - Mock TTS: `get_available_voices() → list[str]` (matches port)
   - Azure TTS: `list_available_voices(language) → list[dict]` (doesn't match)

---

## Overview

Refactor Azure Speech adapters to match port contracts exactly. Update port interfaces where adapter flexibility is needed.

**Strategy**:
- Remove `language` param from `synthesize_speech()` → derive from voice name
- Rename/fix `list_available_voices()` → `get_available_voices()`
- Update return types to match port contracts
- Ensure mock adapters match real adapters

---

## Key Insights

### Design Decision: Voice Name vs Language Param

**Problem**: Azure TTS uses both language code and voice name, but port only has voice param.

**Solution**: Voice names are locale-specific (e.g., "en-US-JennyNeural", "vi-VN-HoaiMyNeural"), so language is redundant.

**Implementation**:
```python
# BEFORE (mismatch)
async def synthesize_speech(text, language, voice) → bytes:
    selected_voice = voice or DEFAULT_VOICES.get(language, self.default_voice)

# AFTER (matches port)
async def synthesize_speech(text, voice, speed) → bytes:
    # Voice name includes language (e.g., "en-US-JennyNeural")
    # No language param needed - extract from voice if needed
    selected_voice = voice or self.default_voice
```

### Design Decision: Available Voices Return Type

**Problem**: Port has `list[str]`, but Azure returns rich metadata (name, locale, gender, voice_type).

**Solution**: Update port to return `list[dict]` for maximum flexibility.

**Rationale**:
- Frontend may want to display voice gender, locale, type
- Richer metadata enables better voice selection UX
- Still backwards compatible (can extract `name` field)

---

## Requirements

### Functional
- ✅ Azure STT adapter matches `SpeechToTextPort` signature exactly
- ✅ Azure TTS adapter matches `TextToSpeechPort` signature exactly
- ✅ Mock STT adapter matches `SpeechToTextPort` signature exactly
- ✅ Mock TTS adapter matches `TextToSpeechPort` signature exactly
- ✅ All adapters pass `isinstance(adapter, Port)` check

### Non-Functional
- ✅ No breaking changes to existing functionality
- ✅ Mypy type checking passes with no errors
- ✅ All adapter methods have complete docstrings
- ✅ Parameter types match port types (bytes vs str, etc.)

---

## Architecture

### Port Interface Updates

**TextToSpeechPort** (`src/domain/ports/text_to_speech_port.py`):

```python
from abc import ABC, abstractmethod

class TextToSpeechPort(ABC):
    """Interface for text-to-speech operations."""

    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
    ) -> bytes:
        """Convert text to speech audio.

        Args:
            text: Text to synthesize
            voice: Voice name (e.g., "en-US-AriaNeural", locale-specific)
            speed: Speaking rate multiplier (0.5-2.0, default 1.0)

        Returns:
            WAV audio bytes (16kHz mono)
        """
        pass

    @abstractmethod
    async def save_speech_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-AriaNeural",
        speed: float = 1.0,
    ) -> str:
        """Convert text to speech and save to file.

        Args:
            text: Text to synthesize
            output_path: Path where audio file should be saved
            voice: Voice name (locale-specific)
            speed: Speaking rate multiplier (0.5-2.0)

        Returns:
            Path to saved audio file
        """
        pass

    @abstractmethod
    async def get_available_voices(self) -> list[dict]:
        """Get list of available voices with metadata.

        Returns:
            List of dicts with keys: name, locale, gender, voice_type
            Example: [
                {
                    "name": "en-US-AriaNeural",
                    "locale": "en-US",
                    "gender": "Female",
                    "voice_type": "Neural"
                },
                ...
            ]
        """
        pass
```

**No changes needed** for `SpeechToTextPort` (already matches).

---

## Implementation Steps

### Step 1: Update TextToSpeechPort Interface (15 min)

**File**: `src/domain/ports/text_to_speech_port.py`

**Changes**:
1. Update `get_available_voices()` return type: `list[str]` → `list[dict]`
2. Add docstring explaining dict structure (keys: name, locale, gender, voice_type)

### Step 2: Update AzureTTSAdapter (30 min)

**File**: `src/adapters/speech/azure_tts_adapter.py`

**Changes**:

1. **Remove `language` param from `synthesize_speech()`**:
```python
# BEFORE
async def synthesize_speech(
    self,
    text: str,
    language: str = "en-US",
    voice: Optional[str] = None,
) -> bytes:

# AFTER
async def synthesize_speech(
    self,
    text: str,
    voice: str = "en-US-AriaNeural",
    speed: float = 1.0,
) -> bytes:
    """Convert text to speech audio using Azure Speech Services.

    Args:
        text: Text to synthesize
        voice: Voice name (locale-specific, e.g., "en-US-JennyNeural")
        speed: Speaking rate multiplier (0.5-2.0, default 1.0)

    Returns:
        Audio data as bytes (WAV format)
    """
    # Select voice (use param or default)
    selected_voice = voice or self.default_voice

    # Configure voice
    self.speech_config.speech_synthesis_voice_name = selected_voice

    # Configure speaking rate via SSML if speed != 1.0
    if speed != 1.0:
        # Generate SSML with prosody rate
        ssml = self._create_ssml_with_speed(text, selected_voice, speed)
        result = speech_synthesizer.speak_ssml_async(ssml).get()
    else:
        result = speech_synthesizer.speak_text_async(text).get()

    # Return audio bytes
    return result.audio_data
```

2. **Add speed support via SSML**:
```python
def _create_ssml_with_speed(
    self,
    text: str,
    voice: str,
    speed: float,
) -> str:
    """Create SSML with speaking rate adjustment.

    Args:
        text: Text to synthesize
        voice: Voice name
        speed: Speed multiplier (0.5 = 50% slower, 2.0 = 100% faster)

    Returns:
        SSML markup string
    """
    # Convert speed multiplier to percentage
    rate_percent = f"{int((speed - 1.0) * 100):+d}%"  # e.g., 1.2 → "+20%"

    ssml = f"""
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="{voice}">
            <prosody rate="{rate_percent}">
                {text}
            </prosody>
        </voice>
    </speak>
    """
    return ssml.strip()
```

3. **Remove `language` param from `save_speech_to_file()`**:
```python
# BEFORE
async def save_speech_to_file(
    self,
    text: str,
    output_path: str,
    language: str = "en-US",
    voice: Optional[str] = None,
) -> str:

# AFTER
async def save_speech_to_file(
    self,
    text: str,
    output_path: str,
    voice: str = "en-US-AriaNeural",
    speed: float = 1.0,
) -> str:
    # Same implementation as synthesize_speech, but save to file
    # ...
```

4. **Rename `list_available_voices()` → `get_available_voices()`**:
```python
# BEFORE
async def list_available_voices(
    self,
    language: Optional[str] = None,
) → list[dict]:

# AFTER
async def get_available_voices(self) -> list[dict]:
    """Get list of available voices with metadata.

    Returns:
        List of dicts: [{name, locale, gender, voice_type}, ...]
    """
    # Create synthesizer
    speech_synthesizer = speechsdk.SpeechSynthesizer(...)

    # Get voice list (Azure SDK call)
    result = speech_synthesizer.get_voices_async().get()

    # Extract voices
    voices = []
    for voice in result.voices:
        voices.append({
            "name": voice.short_name,  # e.g., "en-US-AriaNeural"
            "locale": voice.locale,    # e.g., "en-US"
            "gender": voice.gender.name,  # e.g., "Female"
            "voice_type": voice.voice_type.name,  # e.g., "Neural"
        })
    return voices
```

### Step 3: Update MockTTSAdapter (20 min)

**File**: `src/adapters/mock/mock_tts_adapter.py`

**Changes**:

1. **Add `speed` param to `synthesize_speech()`**:
```python
async def synthesize_speech(
    self,
    text: str,
    voice: str = "en-US-AriaNeural",
    speed: float = 1.0,
) -> bytes:
    """Mock speech synthesis with proper WAV structure.

    Args:
        text: Text to synthesize
        voice: Voice name (ignored in mock)
        speed: Speaking rate (used to adjust audio length)

    Returns:
        WAV audio bytes (16kHz mono, 16-bit PCM)
    """
    # Estimate duration based on text and speed
    word_count = len(text.split())
    duration_seconds = (word_count / 150.0) * 60.0 / speed  # Adjust for speed
    duration_seconds = max(duration_seconds, 0.5)

    # Generate silent WAV
    return self._create_wav_bytes(
        sample_rate=16000,
        num_channels=1,
        bits_per_sample=16,
        num_samples=int(16000 * duration_seconds),
    )
```

2. **Add `speed` param to `save_speech_to_file()`**:
```python
async def save_speech_to_file(
    self,
    text: str,
    output_path: str,
    voice: str = "en-US-AriaNeural",
    speed: float = 1.0,
) -> str:
    audio_bytes = await self.synthesize_speech(text, voice, speed)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    return output_path
```

3. **Update `get_available_voices()` to return `list[dict]`**:
```python
async def get_available_voices(self) -> list[dict]:
    """Get list of mock voices with minimal metadata.

    Returns:
        List of dicts with name, locale, gender, voice_type
    """
    return [
        {
            "name": "en-US-AriaNeural",
            "locale": "en-US",
            "gender": "Female",
            "voice_type": "Neural",
        },
        {
            "name": "en-US-JennyNeural",
            "locale": "en-US",
            "gender": "Female",
            "voice_type": "Neural",
        },
        {
            "name": "en-US-GuyNeural",
            "locale": "en-US",
            "gender": "Male",
            "voice_type": "Neural",
        },
        {
            "name": "en-GB-SoniaNeural",
            "locale": "en-GB",
            "gender": "Female",
            "voice_type": "Neural",
        },
        {
            "name": "en-GB-RyanNeural",
            "locale": "en-GB",
            "gender": "Male",
            "voice_type": "Neural",
        },
    ]
```

### Step 4: Verify STT Adapters (10 min)

**Files**:
- `src/adapters/speech/azure_stt_adapter.py`
- `src/adapters/mock/mock_stt_adapter.py`

**Verification**:
- Check signatures match `SpeechToTextPort` exactly
- `transcribe_audio(audio_bytes: bytes, language: str) → dict[str, Any]` ✅
- `transcribe_stream(audio_stream: bytes, language: str) → dict[str, Any]` ✅
- `detect_language(audio_bytes: bytes) → str | None` ✅

**No changes needed** (already correct).

### Step 5: Type Checking & Linting (15 min)

**Commands**:
```bash
# Type checking
mypy src/adapters/speech/ src/adapters/mock/mock_*_adapter.py

# Linting
ruff check src/adapters/speech/ src/adapters/mock/

# Format
black src/adapters/speech/ src/adapters/mock/
```

**Expected Output**: No errors, all checks pass.

---

## Todo

### Implementation Tasks
- [ ] Update `TextToSpeechPort.get_available_voices()` return type to `list[dict]`
- [ ] Remove `language` param from `AzureTTSAdapter.synthesize_speech()`
- [ ] Add `speed` param support via SSML in `AzureTTSAdapter`
- [ ] Remove `language` param from `AzureTTSAdapter.save_speech_to_file()`
- [ ] Rename `list_available_voices()` → `get_available_voices()` in `AzureTTSAdapter`
- [ ] Add `speed` param to `MockTTSAdapter.synthesize_speech()`
- [ ] Update `MockTTSAdapter.get_available_voices()` to return `list[dict]`
- [ ] Verify `AzureSTTAdapter` matches port signature (no changes needed)
- [ ] Verify `MockSTTAdapter` matches port signature (no changes needed)
- [ ] Run mypy type checking
- [ ] Run ruff linting
- [ ] Run black formatting

### Validation Tasks
- [ ] Test `synthesize_speech()` with different speed values (0.5, 1.0, 2.0)
- [ ] Test `get_available_voices()` returns list of dicts with required keys
- [ ] Test mock and real adapters have identical signatures
- [ ] Verify `isinstance(adapter, Port)` passes for all adapters

---

## Success Criteria

### Must Have
- ✅ All adapter signatures match port interfaces exactly
- ✅ Mypy passes with no type errors
- ✅ Ruff linting passes
- ✅ No breaking changes to existing functionality

### Should Have
- ✅ Speed param works correctly (SSML prosody rate)
- ✅ Available voices return rich metadata
- ✅ Mock adapters provide realistic test data

### Nice to Have
- ✅ Docstrings updated with examples
- ✅ Type hints complete on all methods

---

## Risks

### Low Risks
1. **SSML Speed Conversion**
   - **Risk**: Speed multiplier to percentage conversion incorrect
   - **Mitigation**: Test with known values (0.5 → "-50%", 1.2 → "+20%")
   - **Test**: `assert _create_ssml_with_speed(1.5) == "+50%"`

2. **Voice Name Extraction**
   - **Risk**: Azure SDK voice names may not include locale
   - **Mitigation**: Use `voice.short_name` (includes locale prefix)
   - **Verification**: Check Azure docs, test with real API

---

## Security

### No Security Impact
- Changes are signature refactoring only
- No new external dependencies
- No changes to API key handling

---

## Next Steps

After Phase 1 completion:
1. **Phase 2**: Implement DI container with mock/real toggle
2. **Manual Test**: Verify Azure TTS with real API key
3. **Documentation**: Update architecture docs with new signatures

---

## References

- [Azure TTS Voice List](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [SSML Prosody Rate](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice#adjust-prosody)
- [Clean Architecture: Adapter Pattern](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
