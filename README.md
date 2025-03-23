# Travel Advisory App - MMVP (Massively Multiplayer Vibe Programming)

A Django-based travel advisory application that uses AI21's Maestro to provide intelligent travel recommendations and advice.

## Features

- Create and manage travel destinations
- Generate AI-powered travel advice using AI21's Maestro
- Get comprehensive information about:
  - Safety
  - Weather and best time to visit
  - Cultural considerations
  - Transportation options
  - Must-see attractions

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd travel-advisor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your AI21 API key:
```
AI21_API_KEY=your_api_key_here
DJANGO_SECRET_KEY=your_django_secret_key_here
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Run the development server:
```bash
python manage.py runserver
```

## API Endpoints

- `GET /api/destinations/`: List all destinations
- `POST /api/destinations/`: Create a new destination
- `GET /api/destinations/{id}/`: Get destination details
- `POST /api/destinations/{id}/generate_advice/`: Generate AI-powered travel advice
- `GET /api/advice/`: List all travel advice
- `GET /api/advice/{id}/`: Get specific travel advice

## Testing

Run the test suite:
```bash
pytest
```

## Dependencies

- Django
- Django REST Framework
- AI21 Maestro
- Python-dotenv
- Requests
- Pytest

## License

MIT License
