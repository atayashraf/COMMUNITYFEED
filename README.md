# Playto Community Feed

A production-quality prototype of a community feed application with threaded discussions and a dynamic leaderboard.

## 🌐 Live Demo

> **Frontend**: [https://frontend-eight-amber-64.vercel.app](https://frontend-eight-amber-64.vercel.app)  
> **Backend API**: *Deploy to Railway to get URL*

## Screenshots

### Feed View
![Feed](screenshots/feed.png)
*Main feed with posts, like buttons, and comment threads*

### Threaded Comments
![Comments](screenshots/comments.png)
*Reddit-style nested comments with infinite depth*

### Leaderboard
![Leaderboard](screenshots/leaderboard.png)
*Top 5 contributors by karma earned in last 24 hours*

## Tech Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Frontend**: React 18 + Tailwind CSS
- **Database**: SQLite (local dev) / PostgreSQL (production)

## UI Design

Modern dark theme with glass morphism effects:
- **Gradient background**: Deep blue/purple (`#1a1a2e` → `#0f3460`)
- **Glass cards**: Frosted blur with subtle borders
- **Accent colors**: Violet/Fuchsia gradients
- **Animations**: Smooth fade-in and slide transitions
- **Focus on readability**: High contrast, clear hierarchy

## Features

- 📝 **Feed**: Create text posts with like functionality
- 💬 **Threaded Comments**: Reddit-style nested comments with infinite depth
- ⭐ **Gamification**: Karma system (+5 for post likes, +1 for comment likes)
- 🏆 **Leaderboard**: Top 5 users by karma earned in last 24 hours
- 🔒 **Concurrency-safe**: DB-level constraints prevent double likes

## Design Philosophy

> **"Optimized for correctness and clarity over premature caching."**

Key tradeoffs made intentionally:
- Adjacency list over MPTT for fast comment writes
- Dynamic karma aggregation over cached fields for accuracy
- DB constraints over application-level checks for race-condition safety

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser (optional, for admin)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The API will be available at http://localhost:8000/api/

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at http://localhost:5173/

### Running Tests

```bash
cd backend
python manage.py test feed
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/posts/` | GET | List all posts (feed) |
| `/api/posts/` | POST | Create a new post |
| `/api/posts/{id}/` | GET | Get post with comment tree |
| `/api/posts/{id}/like/` | POST | Like a post |
| `/api/posts/{id}/like/` | DELETE | Unlike a post |
| `/api/posts/{id}/comments/` | GET | Get comments for a post |
| `/api/posts/{id}/comments/` | POST | Create a comment |
| `/api/comments/{id}/like/` | POST | Like a comment |
| `/api/comments/{id}/like/` | DELETE | Unlike a comment |
| `/api/leaderboard/` | GET | Get top 5 users (24h karma) |
| `/api/users/` | GET/POST | List or create users |

## Project Structure

```
CommunityTalks/
├── backend/
│   ├── config/             # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── feed/               # Main application
│   │   ├── models.py       # Database models
│   │   ├── services.py     # Business logic
│   │   ├── serializers.py  # DRF serializers
│   │   ├── views.py        # API views
│   │   ├── urls.py         # URL routing
│   │   └── tests.py        # Unit tests
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── Feed.jsx
│   │   │   ├── Post.jsx
│   │   │   ├── CommentTree.jsx
│   │   │   ├── Leaderboard.jsx
│   │   │   ├── CreatePost.jsx
│   │   │   └── UserSelector.jsx
│   │   ├── api.js          # API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── README.md
├── EXPLAINER.md
└── docker-compose.yml
```

## Architecture Decisions

See [EXPLAINER.md](EXPLAINER.md) for detailed explanations of:
- Comment tree modeling and N+1 prevention
- Leaderboard query implementation
- AI audit with bug fixes

## License

MIT
