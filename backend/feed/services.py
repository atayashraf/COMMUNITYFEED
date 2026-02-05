"""
Business logic services for Community Feed.

Why Services?
-------------
Keeping business logic in services (not views/serializers) because:
1. Testability: Services are easy to unit test
2. Reusability: Logic can be called from multiple endpoints
3. Clarity: Views handle HTTP, services handle domain logic
4. Transactions: Complex operations are easier to wrap atomically
"""
from django.db import transaction, IntegrityError
from django.db.models import Sum, Count, Prefetch
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

from .models import Post, Comment, PostLike, CommentLike, KarmaEvent


# =============================================================================
# KARMA CONSTANTS
# =============================================================================
KARMA_POST_LIKE = 5
KARMA_COMMENT_LIKE = 1


# =============================================================================
# POST SERVICES
# =============================================================================

def create_post(author: User, content: str) -> Post:
    """
    Create a new post.
    
    Args:
        author: The user creating the post
        content: The post content text
        
    Returns:
        The created Post instance
    """
    return Post.objects.create(author=author, content=content)


def get_feed_posts(user: User = None):
    """
    Fetch posts with optimized queries for the feed.
    
    Optimization Strategy:
    - select_related for author (1 JOIN instead of N queries)
    - annotate like_count (1 subquery instead of N queries)
    - prefetch user's likes to show "liked" state
    
    Args:
        user: Optional current user to check if they liked posts
        
    Returns:
        QuerySet of posts with annotations
    """
    queryset = Post.objects.select_related('author').annotate(
        _like_count=Count('likes')
    )
    
    if user and user.is_authenticated:
        # Prefetch user's likes to determine "liked" state without N+1
        queryset = queryset.prefetch_related(
            Prefetch(
                'likes',
                queryset=PostLike.objects.filter(user=user),
                to_attr='user_likes'
            )
        )
    
    return queryset


# =============================================================================
# COMMENT SERVICES
# =============================================================================

def create_comment(post: Post, author: User, content: str, parent: Comment = None) -> Comment:
    """
    Create a comment on a post, optionally as a reply to another comment.
    
    Args:
        post: The post to comment on
        author: The user creating the comment
        content: The comment text
        parent: Optional parent comment for nesting
        
    Returns:
        The created Comment instance
    """
    return Comment.objects.create(
        post=post,
        author=author,
        content=content,
        parent=parent
    )


def get_comments_for_post(post_id: int, user: User = None) -> list:
    """
    Fetch all comments for a post and build a nested tree structure.
    
    N+1 Prevention Strategy:
    ------------------------
    Instead of recursively fetching children (which would cause N+1),
    we fetch ALL comments for the post in ONE query with:
    - select_related('author', 'parent') - joins for related data
    - annotate like count
    - prefetch user's likes
    
    Then we build the tree structure in Python.
    
    This approach:
    - 1 query for all comments (regardless of depth)
    - 1 query for like counts (via annotation)
    - 1 query for user's likes (via prefetch) if user provided
    
    Total: 2-3 queries for ANY number of comments/depth
    
    Args:
        post_id: ID of the post
        user: Optional current user for "liked" state
        
    Returns:
        List of top-level comments with nested 'children' lists
    """
    # Single query to get ALL comments for this post
    queryset = Comment.objects.filter(post_id=post_id).select_related(
        'author', 'parent'
    ).annotate(
        _like_count=Count('likes')
    ).order_by('created_at')
    
    if user and user.is_authenticated:
        queryset = queryset.prefetch_related(
            Prefetch(
                'likes',
                queryset=CommentLike.objects.filter(user=user),
                to_attr='user_likes'
            )
        )
    
    comments = list(queryset)
    
    # Build tree in Python (O(n) time complexity)
    return _build_comment_tree(comments)


def _build_comment_tree(comments: list) -> list:
    """
    Build nested comment tree from flat list.
    
    Algorithm:
    1. Create a mapping of comment_id -> comment object
    2. Add empty 'children' list to each comment
    3. For each comment, if it has a parent, add it to parent's children
    4. Return only top-level comments (parent=None)
    
    Time Complexity: O(n) where n = number of comments
    Space Complexity: O(n) for the mapping
    
    Args:
        comments: Flat list of Comment objects
        
    Returns:
        List of top-level comments with nested children
    """
    if not comments:
        return []
    
    # Step 1: Create lookup map and initialize children
    comment_map = {}
    for comment in comments:
        comment.children = []  # Add children attribute dynamically
        comment_map[comment.id] = comment
    
    # Step 2: Build parent-child relationships
    top_level = []
    for comment in comments:
        if comment.parent_id is None:
            top_level.append(comment)
        else:
            parent = comment_map.get(comment.parent_id)
            if parent:
                parent.children.append(comment)
    
    return top_level


# =============================================================================
# LIKE SERVICES
# =============================================================================

class AlreadyLikedException(Exception):
    """Raised when user tries to like something they already liked."""
    pass


@transaction.atomic
def like_post(user: User, post: Post) -> PostLike:
    """
    Like a post and create karma event for the post author.
    
    Concurrency Safety:
    -------------------
    1. DB unique constraint on (user, post) prevents duplicates
    2. transaction.atomic ensures like + karma are created together
    3. IntegrityError is caught and converted to meaningful exception
    
    Args:
        user: The user liking the post
        post: The post to like
        
    Returns:
        The created PostLike instance
        
    Raises:
        AlreadyLikedException: If user already liked this post
    """
    try:
        # Create the like (will fail if duplicate due to unique constraint)
        like = PostLike.objects.create(user=user, post=post)
        
        # Create karma event for post author (NOT the liker)
        # Only if author is not the same as liker (no self-karma)
        if post.author_id != user.id:
            KarmaEvent.objects.create(
                user=post.author,
                amount=KARMA_POST_LIKE,
                event_type=KarmaEvent.KARMA_POST_LIKE,
                post_like=like
            )
        
        return like
        
    except IntegrityError:
        # Unique constraint violation = already liked
        raise AlreadyLikedException("You have already liked this post")


@transaction.atomic
def unlike_post(user: User, post: Post) -> bool:
    """
    Remove a like from a post and delete associated karma event.
    
    Args:
        user: The user unliking the post
        post: The post to unlike
        
    Returns:
        True if like was removed, False if not found
    """
    try:
        like = PostLike.objects.get(user=user, post=post)
        # Delete karma event first (due to FK constraint)
        KarmaEvent.objects.filter(post_like=like).delete()
        like.delete()
        return True
    except PostLike.DoesNotExist:
        return False


@transaction.atomic
def like_comment(user: User, comment: Comment) -> CommentLike:
    """
    Like a comment and create karma event for the comment author.
    
    Same concurrency safety pattern as like_post.
    
    Args:
        user: The user liking the comment
        comment: The comment to like
        
    Returns:
        The created CommentLike instance
        
    Raises:
        AlreadyLikedException: If user already liked this comment
    """
    try:
        like = CommentLike.objects.create(user=user, comment=comment)
        
        # Create karma event for comment author (NOT the liker)
        if comment.author_id != user.id:
            KarmaEvent.objects.create(
                user=comment.author,
                amount=KARMA_COMMENT_LIKE,
                event_type=KarmaEvent.KARMA_COMMENT_LIKE,
                comment_like=like
            )
        
        return like
        
    except IntegrityError:
        raise AlreadyLikedException("You have already liked this comment")


@transaction.atomic
def unlike_comment(user: User, comment: Comment) -> bool:
    """
    Remove a like from a comment and delete associated karma event.
    
    Args:
        user: The user unliking the comment
        comment: The comment to unlike
        
    Returns:
        True if like was removed, False if not found
    """
    try:
        like = CommentLike.objects.get(user=user, comment=comment)
        KarmaEvent.objects.filter(comment_like=like).delete()
        like.delete()
        return True
    except CommentLike.DoesNotExist:
        return False


# =============================================================================
# LEADERBOARD SERVICES
# =============================================================================

def get_leaderboard(hours: int = 24, limit: int = 5) -> list:
    """
    Get top users by karma earned in the last N hours.
    
    THE QUERY EXPLAINED:
    --------------------
    This is the critical aggregation query for the leaderboard.
    
    SQL equivalent:
    ```sql
    SELECT 
        user_id,
        auth_user.username,
        SUM(amount) as total_karma
    FROM feed_karmaevent
    INNER JOIN auth_user ON feed_karmaevent.user_id = auth_user.id
    WHERE created_at >= NOW() - INTERVAL '24 hours'
    GROUP BY user_id, auth_user.username
    ORDER BY total_karma DESC
    LIMIT 5;
    ```
    
    Django ORM breakdown:
    1. KarmaEvent.objects.filter(created_at__gte=cutoff)
       - Filter to last 24 hours
    
    2. .values('user_id', 'user__username')
       - GROUP BY user_id and username
       - We include username in values() to get it in one query
    
    3. .annotate(total_karma=Sum('amount'))
       - SUM(amount) for each group
    
    4. .order_by('-total_karma')[:limit]
       - ORDER BY total_karma DESC LIMIT 5
    
    Why this approach:
    - Single query with JOIN (not N+1)
    - Proper GROUP BY (user_id only, with username for display)
    - Index on (created_at, user_id) makes filtering efficient
    
    Args:
        hours: Time window in hours (default 24)
        limit: Number of top users to return (default 5)
        
    Returns:
        List of dicts with user_id, username, total_karma
    """
    cutoff = timezone.now() - timedelta(hours=hours)
    
    leaderboard = (
        KarmaEvent.objects
        .filter(created_at__gte=cutoff)
        .values('user_id', 'user__username')
        .annotate(total_karma=Sum('amount'))
        .order_by('-total_karma')[:limit]
    )
    
    # Convert to list of clean dicts
    return [
        {
            'user_id': entry['user_id'],
            'username': entry['user__username'],
            'karma': entry['total_karma']
        }
        for entry in leaderboard
    ]


def get_user_total_karma(user: User) -> int:
    """
    Get total karma for a user (all time).
    
    This is a simple aggregation query.
    
    Args:
        user: The user to get karma for
        
    Returns:
        Total karma amount
    """
    result = KarmaEvent.objects.filter(user=user).aggregate(
        total=Sum('amount')
    )
    return result['total'] or 0
