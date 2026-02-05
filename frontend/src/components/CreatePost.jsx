import { useState } from 'react';
import { createPost } from '../api';

const AVATAR_COLORS = {
  a: 'from-violet-500 to-purple-500',
  b: 'from-blue-500 to-cyan-500',
  c: 'from-emerald-500 to-teal-500',
  d: 'from-orange-500 to-amber-500',
  e: 'from-pink-500 to-rose-500',
};

function getAvatarColor(name) {
  const firstChar = name[0]?.toLowerCase() || 'a';
  return AVATAR_COLORS[firstChar] || 'from-violet-500 to-fuchsia-500';
}

export default function CreatePost({ currentUser, onPostCreated }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [focused, setFocused] = useState(false);

  const submit = async e => {
    e.preventDefault();
    if (!content.trim()) return;
    setLoading(true);
    await createPost(content.trim());
    setContent('');
    setLoading(false);
    setFocused(false);
    onPostCreated();
  };

  return (
    <form
      onSubmit={submit}
      className={`glass rounded-2xl p-5 transition-all duration-300 ${focused ? 'ring-2 ring-violet-500/50' : ''}`}
    >
      <div className="flex gap-4">
        {/* Avatar */}
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${getAvatarColor(currentUser)} flex items-center justify-center text-white font-bold text-lg shadow-lg flex-shrink-0`}>
          {currentUser[0].toUpperCase()}
        </div>

        {/* Input */}
        <div className="flex-1 space-y-4">
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => !content && setFocused(false)}
            placeholder="Share something with the community..."
            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 resize-none focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20 transition-all"
            rows={focused ? 4 : 2}
          />

          {/* Actions */}
          <div className={`flex items-center justify-between transition-all ${focused ? 'opacity-100' : 'opacity-0 h-0 overflow-hidden'}`}>
            <div className="flex gap-2">
              <button type="button" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </button>
              <button type="button" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>

            <button
              disabled={!content.trim() || loading}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white font-medium text-sm hover:shadow-lg hover:shadow-violet-500/25 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none flex items-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  Posting...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  Post
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
