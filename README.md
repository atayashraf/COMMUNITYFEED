Playto Community Feed

Playto Community Feed is a community discussion platform prototype where users can create posts, join threaded discussions, and compete on a leaderboard based on their activity.

The goal of this project was to build a simple, scalable community feed system with clean architecture and a modern UI.

🌐 Live Demo

Frontend: https://frontend-eight-amber-64.vercel.app


Tech Stack

Backend: Django 4.2, Django REST Framework
Frontend: React 18, Tailwind CSS
Database: SQLite (development), PostgreSQL (production)

Features

📝 Post Feed – Users can create posts and like them

💬 Threaded Comments – Reddit-style nested comment system

⭐ Karma System – Engagement-based points system

🏆 Leaderboard – Top 5 users based on karma earned in the last 24 hours

🔒 Safe Likes System – Database constraints prevent duplicate likes

Design Approach

This project focuses on correctness and clean architecture rather than premature optimization.

Uses adjacency list structure for comment threads

Dynamic karma calculation to keep scores accurate

Database-level constraints to avoid race conditions

Running the Project
Backend
cd backend
python -m venv venv
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
Frontend
cd frontend
npm install
npm run dev
