import { useState } from 'react';
import { setCurrentUser as saveUser } from '../api';

const AVATAR_COLORS = {
  a: 'from-violet-500 to-purple-500',
  b: 'from-blue-500 to-cyan-500',
  c: 'from-emerald-500 to-teal-500',
  d: 'from-orange-500 to-amber-500',
  e: 'from-pink-500 to-rose-500',
  f: 'from-indigo-500 to-blue-500',
  g: 'from-green-500 to-emerald-500',
  h: 'from-red-500 to-orange-500',
};

function getAvatarColor(name) {
  const firstChar = name[0]?.toLowerCase() || 'a';
  return AVATAR_COLORS[firstChar] || 'from-violet-500 to-fuchsia-500';
}

export default function UserSelector({ currentUser, onUserChange }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(currentUser);

  const submit = e => {
    e.preventDefault();
    if (!value.trim()) return;
    saveUser(value.trim());
    onUserChange(value.trim());
    setEditing(false);
  };

  if (editing) {
    return (
      <form onSubmit={submit} className="flex gap-2 animate-fade-in">
        <input
          className="px-4 py-2 rounded-xl bg-white/10 border border-white/20 text-white text-sm focus:border-violet-400 focus:outline-none focus:ring-2 focus:ring-violet-400/20 transition-all"
          placeholder="Enter username..."
          value={value}
          onChange={e => setValue(e.target.value)}
          autoFocus
        />
        <button className="px-4 py-2 rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-violet-500/25 transition-all">
          Save
        </button>
        <button 
          type="button"
          onClick={() => setEditing(false)}
          className="px-3 py-2 rounded-xl bg-white/5 text-gray-400 text-sm hover:bg-white/10 transition-all"
        >
          ✕
        </button>
      </form>
    );
  }

  return (
    <button
      onClick={() => setEditing(true)}
      className="flex items-center gap-3 px-4 py-2 rounded-xl glass glass-hover transition-all group"
    >
      <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${getAvatarColor(currentUser)} flex items-center justify-center text-white font-bold shadow-lg`}>
        {currentUser[0].toUpperCase()}
      </div>
      <div className="text-left">
        <div className="text-sm font-medium text-white">{currentUser}</div>
        <div className="text-xs text-gray-400 group-hover:text-violet-400 transition-colors">Click to switch</div>
      </div>
      <svg className="w-4 h-4 text-gray-400 group-hover:text-violet-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
}
