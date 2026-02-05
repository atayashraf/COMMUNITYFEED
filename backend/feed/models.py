"""
Database models for Community Feed.

Design Decisions:
-----------------
1. COMMENT TREE: Adjacency List model (parent FK) - simple and works well with 
   recursive prefetching. For deep trees, we use a custom prefetch approach.

2. LIKES: Separate PostLike/CommentLike tables instead of GenericForeignKey.
   Reasons:
   - Cleaner database constraints (FK integrity)
   - More efficient queries (no content_type joins)
   - DB-level unique constraints work properly

3. KARMA EVENTS: Every like creates a KarmaEvent record. This enables:
   - Historical tracking (when was karma earned)
   - Dynamic leaderboard (sum events from last 24h)
   - Audit trail for gamification

4. CONCURRENCY: Using unique_together constraints at DB level to prevent
   double likes even under race conditions.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Post(models.Model):
    """
    A text post in the community feed.
    """
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at}"

    @property
    def like_count(self):
        """Return cached like count if available, otherwise query."""
        if hasattr(self, '_like_count'):
            return self._like_count
        return self.likes.count()


class Comment(models.Model):
    """
    A comment on a post, with support for infinite nesting via self-referential FK.
    
    Tree Structure:
    - parent=None means this is a top-level comment on the post
    - parent=<Comment> means this is a reply to that comment
    
    We use an adjacency list model. For efficient tree loading, we prefetch
    all comments for a post and build the tree in Python.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Depth tracking for display purposes (computed on save)
    depth = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post_id}"

    def save(self, *args, **kwargs):
        """Calculate depth based on parent chain."""
        if self.parent:
            self.depth = self.parent.depth + 1
        else:
            self.depth = 0
        super().save(*args, **kwargs)

    @property
    def like_count(self):
        """Return cached like count if available, otherwise query."""
        if hasattr(self, '_like_count'):
            return self._like_count
        return self.likes.count()


class PostLike(models.Model):
    """
    A like on a post. Unique constraint prevents double-liking.
    
    Karma: +5 to post author
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='post_likes'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # DB-level constraint prevents double likes even under race conditions
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_post_like'
            )
        ]

    def __str__(self):
        return f"{self.user.username} liked Post {self.post_id}"


class CommentLike(models.Model):
    """
    A like on a comment. Unique constraint prevents double-liking.
    
    Karma: +1 to comment author
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_likes'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'comment'],
                name='unique_comment_like'
            )
        ]

    def __str__(self):
        return f"{self.user.username} liked Comment {self.comment_id}"


class KarmaEvent(models.Model):
    """
    A karma transaction record. Created whenever karma is earned.
    
    This is the SOURCE OF TRUTH for karma calculations.
    We NEVER store a cached karma total on the User model.
    
    Leaderboard query sums these events filtered by created_at > 24h ago.
    """
    KARMA_POST_LIKE = 'post_like'
    KARMA_COMMENT_LIKE = 'comment_like'
    
    KARMA_TYPES = [
        (KARMA_POST_LIKE, 'Post Like'),
        (KARMA_COMMENT_LIKE, 'Comment Like'),
    ]
    
    # User who RECEIVED the karma (post/comment author)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='karma_events'
    )
    # Amount of karma earned (5 for post like, 1 for comment like)
    amount = models.IntegerField()
    # Type of event for auditing
    event_type = models.CharField(max_length=20, choices=KARMA_TYPES)
    # When the karma was earned
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: link back to the source like for auditing
    post_like = models.ForeignKey(
        PostLike,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='karma_event'
    )
    comment_like = models.ForeignKey(
        CommentLike,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='karma_event'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Index for efficient leaderboard query
            models.Index(fields=['created_at', 'user']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} earned {self.amount} karma ({self.event_type})"
