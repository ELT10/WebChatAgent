# Manglish Response Improvement

## Problem

The previous implementation was producing very unnatural Manglish responses like:
```
Nicea — Ayurveda prakaram acne (muku/face pimples) orvalaku molam Agni-in debilitation, athu prthyekichch Pita dosha inbalance agathal nadakum.
```

This text is difficult to read and doesn't flow naturally for Malayalam speakers.

## Root Cause

The old approach:
1. User asks in **Manglish** (e.g., "acne treatment entha?")
2. Query translated to **English** for retrieval
3. LLM generates response in **English**
4. Response translated to **Malayalam script** (മലയാളം)
5. Malayalam script **transliterated** character-by-character to Latin alphabet

**The problem:** Step 5 produces unnatural output because simple character mapping doesn't preserve natural Manglish patterns. "ഊർവലക്ക് മൂലം" becomes "orvalaku molam" instead of natural Manglish like "oorvala kaaranam".

## Solution

**Let the LLM handle Manglish directly!**

New approach:
1. User asks in **Manglish** (e.g., "acne treatment entha?")
2. Detect language as Manglish
3. Query translated to **English** for retrieval (if needed)
4. **Pass instruction to LLM:** "Respond in natural Manglish"
5. LLM generates response directly in natural Manglish

## Changes Made

### 1. `orchestrator.py`
- Added `lang_instruction` parameter that tells the LLM what language to respond in
- For Manglish: `"Please respond in natural Manglish (Malayalam written in English script). Write it naturally as a Malayalam speaker would type in English letters, like 'acne treatment entha', 'ithinu enthokke options undu', etc."`
- Manglish queries now use **streaming** responses (same as English)
- Only Malayalam script queries require translation

### 2. `chatbot.py`
- Updated `get_response()` to accept `language_instruction` parameter
- Updated `get_response_stream()` to accept `language_instruction` parameter
- Language instruction appended to the system prompt/instructions: `"IMPORTANT: {language_instruction}"`

## Benefits

1. **Natural output:** LLM generates idiomatic Manglish that Malayalam speakers actually use
2. **Streaming support:** Manglish responses can now stream (faster UX)
3. **Less processing:** No unnecessary translation + transliteration steps
4. **Better quality:** LLM is better at generating natural language than character mapping
5. **Consistent style:** LLM maintains conversational Manglish style

## Example

**Before:**
```
orvalaku molam Agni-in debilitation, athu prthyekichch Pita dosha inbalance
```

**After (expected):**
```
Ayurveda prakaram acne oru Agni weakness kaaranam vannatha, visheshichu Pitta dosha imbalance aanu main reason. Treatment nammude clinicil und.
```

## Testing

To test the improvement:
1. Start the app: `python app.py`
2. Ask a question in Manglish: "acne treatment entha?"
3. Response should now be in natural Manglish that flows well

## Notes

- The translation service's transliteration code is still there for backwards compatibility
- Only Malayalam script (മലയാളം) queries still use translation
- English and Manglish queries both use streaming for better UX

