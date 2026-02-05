import { useState } from 'react';
import { createComment, likeComment, unlikeComment, deleteComment } from '../api';

const AVATAR_COLORS = ['from-violet-500 to-purple-500', 'from-blue-500 to-cyan-500', 'from-emerald-500 to-teal-500', 'from-pink-500 to-rose-500', 'from-orange-500 to-amber-500', 'from-indigo-500 to-blue-500'];

function getAvatarColor(name) {
  const index = name.charCodeAt(0) % AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
}

function timeAgo(date) {
  const seconds = Math.floor((new Date() - new Date(date)) / 1000);
  if (seconds < 60) return 'now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  return `${days}d`;
}

export default function CommentTree({ comments, postId, currentUser, onChange, depth = 0 }) {
  return (
    <div className={depth ? 'ml-6 pl-4 border-l-2 border-white/10' : ''}>
      {comments.map((c, i) => (
        <div key={c.id} className="animate-fade-in" style={{ animationDelay: `${i * 30}ms` }}>
          <Comment
            comment={c}
            postId={postId}
            currentUser={currentUser}
            onChange={onChange}
            depth={depth}
          />
        </div>
      ))}
    </div>
  );
}

function Comment({ comment, postId, currentUser, onChange, depth }) {
  const [liked, setLiked] = useState(comment.is_liked);
  const [likes, setLikes] = useState(comment.like_count);
  const [reply, setReply] = useState('');
  const [showReply, setShowReply] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const isAuthor = comment.author.username === currentUser;

  const toggleLike = async () => {
    if (liked) {
      await unlikeComment(comment.id);
      setLikes(l => l - 1);
    } else {
      await likeComment(comment.id);
      setLikes(l => l + 1);
    }
    setLiked(!liked);
  };

  const submitReply = async e => {
    e.preventDefault();
    if (!reply.trim() || submitting) return;
    setSubmitting(true);
    await createComment(postId, reply, comment.id);
    setReply('');
    setShowReply(false);
    setSubmitting(false);
    onChange();
  };

  const handleDelete = async () => {
    if (!confirm('Delete this comment?')) return;
    setDeleting(true);
    try {
      await deleteComment(comment.id);
      onChange();
    } catch (err) {
      alert('Failed to delete: ' + err.message);
      setDeleting(false);
    }
  };

  const childCount = comment.children?.length || 0;

  return (
    <div className="py-2">
      <div className="group">
        {/* Comment card */}
        <div className="flex gap-3">
          {/* Avatar */}
          <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${getAvatarColor(comment.author.username)} flex items-center justify-center text-white text-xs font-bold flex-shrink-0`}>
            {comment.author.username[0].toUpperCase()}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="bg-white/5 rounded-xl px-4 py-3 hover:bg-white/[0.07] transition-colors">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium text-white text-sm">{comment.author.username}</span>
                {isAuthor && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-violet-500/20 text-violet-400">
                    You
                  </span>
                )}
                <span className="text-gray-500 text-xs">{timeAgo(comment.created_at)}</span>
                
                {/* Delete button */}
                {isAuthor && (
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="ml-auto opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-all p-1 rounded hover:bg-red-500/10"
                    title="Delete comment"
                  >
                    {deleting ? (
                      <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    )}
                  </button>
                )}
              </div>
              <p className="text-gray-300 text-sm whitespace-pre-wrap">{comment.content}</p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1 mt-1 ml-2">
              {/* Like */}
              <button 
                onClick={toggleLike} 
                className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all
                  ${liked 
                    ? 'text-pink-400 bg-pink-500/10' 
                    : 'text-gray-500 hover:text-pink-400 hover:bg-pink-500/10'
                  }`}
              >
                <svg className="w-3.5 h-3.5" fill={liked ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                {likes > 0 && <span>{likes}</span>}
              </button>

              {/* Reply */}
              <button 
                onClick={() => setShowReply(!showReply)} 
                className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all
                  ${showReply 
                    ? 'text-blue-400 bg-blue-500/10' 
                    : 'text-gray-500 hover:text-blue-400 hover:bg-blue-500/10'
                  }`}
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                </svg>
                Reply
              </button>

              {/* Collapse */}
              {childCount > 0 && (
                <button 
                  onClick={() => setCollapsed(!collapsed)} 
                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs text-gray-500 hover:text-white hover:bg-white/10 transition-all"
                >
                  <svg className={`w-3.5 h-3.5 transition-transform ${collapsed ? '' : 'rotate-90'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                  {collapsed ? `Show ${childCount} ${childCount === 1 ? 'reply' : 'replies'}` : 'Hide'}
                </button>
              )}
            </div>

            {/* Reply form */}
            {showReply && (
              <form onSubmit={submitReply} className="mt-3 flex gap-2 animate-fade-in">
                <div className={`w-6 h-6 rounded-md bg-gradient-to-br ${getAvatarColor(currentUser)} flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0`}>
                  {currentUser[0].toUpperCase()}
                </div>
                <div className="flex-1 flex gap-2">
                  <input
                    value={reply}
                    onChange={e => setReply(e.target.value)}
                    className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-violet-500/50 focus:outline-none focus:ring-1 focus:ring-violet-500/20 transition-all"
                    placeholder={`Reply to ${comment.author.username}...`}
                    autoFocus
                  />
                  <button 
                    type="submit"
                    disabled={!reply.trim() || submitting}
                    className="px-3 py-2 rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white text-xs font-medium hover:shadow-lg hover:shadow-violet-500/25 transition-all disabled:opacity-50"
                  >
                    {submitting ? '...' : 'Reply'}
                  </button>
                  <button 
                    type="button"
                    onClick={() => { setShowReply(false); setReply(''); }}
                    className="px-2 py-2 rounded-lg bg-white/5 text-gray-400 text-xs hover:bg-white/10 transition-all"
                  >
                    ✕
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>

      {/* Children */}
      {!collapsed && comment.children && comment.children.length > 0 && (
        <CommentTree
          comments={comment.children}
          postId={postId}
          currentUser={currentUser}
          onChange={onChange}
          depth={depth + 1}
        />
      )}
    </div>
  );
}
