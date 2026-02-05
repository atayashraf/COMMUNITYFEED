"""
Tests for Community Feed application.

Focus on critical functionality:
1. Leaderboard 24-hour calculation
2. Double-like prevention (concurrency)
3. Comment tree building
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError, transaction
import threading

from .models import Post, Comment, PostLike, CommentLike, KarmaEvent
from . import services


class LeaderboardTests(TestCase):
    """
    Tests for the leaderboard feature.
    
    CRITICAL: The leaderboard must only count karma from the last 24 hours,
    calculated dynamically from KarmaEvent records.
    """
    
    def setUp(self):
        """Create test users and posts."""
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'pass123')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'pass123')
        self.user3 = User.objects.create_user('user3', 'user3@test.com', 'pass123')
        self.user4 = User.objects.create_user('user4', 'user4@test.com', 'pass123')  # Liker
        
        # Create posts for users 1, 2, 3
        self.post1 = Post.objects.create(author=self.user1, content='Post by user1')
        self.post2 = Post.objects.create(author=self.user2, content='Post by user2')
        self.post3 = Post.objects.create(author=self.user3, content='Post by user3')
    
    def test_leaderboard_only_counts_last_24_hours(self):
        """
        Verify that leaderboard ONLY includes karma from the last 24 hours.
        
        Setup:
        - user1 gets 5 karma NOW
        - user2 gets 5 karma 25 hours ago (should be EXCLUDED)
        - user3 gets 5 karma 12 hours ago (should be included)
        
        Expected: user1 and user3 on leaderboard, user2 NOT
        """
        # user1: karma earned NOW
        services.like_post(self.user4, self.post1)
        
        # user2: karma earned 25 hours ago (OUTSIDE 24h window)
        like2 = PostLike.objects.create(user=self.user4, post=self.post2)
        karma2 = KarmaEvent.objects.create(
            user=self.user2,
            amount=5,
            event_type=KarmaEvent.KARMA_POST_LIKE,
            post_like=like2
        )
        # Manually set created_at to 25 hours ago
        karma2.created_at = timezone.now() - timedelta(hours=25)
        karma2.save()
        
        # user3: karma earned 12 hours ago (INSIDE 24h window)
        like3 = PostLike.objects.create(user=self.user4, post=self.post3)
        karma3 = KarmaEvent.objects.create(
            user=self.user3,
            amount=5,
            event_type=KarmaEvent.KARMA_POST_LIKE,
            post_like=like3
        )
        karma3.created_at = timezone.now() - timedelta(hours=12)
        karma3.save()
        
        # Get leaderboard
        leaderboard = services.get_leaderboard(hours=24, limit=5)
        
        # Verify results
        usernames = [entry['username'] for entry in leaderboard]
        
        self.assertIn('user1', usernames, "user1 should be on leaderboard (karma now)")
        self.assertIn('user3', usernames, "user3 should be on leaderboard (karma 12h ago)")
        self.assertNotIn('user2', usernames, "user2 should NOT be on leaderboard (karma 25h ago)")
    
    def test_leaderboard_correct_karma_amounts(self):
        """
        Verify karma amounts are summed correctly.
        
        user1 gets:
        - 2 post likes = 10 karma
        user2 gets:
        - 1 post like = 5 karma
        - 1 comment like = 1 karma
        Total: 6 karma
        
        user1 should be first with 10, user2 second with 6
        """
        # Create another post for user1 and a comment for user2
        post1b = Post.objects.create(author=self.user1, content='Another post by user1')
        comment2 = Comment.objects.create(
            post=self.post2,
            author=self.user2,
            content='Comment by user2'
        )
        
        # Like both posts by user1 (user4 is the liker)
        services.like_post(self.user4, self.post1)  # +5 to user1
        services.like_post(self.user4, post1b)      # +5 to user1
        
        # Like post2 and comment2 (user3 is the liker)
        services.like_post(self.user3, self.post2)  # +5 to user2
        services.like_comment(self.user3, comment2) # +1 to user2
        
        leaderboard = services.get_leaderboard(hours=24, limit=5)
        
        # Verify order and amounts
        self.assertEqual(leaderboard[0]['username'], 'user1')
        self.assertEqual(leaderboard[0]['karma'], 10)
        
        self.assertEqual(leaderboard[1]['username'], 'user2')
        self.assertEqual(leaderboard[1]['karma'], 6)


class DoubleLikePreventionTests(TestCase):
    """
    Tests for preventing double likes.
    
    CRITICAL: Users must not be able to like the same post/comment twice.
    The unique constraint should prevent this even under race conditions.
    """
    
    def setUp(self):
        self.user = User.objects.create_user('liker', 'liker@test.com', 'pass123')
        self.author = User.objects.create_user('author', 'author@test.com', 'pass123')
        self.post = Post.objects.create(author=self.author, content='Test post')
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            content='Test comment'
        )
    
    def test_cannot_like_post_twice(self):
        """Attempting to like a post twice should raise AlreadyLikedException."""
        # First like should succeed
        services.like_post(self.user, self.post)
        
        # Second like should fail
        with self.assertRaises(services.AlreadyLikedException):
            services.like_post(self.user, self.post)
        
        # Verify only one like exists
        self.assertEqual(PostLike.objects.filter(user=self.user, post=self.post).count(), 1)
    
    def test_cannot_like_comment_twice(self):
        """Attempting to like a comment twice should raise AlreadyLikedException."""
        services.like_comment(self.user, self.comment)
        
        with self.assertRaises(services.AlreadyLikedException):
            services.like_comment(self.user, self.comment)
        
        self.assertEqual(CommentLike.objects.filter(user=self.user, comment=self.comment).count(), 1)
    
    def test_db_constraint_prevents_double_like(self):
        """
        Test that the database constraint itself prevents duplicates.
        This is the actual concurrency protection.
        """
        # Bypass service layer to test raw DB constraint
        PostLike.objects.create(user=self.user, post=self.post)
        
        with self.assertRaises(IntegrityError):
            PostLike.objects.create(user=self.user, post=self.post)
    
    def test_karma_created_only_once(self):
        """Verify karma is only created once even if like attempt is duplicated."""
        # First like creates karma
        services.like_post(self.user, self.post)
        initial_karma = KarmaEvent.objects.filter(user=self.author).count()
        
        # Second like attempt fails, no new karma
        try:
            services.like_post(self.user, self.post)
        except services.AlreadyLikedException:
            pass
        
        final_karma = KarmaEvent.objects.filter(user=self.author).count()
        self.assertEqual(initial_karma, final_karma)


class CommentTreeTests(TestCase):
    """
    Tests for comment tree building and retrieval.
    
    Verifies:
    1. Nested structure is correctly built
    2. No N+1 queries
    """
    
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@test.com', 'pass123')
        self.post = Post.objects.create(author=self.user, content='Test post')
        
        # Create a comment tree:
        # - comment1 (top level)
        #   - reply1a (child of comment1)
        #     - reply1a1 (child of reply1a)
        #   - reply1b (child of comment1)
        # - comment2 (top level)
        
        self.comment1 = Comment.objects.create(
            post=self.post, author=self.user, content='Top level 1'
        )
        self.reply1a = Comment.objects.create(
            post=self.post, author=self.user, content='Reply 1a',
            parent=self.comment1
        )
        self.reply1a1 = Comment.objects.create(
            post=self.post, author=self.user, content='Reply 1a1',
            parent=self.reply1a
        )
        self.reply1b = Comment.objects.create(
            post=self.post, author=self.user, content='Reply 1b',
            parent=self.comment1
        )
        self.comment2 = Comment.objects.create(
            post=self.post, author=self.user, content='Top level 2'
        )
    
    def test_tree_structure(self):
        """Verify comment tree is built with correct parent-child relationships."""
        tree = services.get_comments_for_post(self.post.id)
        
        # Should have 2 top-level comments
        self.assertEqual(len(tree), 2)
        
        # Find comment1 and verify its children
        comment1 = next(c for c in tree if c.id == self.comment1.id)
        self.assertEqual(len(comment1.children), 2)
        
        # Find reply1a and verify its child
        reply1a = next(c for c in comment1.children if c.id == self.reply1a.id)
        self.assertEqual(len(reply1a.children), 1)
        self.assertEqual(reply1a.children[0].id, self.reply1a1.id)
        
        # Verify comment2 has no children
        comment2 = next(c for c in tree if c.id == self.comment2.id)
        self.assertEqual(len(comment2.children), 0)
    
    def test_depth_is_set_correctly(self):
        """Verify depth is calculated correctly for nested comments."""
        self.assertEqual(self.comment1.depth, 0)
        self.assertEqual(self.reply1a.depth, 1)
        self.assertEqual(self.reply1a1.depth, 2)
        self.assertEqual(self.reply1b.depth, 1)
        self.assertEqual(self.comment2.depth, 0)
    
    def test_query_count_is_constant(self):
        """
        Verify fetching comment tree doesn't cause N+1 queries.
        Should be 2-3 queries regardless of comment count/depth.
        """
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        
        with CaptureQueriesContext(connection) as context:
            tree = services.get_comments_for_post(self.post.id)
            # Force evaluation of the tree
            _ = [c for c in tree]
        
        # Should be at most 3 queries:
        # 1. Fetch all comments with select_related
        # 2. Annotate like counts
        # 3. (Optional) prefetch user likes
        self.assertLessEqual(
            len(context), 3,
            f"Expected at most 3 queries, got {len(context)}: {[q['sql'] for q in context]}"
        )
