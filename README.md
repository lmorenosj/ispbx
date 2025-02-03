# ISPBX Manager

A Python-based application to manage and monitor Asterisk PJSIP configuration.

## Project Structure
```
ispbx/
├── backend/
│   ├── src/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
└── frontend/
```

## Backend Setup

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
cd src
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

## API Endpoints

- GET `/`: Welcome message
- GET `/pjsip/config`: Get current PJSIP configuration
- GET `/pjsip/status`: Get PJSIP status

## Note
- The application needs access to `/etc/asterisk/pjsip.conf`
- Make sure you have appropriate permissions to read the configuration file
- For production use, consider implementing proper authentication and security measures
