# AI Real Estate Showing Assistant

A modern real estate assistant that helps agents analyze properties, save reports, and interact via **voice and AI**.

## Features

- **Property Search** - By address or listing URL (Zillow, etc.)
- **Verified Data** - Multi-source property profiles from RentCast + Census
- **Voice Interaction** - Ask questions verbally, get spoken answers
- **AI Briefings** - Auto-generated property summaries for agents
- **Smart Caching** - Reduces API costs by caching property data
- **Beautiful UI** - Next.js dashboard with real-time property analysis

## What's Included

- **FastAPI Backend** - RESTful API with voice + LLM endpoints
- **Next.js Frontend** - Responsive property dashboard
- **RentCast Integration** - Real property data (bedrooms, baths, value estimates)
- **OpenAI Integration** - Voice (Whisper/TTS) + LLM (GPT-4) for Q&A
- **SQLite Database** - Property history and caching
- **Docker Support** - Easy deployment with docker-compose

## Quick Start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Add API keys to .env
echo "RENTCAST_API_KEY=your-key" >> .env
echo "OPENAI_API_KEY=your-key" >> .env

# Start server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Quick Start Script

```bash
./start.sh  # Starts both backend and frontend
```

## Configuration

### Required API Keys

1. **RentCast** - Get at https://app.rentcast.io/
   - Property data, valuations, comparables

2. **OpenAI** - Get at https://platform.openai.com/api-keys
   - Voice features (Whisper, TTS)
   - AI assistant (GPT-4)

Add to `backend/.env`:

```bash
RENTCAST_API_KEY=your-rentcast-key
OPENAI_API_KEY=sk-your-openai-key
ENABLE_VOICE_FEATURES=true
```

## Voice Features

See [VOICE_FEATURES.md](VOICE_FEATURES.md) for complete guide.

### Example Workflow

1. Agent enters property address
2. AI generates briefing: "This is a 3-bed, 2-bath home..."
3. Agent asks: "What about the roof?"
4. AI responds: "According to records, roof was replaced in 2020..."
5. Agent is fully briefed before the showing!

### Voice API Endpoints

- **GET** `/voice/properties/{id}/briefing` - Text briefing
- **GET** `/voice/properties/{id}/briefing/audio` - Audio briefing (MP3)
- **POST** `/voice/transcribe` - Speech-to-text
- **POST** `/voice/speak` - Text-to-speech  
- **POST** `/voice/properties/ask- Ask questions (text)
- **POST** `/voice/properties/ask/voice` - Ask questions (voice in/out)

## Documentation

- [Voice Features Guide](VOICE_FEATURES.md) - Complete voice/LLM setup
- [Fixes & Setup](FIXES_AND_SETUP.md) - Troubleshooting and configuration
- [API Docs](http://localhost:8000/docs) - Interactive Swagger UI (when server running)

## Project Structure

```
real_estate_ai_assistant_v2/
├── backend/
│   ├── app/
│   │   ├── core/              # Configuration
│   │   ├── db/                # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   │   ├── property_service.py
│   │   │   ├── voice_service.py        # NEW: Voice features
│   │   │   └── llm_assistant_service.py # NEW: AI assistant
│   │   └── integrations/      # External APIs
│   │       ├── rentcast.py    # RentCast API
│   │       └── census/        # Census geocoding
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Main dashboard
│   │   └── globals.css
│   └── package.json
├── docs/                      # Additional documentation
├── README.md                  # This file
├── VOICE_FEATURES.md          # Voice feature guide
├── FIXES_AND_SETUP.md         # Troubleshooting
└── start.sh                   # Quick start script
```

## Development

### Testing

```bash
cd backend
pytest tests/
```

### API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database

The app uses SQLite for simplicity. Schema auto-creates on startup.

To reset the database:
```bash
rm backend/app.db
# Restart server - tables will recreate
```

## Deployment

See [docker-compose.yml](docker-compose.yml) for containerized deployment.

```bash
docker-compose up -d
```

## Roadmap

- [ ] Voice UI in frontend (microphone, waveforms)
- [ ] Conversation history persistence
- [ ] Additional data sources (FEMA flood, school ratings)
- [ ] Mobile app (React Native)
- [ ] Multi-user support with authentication
- [ ] Property comparison tool
- [ ] Neighborhood insights

## Contributing

This is a personal project, but suggestions and issues are welcome!

## License

MIT - Do whatever you want with it

## Support

- RentCast API: https://developers.rentcast.io/
- OpenAI API: https://platform.openai.com/docs/

---

**Built for real estate agents who want to be fully prepared before every showing.**
- Verified facts and AI analysis are separated by design.
