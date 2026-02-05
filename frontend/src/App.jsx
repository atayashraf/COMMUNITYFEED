import { useState } from 'react';
import Feed from './components/Feed';
import Leaderboard from './components/Leaderboard';
import CreatePost from './components/CreatePost';
import UserSelector from './components/UserSelector';
import { getCurrentUser } from './api';

export default function App() {
  const [currentUser, setCurrentUser] = useState(getCurrentUser());
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="min-h-screen text-white">
      {/* Header */}
      <header className="glass sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
                <span className="text-xl">💬</span>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
                  Playto Community
                </h1>
                <p className="text-xs text-gray-400">Connect • Share • Grow</p>
              </div>
            </div>

            {/* User selector */}
            <UserSelector currentUser={currentUser} onUserChange={setCurrentUser} />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex gap-8">
          {/* Left column - Feed */}
          <div className="flex-1 max-w-2xl space-y-6">
            <CreatePost
              currentUser={currentUser}
              onPostCreated={() => setRefreshKey(k => k + 1)}
            />
            <Feed key={refreshKey} currentUser={currentUser} />
          </div>

          {/* Right column - Sidebar */}
          <aside className="w-80 hidden lg:block space-y-6">
            {/* Leaderboard */}
            <Leaderboard currentUser={currentUser} />

            {/* Quick Stats */}
            <div className="glass rounded-2xl p-5">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                How Karma Works
              </h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center text-sm">
                    ❤️
                  </div>
                  <div>
                    <div className="text-sm font-medium">Post Like</div>
                    <div className="text-xs text-emerald-400">+5 Karma</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-sm">
                    💬
                  </div>
                  <div>
                    <div className="text-sm font-medium">Comment Like</div>
                    <div className="text-xs text-emerald-400">+1 Karma</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="text-center text-xs text-gray-500 pt-4">
              <p>Built with ❤️ for Playto</p>
              <p className="mt-1">Django + React + Tailwind</p>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
