"""
DRF Serializers for Community Feed.

Philosophy:
-----------
Serializers handle data TRANSFORMATION only:
- Input validation
- JSON serialization
- Field mapping

Business logic lives in services.py, NOT here.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Post, Comment, PostLike, CommentLike, KarmaEvent


class UserSerializer(serializers.ModelSerializer):
    """Basic user info serializer."""
    
    class Meta:
        model = User
        fields = ['id', 'username']


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for comments with nested children support.
    
    The 'children' field is populated by the service layer after
    building the comment tree. This serializer handles the recursive
    structure by declaring children as a method field.
    """
    author = UserSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'parent', 'author', 'content',
            'created_at', 'depth', 'like_count', 'is_liked', 'children'
        ]
        read_only_fields = ['author', 'created_at', 'depth']
    
    def get_like_count(self, obj):
        """
        Return like count from annotation if available.
        This avoids N+1 queries since count is pre-computed.
        """
        if hasattr(obj, '_like_count'):
            return obj._like_count
        return obj.likes.count()
    
    def get_is_liked(self, obj):
        """
        Check if current user has liked this comment.
        Uses prefetched user_likes if available.
        """
        if hasattr(obj, 'user_likes'):
            return len(obj.user_likes) > 0
        
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_children(self, obj):
        """
        Recursively serialize children comments.
        Children are attached by _build_comment_tree() in services.
        """
        if hasattr(obj, 'children') and obj.children:
            # Pass context to nested serializer for is_liked to work
            return CommentSerializer(
                obj.children, 
                many=True, 
                context=self.context
            ).data
        return []


class CommentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a comment.
    Separate from CommentSerializer for cleaner input validation.
    """
    content = serializers.CharField(max_length=2000)
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_parent_id(self, value):
        """Validate that parent comment exists and belongs to same post."""
        if value is not None:
            post_id = self.context.get('post_id')
            try:
                parent = Comment.objects.get(id=value)
                if parent.post_id != post_id:
                    raise serializers.ValidationError(
                        "Parent comment must belong to the same post"
                    )
                return value
            except Comment.DoesNotExist:
                raise serializers.ValidationError("Parent comment not found")
        return value


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for posts in the feed.
    
    Like count and is_liked use the optimized annotations from
    get_feed_posts() to avoid N+1 queries.
    """
    author = UserSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'created_at', 
            'like_count', 'is_liked', 'comment_count'
        ]
        read_only_fields = ['author', 'created_at']
    
    def get_like_count(self, obj):
        """Return pre-annotated like count."""
        if hasattr(obj, '_like_count'):
            return obj._like_count
        return obj.likes.count()
    
    def get_is_liked(self, obj):
        """Check if current user liked this post."""
        if hasattr(obj, 'user_likes'):
            return len(obj.user_likes) > 0
        
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_comment_count(self, obj):
        """Get total comment count for the post."""
        if hasattr(obj, '_comment_count'):
            return obj._comment_count
        return obj.comments.count()


class PostCreateSerializer(serializers.Serializer):
    """Serializer for creating a post."""
    content = serializers.CharField(max_length=5000)


class PostDetailSerializer(PostSerializer):
    """
    Extended post serializer that includes the comment tree.
    Used for single post detail view.
    """
    comments = serializers.SerializerMethodField()
    
    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['comments']
    
    def get_comments(self, obj):
        """
        Return nested comment tree.
        The comment tree is passed via context by the view.
        """
        comment_tree = self.context.get('comment_tree', [])
        return CommentSerializer(
            comment_tree, 
            many=True, 
            context=self.context
        ).data


class LeaderboardEntrySerializer(serializers.Serializer):
    """Serializer for a leaderboard entry."""
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    karma = serializers.IntegerField()
    rank = serializers.IntegerField(required=False)
