import { useEffect, useState } from 'react';
import { getPosts } from '../api';
import Post from './Post';

export default function Feed({ currentUser }) {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPosts()
      .then(setPosts)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="glass rounded-2xl p-5 animate-pulse">
            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-xl bg-white/10"></div>
              <div className="flex-1 space-y-3">
                <div className="h-4 bg-white/10 rounded w-1/4"></div>
                <div className="h-4 bg-white/10 rounded w-3/4"></div>
                <div className="h-4 bg-white/10 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!posts.length) {
    return (
      <div className="glass rounded-2xl p-12 text-center">
        <span className="text-5xl block mb-4">✨</span>
        <h3 className="text-xl font-bold text-white mb-2">No posts yet</h3>
        <p className="text-gray-400">Be the first to share something with the community!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {posts.map((p, i) => (
        <div key={p.id} className="animate-fade-in" style={{ animationDelay: `${i * 50}ms` }}>
          <Post post={p} currentUser={currentUser} />
        </div>
      ))}
    </div>
  );
}
