# Voice & LLM Features Guide

## Overview

Your Real Estate AI Assistant now includes **voice interaction and LLM-powered Q&A** features! Agents can:

1. **Input an address** (type or Zillow link)
2. **Listen to an AI briefing** about the property
3. **Ask questions verbally** and get spoken answers
4. **Have a conversation** with context-aware responses

---

## Setup

### 1. Get an OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy it to your `.env` file:

```bash
OPENAI_API_KEY=sk-...your-key-here...
```

### 2. Install Dependencies

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

The new dependencies include:
- `openai` - OpenAI Python SDK
- `pydub` - Audio processing (optional, for advanced features)

### 3. Configure Voice Settings (Optional)

In `.env`, you can customize:

```bash
# Which GPT model to use for analysis
OPENAI_MODEL=gpt-4

# Text-to-Speech settings
OPENAI_TTS_MODEL=tts-1        # or tts-1-hd for higher quality
OPENAI_TTS_VOICE=alloy        # alloy, echo, fable, onyx, nova, shimmer

# Speech-to-Text model
OPENAI_WHISPER_MODEL=whisper-1

# Enable/disable voice features
ENABLE_VOICE_FEATURES=true
```

---

## Features

### 1. Property Briefing (Text)

**GET** `/voice/properties/{property_id}/briefing`

Get an AI-generated briefing about a property.

**Example Response:**
```json
{
  "briefing": "This is a 3-bedroom, 2-bathroom home at 5335 W Cardinal St in Rogers, Arkansas. Built in 2005, it offers 1,800 square feet of living space. The property is currently listed at $285,000, with an estimated market value around $275,000, suggesting it's fairly priced. Located in Benton County, this single-family home is in a desirable area with good schools nearby. The agent should highlight the modern amenities and recent updates when showing the property."
}
```

### 2. Property Briefing (Audio)

**GET** `/voice/properties/{property_id}/briefing/audio`

Get the briefing as spoken audio (MP3).

**Returns:** Audio file that plays directly in the browser or app.

**Example Usage:**
```html
<audio controls src="/voice/properties/1/briefing/audio"></audio>
```

### 3. Ask a Question (Text)

**POST** `/voice/properties/ask`

```json
{
  "property_id": 1,
  "question": "What's the school district like?",
  "conversation_history": [
    {"role": "user", "content": "How old is the house?"},
    {"role": "assistant", "content": "The house was built in 2005, making it about 21 years old."}
  ]
}
```

**Response:**
```json
{
  "answer": "This property is located in the Rogers School District, which is highly rated in Arkansas. Nearby schools include Elmwood Middle School and Rogers High School, both known for strong academics and extracurricular programs.",
  "audio_url": null
}
```

### 4. Speech-to-Text

**POST** `/voice/transcribe`

Upload an audio file and get back the transcribed text.

**Example (using curl):**
```bash
curl -X POST http://localhost:8000/voice/transcribe \
  -F "audio=@question.wav"
```

**Response:**
```json
{
  "text": "What's the neighborhood like?"
}
```

### 5. Text-to-Speech

**POST** `/voice/speak`

```json
{
  "text": "The neighborhood is quiet and family-friendly with several parks nearby."
}
```

**Returns:** MP3 audio file

### 6. Voice Q&A (Full Flow)

**POST** `/voice/properties/ask/voice?property_id=1`

Upload audio of your question, get back audio of the answer!

**Example:**
```bash
curl -X POST http://localhost:8000/voice/properties/ask/voice?property_id=1 \
  -F "audio=@my_question.wav" \
  --output answer.mp3
```

**Response Headers:**
- `X-Question`: The transcribed question text
- `X-Answer-Text`: The answer text
- Body: MP3 audio of the answer

---

## Use Case Flow

### Agent Preparation Workflow

1. **Agent arrives at office**, opens the app
2. **Enters property address** from listing
3. **Clicks "Get Briefing"** or **"Listen to Briefing"**
4. **AI speaks:** "This is a 3-bedroom home at..."
5. **Agent asks:** "What about the HVAC system?"
6. **AI responds:** "According to the property data, the HVAC was replaced in 2020..."
7. **Agent follows up:** "And the roof?"
8. **AI responds:** "The roof is original from 2005 and may need inspection..."

The agent is now fully briefed and ready for the showing!

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/voice/transcribe` | POST | Convert speech to text (Whisper) |
| `/voice/speak` | POST | Convert text to speech (TTS) |
| `/voice/properties/{id}/briefing` | GET | Get text briefing |
| `/voice/properties/{id}/briefing/audio` | GET | Get audio briefing |
| `/voice/properties/ask` | POST | Ask question (text in/out) |
| `/voice/properties/ask/voice` | POST | Ask question (voice in/out) |

---

## Frontend Integration (Coming Soon)

The frontend will include:

- **Microphone button** to record questions
- **Speaker button** to play AI responses
- **Auto-play briefing** when property loads
- **Conversation history** display
- **Waveform visualization** for audio

### Example React Component (Skeleton)

```tsx
function VoiceInteraction({ propertyId }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [answer, setAnswer] = useState("");

  const startRecording = () => {
    // Start microphone recording
    setIsRecording(true);
  };

  const stopRecording = async (audioBlob) => {
    setIsRecording(false);
    
    // Send to backend
    const formData = new FormData();
    formData.append("audio", audioBlob);
    
    const response = await fetch(
      `/voice/properties/ask/voice?property_id=${propertyId}`,
      {
        method: "POST",
        body: formData,
      }
    );
    
    // Get transcribed question from header
    const question = response.headers.get("X-Question");
    setTranscript(question);
    
    // Play the audio answer
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();
  };

  return (
    <div>
      <button onClick={isRecording ? stopRecording : startRecording}>
        {isRecording ? "Stop Recording" : "Ask a Question"}
      </button>
      {transcript && <p>You asked: {transcript}</p>}
    </div>
  );
}
```

---

## Voice Settings

### Available TTS Voices

- **alloy** - Neutral, balanced
- **echo** - Male, clear
- **fable** - British accent, storytelling
- **onyx** - Deep, authoritative
- **nova** - Female, warm
- **shimmer** - Soft, friendly

Change in `.env`:
```bash
OPENAI_TTS_VOICE=nova
```

### Model Options

- **gpt-4** - Best quality, slower, more expensive
- **gpt-4-turbo** - Faster, cheaper, still great
- **gpt-3.5-turbo** - Fastest, cheapest, good for basic Q&A

---

## Cost Estimates

### OpenAI Pricing (as of 2024)

- **Whisper (STT)**: $0.006 per minute of audio
- **TTS**: $15.00 per 1M characters (~$0.015 per briefing)
- **GPT-4**: $0.03 per 1K tokens (~$0.05 per conversation)

**Example:** 100 properties/day with briefing + 3 questions each:
- Briefings: 100 × $0.015 = $1.50
- Questions: 300 × $0.05 = $15.00
- **Total: ~$16.50/day**

---

## Troubleshooting

### "OpenAI API key not configured"
- Add `OPENAI_API_KEY=sk-...` to `.env`
- Restart the backend server

### "Voice features are disabled"
- Set `ENABLE_VOICE_FEATURES=true` in `.env`
- Restart the backend server

### Audio doesn't play
- Check browser console for errors
- Verify the response Content-Type is `audio/mpeg`
- Try downloading the file and playing locally

### Transcription is inaccurate
- Use higher quality audio (clear speech, low background noise)
- Save recordings as WAV or MP3
- Speak clearly and at moderate pace

---

## Next Steps

1. **Get OpenAI API key** and add to `.env`
2. **Test the endpoints** using the API docs at http://localhost:8000/docs
3. **Build the frontend UI** for voice interaction
4. **Train your agents** on how to use voice features

Happy voice-coding!
