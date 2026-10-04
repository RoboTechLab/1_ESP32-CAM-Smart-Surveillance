# ESP32-CAM Smart Surveillance System

An AI-powered smart surveillance system developed by RoboTech Labs.

The system uses computer vision to detect people in a camera feed, record detection events, capture surveillance snapshots, send Telegram alerts, and display system information through a Flask web dashboard.

## Current Development Status

The project is currently being developed and tested using a laptop webcam.

The final system is intended to use an ESP32-CAM as the surveillance camera together with an RCWL-0513 microwave motion sensor.

## Features

- Real-time camera monitoring
- YOLO11n person detection
- Multiple-person detection
- Person-count monitoring
- Best-frame snapshot capture
- SQLite event logging
- Telegram detection alerts
- Flask web dashboard
- Live camera feed
- Recent detection event history
- Detection confidence display

## System Architecture

Camera Feed
    |
    v
OpenCV
    |
    v
YOLO11n Person Detection
    |
    +----> Event Manager
    |          |
    |          +----> Snapshot
    |          +----> SQLite Database
    |          +----> Telegram Alert
    |
    +----> Flask Dashboard

## Project Structure

```text
smart_surveillance/
|
├── app.py
├── camera_service.py
├── config.py
├── database.py
├── detector.py
├── event_manager.py
├── telegram_bot.py
|
├── templates/
│   └── index.html
|
├── static/
│   └── style.css
|
├── events/
|
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Requirements

- Python 3
- Git
- Webcam for the current development version
- Internet connection for initial package/model installation
- Internet connection for Telegram notifications

VS Code is recommended for development but is not required.

## Installation

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
```

Enter the project directory:

```bash
cd ESP32-CAM-Smart-Surveillance
```

Create a Python virtual environment:

```bash
py -3 -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Telegram Configuration

Copy:

```text
.env.example
```

and rename the copy to:

```text
.env
```

Add your Telegram configuration:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Do not commit the `.env` file to GitHub.

## Running the System

Start the application:

```bash
python app.py
```

Open the dashboard in a browser:

```text
http://127.0.0.1:5000
```

The YOLO model may be downloaded automatically when the application is run for the first time.

## Current Hardware

Development:

- Laptop/PC
- USB or integrated webcam

Planned final hardware:

- ESP32-CAM
- Camera module
- RCWL-0513 microwave motion sensor

## Future Development

- Dashboard statistics
- Improved multi-person monitoring
- System reliability testing
- ESP32-CAM video stream integration
- RCWL-0513 motion-trigger integration
- Deployment configuration
- Final client-ready system

## Security

Sensitive information such as Telegram bot tokens must be stored in `.env`.

Never commit API tokens, passwords, credentials, or other secrets to the repository.

## Developed By

**RoboTech Labs**

Mechatronics | Embedded Systems | Computer Vision | AI | Robotics