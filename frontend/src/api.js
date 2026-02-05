/**
 * API client for Community Feed backend.
 * 
 * Uses fetch API with consistent error handling.
 * For prototype: username is passed via X-Username header.
 */

const API_BASE = '/api';

/**
 * Get current username from localStorage or generate a random one.
 */
export function getCurrentUser() {
  let username = localStorage.getItem('username');
  if (!username) {
    username = `user_${Math.random().toString(36).substring(7)}`;
    localStorage.setItem('username', username);
  }
  return username;
}

/**
 * Set the current username.
 */
export function setCurrentUser(username) {
  localStorage.setItem('username', username);
}

/**
 * Common headers including username for auth simulation.
 */
function getHeaders() {
  return {
    'Content-Type': 'application/json',
    'X-Username': getCurrentUser(),
  };
}

/**
 * Generic API request handler with error handling.
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getHeaders(),
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || error.detail || `HTTP ${response.status}`);
  }
  
  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }
  
  return response.json();
}

// ============================================================================
// Posts API
// ============================================================================

/**
 * Fetch all posts (feed).
 */
export async function getPosts() {
  return apiRequest('/posts/');
}

/**
 * Create a new post.
 */
export async function createPost(content) {
  return apiRequest('/posts/', {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

/**
 * Get a single post with its comment tree.
 */
export async function getPost(postId) {
  return apiRequest(`/posts/${postId}/`);
}

/**
 * Like a post.
 */
export async function likePost(postId) {
  return apiRequest(`/posts/${postId}/like/`, {
    method: 'POST',
  });
}

/**
 * Unlike a post.
 */
export async function unlikePost(postId) {
  return apiRequest(`/posts/${postId}/like/`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Comments API
// ============================================================================

/**
 * Get comments for a post (nested tree structure).
 */
export async function getComments(postId) {
  return apiRequest(`/posts/${postId}/comments/`);
}

/**
 * Create a comment on a post.
 */
export async function createComment(postId, content, parentId = null) {
  return apiRequest(`/posts/${postId}/comments/`, {
    method: 'POST',
    body: JSON.stringify({ content, parent_id: parentId }),
  });
}

/**
 * Delete a comment (only your own).
 */
export async function deleteComment(commentId) {
  return apiRequest(`/comments/${commentId}/`, {
    method: 'DELETE',
  });
}

/**
 * Like a comment.
 */
export async function likeComment(commentId) {
  return apiRequest(`/comments/${commentId}/like/`, {
    method: 'POST',
  });
}

/**
 * Unlike a comment.
 */
export async function unlikeComment(commentId) {
  return apiRequest(`/comments/${commentId}/like/`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Leaderboard API
// ============================================================================

/**
 * Get leaderboard (top users by karma in last 24 hours).
 */
export async function getLeaderboard(hours = 24, limit = 5) {
  return apiRequest(`/leaderboard/?hours=${hours}&limit=${limit}`);
}

// ============================================================================
// Users API
// ============================================================================

/**
 * Get all users.
 */
export async function getUsers() {
  return apiRequest('/users/');
}

/**
 * Create or get a user.
 */
export async function createUser(username) {
  return apiRequest('/users/', {
    method: 'POST',
    body: JSON.stringify({ username }),
  });
}
