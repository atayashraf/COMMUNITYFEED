import { useEffect, useState } from 'react';
import { getLeaderboard } from '../api';

const RANK_STYLES = {
  0: { bg: 'from-yellow-500 to-amber-500', icon: '🥇', shadow: 'shadow-yellow-500/30' },
  1: { bg: 'from-gray-300 to-gray-400', icon: '🥈', shadow: 'shadow-gray-400/30' },
  2: { bg: 'from-orange-600 to-orange-700', icon: '🥉', shadow: 'shadow-orange-500/30' },
};

const AVATAR_COLORS = ['from-violet-500 to-purple-500', 'from-blue-500 to-cyan-500', 'from-emerald-500 to-teal-500', 'from-pink-500 to-rose-500', 'from-orange-500 to-amber-500'];

export default function Leaderboard({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getLeaderboard()
      .then(setUsers)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="glass rounded-2xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-white/10 rounded w-2/3"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-white/5 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="text-xl">🏆</span>
          <div>
            <h2 className="font-bold text-white">Top Contributors</h2>
            <p className="text-xs text-gray-400">Last 24 hours</p>
          </div>
        </div>
      </div>

      {/* List */}
      <div className="p-3 space-y-2">
        {users.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <span className="text-3xl block mb-2">🌟</span>
            <p className="text-sm">No karma earned yet today</p>
            <p className="text-xs mt-1">Be the first to contribute!</p>
          </div>
        ) : (
          users.map((u, i) => {
            const isCurrentUser = u.username === currentUser;
            const rankStyle = RANK_STYLES[i];
            
            return (
              <div
                key={u.username}
                className={`flex items-center gap-3 p-3 rounded-xl transition-all animate-slide-in
                  ${isCurrentUser 
                    ? 'bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 border border-violet-500/30' 
                    : 'bg-white/5 hover:bg-white/10'
                  }`}
                style={{ animationDelay: `${i * 50}ms` }}
              >
                {/* Rank */}
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold
                  ${rankStyle 
                    ? `bg-gradient-to-br ${rankStyle.bg} ${rankStyle.shadow} shadow-lg` 
                    : 'bg-white/10 text-gray-400'
                  }`}
                >
                  {rankStyle ? rankStyle.icon : i + 1}
                </div>

                {/* Avatar */}
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${AVATAR_COLORS[i % AVATAR_COLORS.length]} flex items-center justify-center text-white font-bold shadow-lg`}>
                  {u.username[0].toUpperCase()}
                </div>

                {/* Name */}
                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium truncate ${isCurrentUser ? 'text-violet-300' : 'text-white'}`}>
                    {u.username}
                    {isCurrentUser && <span className="ml-2 text-xs text-violet-400">(You)</span>}
                  </div>
                </div>

                {/* Karma */}
                <div className="text-right">
                  <div className={`text-lg font-bold ${isCurrentUser ? 'text-violet-400' : 'text-white'}`}>
                    {u.karma}
                  </div>
                  <div className="text-xs text-gray-500">karma</div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
