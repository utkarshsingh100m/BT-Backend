# Buddy Tools - Backend

Flask API backend for Buddy Tools with AI chat and contact form functionality.

## 🚀 Quick Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/buddy-tools-backend)

### One-Click Setup

1. Click "Deploy" button above
2. Connect your GitHub account
3. Add environment variable:
   - `OPENROUTER_API_KEY` = your OpenRouter API key
4. Deploy!
5. Copy your deployment URL (e.g., `https://your-project.vercel.app`)

## 📋 Features

- **AI Chat API** - Streaming responses with GPT-4o via OpenRouter
- **Contact Form API** - Save contact submissions
- **Health Check** - Monitor API status
- **CORS Enabled** - Works with any frontend

## 🛠️ Tech Stack

- **Framework:** Flask 3.0
- **AI:** OpenRouter (GPT-4o)
- **Database:** SQLite (development) / PostgreSQL (production)
- **Deployment:** Vercel Serverless Functions

## 📁 Project Structure

```
backend/
├── api/
│   └── index.py          # Vercel entrypoint
├── app/
│   └── chat_api.py       # Main Flask application
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
└── README.md            # This file
```

## ⚙️ Local Development

### Prerequisites

- Python 3.8+
- pip

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/buddy-tools-backend.git
cd buddy-tools-backend
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment**

```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

4. **Run the server**

```bash
python app/chat_api.py
```

Server runs on `http://localhost:5000`

## 🌐 API Endpoints

### POST `/api/chat`

Stream AI chat responses

**Request:**

```json
{
	"message": "Explain photosynthesis",
	"conversationHistory": []
}
```

**Response:** Server-Sent Events (SSE)

### POST `/api/contact`

Save contact form submission

**Request:**

```json
{
	"name": "John Doe",
	"email": "john@example.com",
	"message": "Great tool!"
}
```

**Response:**

```json
{
	"success": true,
	"message": "Message sent successfully"
}
```

### GET `/api/health`

Check API status

**Response:**

```json
{
	"status": "OK",
	"message": "Chat API is running",
	"api_key": "Configured",
	"database": "Connected"
}
```

## 🔑 Environment Variables

Create a `.env` file:

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxx
PORT=5000
```

### Get OpenRouter API Key

1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up / Sign in
3. Go to [Keys](https://openrouter.ai/keys)
4. Create new key
5. Copy and paste into `.env`

## 🚀 Deployment

### Vercel (Recommended)

1. **Install Vercel CLI**

```bash
npm install -g vercel
```

2. **Login**

```bash
vercel login
```

3. **Deploy**

```bash
vercel
```

4. **Set environment variables**

```bash
vercel env add OPENROUTER_API_KEY production
```

5. **Deploy to production**

```bash
vercel --prod
```

### Alternative: Heroku

```bash
# Install Heroku CLI
heroku login
heroku create buddy-tools-api
heroku config:set OPENROUTER_API_KEY=your-key
git push heroku main
```

## 🔗 Connect to Frontend

After deployment, you'll get a URL like:

```
https://buddy-tools-backend.vercel.app
```

Use this in your frontend configuration:

```javascript
// frontend/assets/js/config.js
const API_BASE_URL = "https://buddy-tools-backend.vercel.app";
```

## 🧪 Testing

### Test Health Endpoint

```bash
curl https://your-backend.vercel.app/api/health
```

### Test Chat Endpoint

```bash
curl -X POST https://your-backend.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

## 📝 Notes

### Database

- **Development:** SQLite (file-based)
- **Production:** Consider PostgreSQL for persistence
- **Vercel:** Serverless functions don't persist SQLite

### Limitations

- Cold starts on serverless
- 10-second timeout on Vercel free tier
- No file storage (use cloud storage for uploads)

## 🔒 Security

- API keys in environment variables
- CORS configured for your frontend domain
- Input validation on all endpoints
- SQL injection prevention with parameterized queries

## 📚 Documentation

- [API Documentation](../docs/API.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md)

## 📄 License

MIT License - see [LICENSE](../LICENSE)

## 👥 Team

**Team GenerateZ**

- Utkarsh Singh - Project Manager
- Gaurav Chauhan - Backend Developer
- Praveen Mishra - Frontend Developer
- Sanjeet Kumar Prasad - Frontend Developer

## 📞 Support

- **Email:** work4generatez@gmail.com
- **Issues:** GitHub Issues

---

**Made with ❤️ by Team GenerateZ**
