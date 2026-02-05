import { useState } from 'react';
import { likePost, unlikePost, getComments, createComment } from '../api';
import CommentTree from './CommentTree';

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

function timeAgo(date) {
  const seconds = Math.floor((new Date() - new Date(date)) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function Post({ post, currentUser }) {
  const [liked, setLiked] = useState(post.is_liked);
  const [likes, setLikes] = useState(post.like_count);
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [likeAnimating, setLikeAnimating] = useState(false);

  const toggleLike = async () => {
    setLikeAnimating(true);
    setTimeout(() => setLikeAnimating(false), 300);
    
    if (liked) {
      await unlikePost(post.id);
      setLikes(l => l - 1);
    } else {
      await likePost(post.id);
      setLikes(l => l + 1);
    }
    setLiked(!liked);
  };

  const loadComments = async () => {
    const data = await getComments(post.id);
    setComments(data);
  };

  const submitComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim() || submitting) return;
    setSubmitting(true);
    try {
      await createComment(post.id, newComment.trim());
      setNewComment('');
      await loadComments();
    } catch (err) {
      console.error('Failed to post comment:', err);
    }
    setSubmitting(false);
  };

  const isOwnPost = post.author.username === currentUser;

  return (
    <article className="glass rounded-2xl overflow-hidden hover:border-white/20 transition-all duration-300">
      {/* Header */}
      <div className="p-5">
        <div className="flex gap-4 items-start">
          {/* Avatar */}
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${getAvatarColor(post.author.username)} flex items-center justify-center text-white font-bold text-lg shadow-lg flex-shrink-0`}>
            {post.author.username[0].toUpperCase()}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-white">{post.author.username}</span>
              {isOwnPost && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-violet-500/20 text-violet-400 border border-violet-500/30">
                  You
                </span>
              )}
              <span className="text-gray-500 text-sm">•</span>
              <span className="text-gray-500 text-sm">{timeAgo(post.created_at)}</span>
            </div>
            <p className="text-gray-200 whitespace-pre-wrap leading-relaxed">{post.content}</p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="px-5 py-3 border-t border-white/5 flex gap-2">
        {/* Like button */}
        <button
          onClick={toggleLike}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${likeAnimating ? 'animate-pulse-once' : ''}
            ${liked 
              ? 'bg-gradient-to-r from-pink-500/20 to-rose-500/20 text-pink-400 border border-pink-500/30' 
              : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-transparent'
            }`}
        >
          <svg className={`w-5 h-5 transition-transform ${liked ? 'scale-110' : ''}`} fill={liked ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
          <span className="font-medium">{likes}</span>
          {liked && <span className="text-xs">+5 karma</span>}
        </button>

        {/* Comments button */}
        <button
          onClick={async () => {
            setShowComments(!showComments);
            if (!comments.length) await loadComments();
          }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all
            ${showComments 
              ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-400 border border-blue-500/30' 
              : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-transparent'
            }`}
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <span className="font-medium">Comments</span>
          {comments.length > 0 && <span className="text-xs bg-white/10 px-1.5 py-0.5 rounded-full">{comments.length}</span>}
        </button>

        {/* Share button (decorative) */}
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white transition-all border border-transparent ml-auto">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
        </button>
      </div>

      {/* Comments section */}
      {showComments && (
        <div className="border-t border-white/5 bg-black/20">
          {/* Add new comment form */}
          <form onSubmit={submitComment} className="p-4 border-b border-white/5">
            <div className="flex gap-3">
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${getAvatarColor(currentUser)} flex items-center justify-center text-white text-sm font-bold flex-shrink-0`}>
                {currentUser[0].toUpperCase()}
              </div>
              <div className="flex-1 flex gap-2">
                <input
                  value={newComment}
                  onChange={e => setNewComment(e.target.value)}
                  placeholder="Write a comment..."
                  className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:border-violet-500/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20 transition-all"
                />
                <button
                  type="submit"
                  disabled={!newComment.trim() || submitting}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-violet-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? (
                    <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                    </svg>
                  ) : 'Post'}
                </button>
              </div>
            </div>
          </form>

          {/* Comments list */}
          <div className="p-4">
            {comments.length > 0 ? (
              <CommentTree
                comments={comments}
                postId={post.id}
                currentUser={currentUser}
                onChange={loadComments}
              />
            ) : (
              <div className="text-center py-6">
                <span className="text-2xl block mb-2">💬</span>
                <p className="text-gray-500 text-sm">No comments yet. Start the discussion!</p>
              </div>
            )}
          </div>
        </div>
      )}
    </article>
  );
}
