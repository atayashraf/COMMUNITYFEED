"""
DRF Views for Community Feed API.

View Responsibilities:
- Handle HTTP requests/responses
- Call service layer for business logic
- Return appropriate status codes

Business logic is delegated to services.py.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .models import Post, Comment
from .serializers import (
    PostSerializer, PostCreateSerializer, PostDetailSerializer,
    CommentSerializer, CommentCreateSerializer,
    LeaderboardEntrySerializer, UserSerializer
)
from . import services


class PostViewSet(viewsets.ViewSet):
    """
    ViewSet for Post operations.
    
    Endpoints:
    - GET /api/posts/ - List all posts (feed)
    - POST /api/posts/ - Create a post
    - GET /api/posts/{id}/ - Get post with comments
    - POST /api/posts/{id}/like/ - Like a post
    - DELETE /api/posts/{id}/like/ - Unlike a post
    - GET /api/posts/{id}/comments/ - Get comments for post
    - POST /api/posts/{id}/comments/ - Create comment on post
    """
    
    def list(self, request):
        """
        GET /api/posts/
        
        Returns feed of posts with:
        - Author info (select_related)
        - Like counts (annotated)
        - User's liked status (prefetched)
        
        Query count: 2-3 (not N+1)
        """
        # Get current user (or anonymous)
        user = request.user if request.user.is_authenticated else None
        
        # Fetch optimized queryset from service
        posts = services.get_feed_posts(user)
        
        # Add comment counts in same query
        posts = posts.annotate(_comment_count=Count('comments'))
        
        serializer = PostSerializer(
            posts, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    def create(self, request):
        """
        POST /api/posts/
        
        Create a new post. Requires authentication (simulated for prototype).
        """
        serializer = PostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # For prototype, get or create a demo user if not authenticated
        user = self._get_or_create_user(request)
        
        post = services.create_post(
            author=user,
            content=serializer.validated_data['content']
        )
        
        return Response(
            PostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, pk=None):
        """
        GET /api/posts/{id}/
        
        Get a single post with its comment tree.
        """
        post = get_object_or_404(Post.objects.select_related('author'), pk=pk)
        
        # Get current user for liked status
        user = request.user if request.user.is_authenticated else None
        
        # Build comment tree (efficiently)
        comment_tree = services.get_comments_for_post(post.id, user)
        
        serializer = PostDetailSerializer(
            post,
            context={
                'request': request,
                'comment_tree': comment_tree
            }
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post', 'delete'])
    def like(self, request, pk=None):
        """
        POST /api/posts/{id}/like/ - Like a post
        DELETE /api/posts/{id}/like/ - Unlike a post
        """
        post = get_object_or_404(Post, pk=pk)
        user = self._get_or_create_user(request)
        
        if request.method == 'POST':
            try:
                services.like_post(user, post)
                return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)
            except services.AlreadyLikedException as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:  # DELETE
            removed = services.unlike_post(user, post)
            if removed:
                return Response({'status': 'unliked'})
            return Response(
                {'error': 'Like not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """
        GET /api/posts/{id}/comments/ - Get comment tree
        POST /api/posts/{id}/comments/ - Create comment
        """
        post = get_object_or_404(Post, pk=pk)
        
        if request.method == 'GET':
            user = request.user if request.user.is_authenticated else None
            comment_tree = services.get_comments_for_post(post.id, user)
            serializer = CommentSerializer(
                comment_tree, 
                many=True,
                context={'request': request}
            )
            return Response(serializer.data)
        
        else:  # POST
            serializer = CommentCreateSerializer(
                data=request.data,
                context={'post_id': post.id}
            )
            serializer.is_valid(raise_exception=True)
            
            user = self._get_or_create_user(request)
            
            # Get parent comment if specified
            parent = None
            parent_id = serializer.validated_data.get('parent_id')
            if parent_id:
                parent = get_object_or_404(Comment, pk=parent_id, post=post)
            
            comment = services.create_comment(
                post=post,
                author=user,
                content=serializer.validated_data['content'],
                parent=parent
            )
            
            return Response(
                CommentSerializer(comment, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
    
    def _get_or_create_user(self, request):
        """
        Helper to get authenticated user or create/get demo user.
        
        For a production app, this would require real authentication.
        For the prototype, we allow passing username in request body
        or use a demo user.
        """
        if request.user.is_authenticated:
            return request.user
        
        # Check for username in request data or headers
        username = request.data.get('username') or request.headers.get('X-Username')
        
        if username:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.com'}
            )
            return user
        
        # Default demo user
        user, _ = User.objects.get_or_create(
            username='demo_user',
            defaults={'email': 'demo@example.com'}
        )
        return user


class CommentDeleteView(APIView):
    """
    Delete a comment.
    
    DELETE /api/comments/{id}/ - Delete comment (only by author)
    """
    
    def delete(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        user = self._get_user(request)
        
        # Only the author can delete their comment
        if comment.author != user:
            return Response(
                {'error': 'You can only delete your own comments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def _get_user(self, request):
        if request.user.is_authenticated:
            return request.user
        
        username = request.data.get('username') or request.headers.get('X-Username')
        if username:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.com'}
            )
            return user
        
        user, _ = User.objects.get_or_create(
            username='demo_user',
            defaults={'email': 'demo@example.com'}
        )
        return user


class CommentLikeView(APIView):
    """
    Like/unlike a comment.
    
    POST /api/comments/{id}/like/ - Like
    DELETE /api/comments/{id}/like/ - Unlike
    """
    
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        user = self._get_user(request)
        
        try:
            services.like_comment(user, comment)
            return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)
        except services.AlreadyLikedException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        user = self._get_user(request)
        
        removed = services.unlike_comment(user, comment)
        if removed:
            return Response({'status': 'unliked'})
        return Response(
            {'error': 'Like not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    def _get_user(self, request):
        if request.user.is_authenticated:
            return request.user
        
        username = request.data.get('username') or request.headers.get('X-Username')
        if username:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@example.com'}
            )
            return user
        
        user, _ = User.objects.get_or_create(
            username='demo_user',
            defaults={'email': 'demo@example.com'}
        )
        return user


class LeaderboardView(APIView):
    """
    GET /api/leaderboard/
    
    Returns top 5 users by karma earned in last 24 hours.
    
    Query parameters:
    - hours: Time window in hours (default 24)
    - limit: Number of users to return (default 5)
    """
    
    def get(self, request):
        hours = int(request.query_params.get('hours', 24))
        limit = int(request.query_params.get('limit', 5))
        
        # Validate bounds
        hours = min(max(hours, 1), 168)  # 1 hour to 1 week
        limit = min(max(limit, 1), 100)
        
        leaderboard = services.get_leaderboard(hours=hours, limit=limit)
        
        # Add rank numbers
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1
        
        serializer = LeaderboardEntrySerializer(leaderboard, many=True)
        return Response(serializer.data)


class UserKarmaView(APIView):
    """
    GET /api/users/{id}/karma/
    
    Get a user's total karma (all time).
    """
    
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        karma = services.get_user_total_karma(user)
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'total_karma': karma
        })


@api_view(['GET'])
def api_root(request):
    """API root - list available endpoints."""
    return Response({
        'posts': '/api/posts/',
        'post_detail': '/api/posts/{id}/',
        'post_like': '/api/posts/{id}/like/',
        'post_comments': '/api/posts/{id}/comments/',
        'comment_like': '/api/comments/{id}/like/',
        'leaderboard': '/api/leaderboard/',
        'user_karma': '/api/users/{id}/karma/',
    })


@api_view(['GET', 'POST'])
def users_view(request):
    """
    GET /api/users/ - List all users
    POST /api/users/ - Create a user
    """
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    else:  # POST
        username = request.data.get('username')
        if not username:
            return Response(
                {'error': 'username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@example.com'}
        )
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
