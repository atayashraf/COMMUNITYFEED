"""
Django admin configuration for Community Feed models.
"""
from django.contrib import admin
from .models import Post, Comment, PostLike, CommentLike, KarmaEvent


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'content_preview', 'created_at', 'like_count']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    def like_count(self, obj):
        return obj.likes.count()


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'post', 'parent', 'depth', 'content_preview', 'created_at']
    list_filter = ['created_at', 'depth']
    search_fields = ['content', 'author__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'created_at']
    list_filter = ['created_at']


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'comment', 'created_at']
    list_filter = ['created_at']


@admin.register(KarmaEvent)
class KarmaEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'event_type', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__username']
