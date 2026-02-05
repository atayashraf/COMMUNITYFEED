"""
Seed script to populate the database with sample data for testing.

Run with: python manage.py shell < seed_data.py
Or: python manage.py runscript seed_data (if django-extensions is installed)
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from feed.models import Post, Comment, PostLike, CommentLike, KarmaEvent
from feed import services

def seed_database():
    print("Seeding database...")
    
    # Create users
    users = []
    usernames = ['alice', 'bob', 'charlie', 'diana', 'eve', 'frank']
    for username in usernames:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@example.com'}
        )
        users.append(user)
        if created:
            print(f"  Created user: {username}")
        else:
            print(f"  User exists: {username}")
    
    alice, bob, charlie, diana, eve, frank = users
    
    # Create posts
    posts_data = [
        (alice, "Welcome to Playto Community! 🎉 This is our first post. Let's build something amazing together."),
        (bob, "Just finished learning Django REST Framework. The serializers are powerful but can be tricky with nested relationships."),
        (charlie, "Has anyone tried the new recursive CTE feature in PostgreSQL? It's great for hierarchical data like comments."),
        (diana, "Pro tip: Always use select_related() and prefetch_related() to avoid N+1 queries. Your database will thank you! 🚀"),
        (eve, "Working on a gamification system with karma points. The tricky part is calculating leaderboards efficiently."),
    ]
    
    posts = []
    for author, content in posts_data:
        post, created = Post.objects.get_or_create(
            author=author,
            content=content
        )
        posts.append(post)
        if created:
            print(f"  Created post by {author.username}")
    
    # Create comments
    post1, post2, post3, post4, post5 = posts
    
    # Comments on post 1
    c1 = Comment.objects.get_or_create(
        post=post1, author=bob, content="Welcome! Excited to be part of this community.",
        parent=None
    )[0]
    
    c1a = Comment.objects.get_or_create(
        post=post1, author=charlie, content="Me too! The tech stack looks solid.",
        parent=c1
    )[0]
    
    c1a1 = Comment.objects.get_or_create(
        post=post1, author=alice, content="Thanks everyone! Django + React is a great combo.",
        parent=c1a
    )[0]
    
    c2 = Comment.objects.get_or_create(
        post=post1, author=diana, content="The UI looks clean. Love the Tailwind styling!",
        parent=None
    )[0]
    
    # Comments on post 4 (about N+1)
    c3 = Comment.objects.get_or_create(
        post=post4, author=eve, content="This is so important! I once had a page making 500 queries.",
        parent=None
    )[0]
    
    c3a = Comment.objects.get_or_create(
        post=post4, author=frank, content="500?! 😱 How did you debug that?",
        parent=c3
    )[0]
    
    c3a1 = Comment.objects.get_or_create(
        post=post4, author=eve, content="Django Debug Toolbar saved me. Highly recommend it!",
        parent=c3a
    )[0]
    
    c3a2 = Comment.objects.get_or_create(
        post=post4, author=bob, content="silk is another good option for profiling.",
        parent=c3a
    )[0]
    
    print("  Created comments")
    
    # Create likes (and karma events via service)
    likes = [
        # Likes on posts
        (bob, post1), (charlie, post1), (diana, post1), (eve, post1),  # 4 likes on welcome post
        (alice, post4), (charlie, post4), (eve, post4),  # 3 likes on N+1 post
        (alice, post2), (diana, post2),  # 2 likes on DRF post
        (bob, post5),  # 1 like on gamification post
    ]
    
    for user, post in likes:
        try:
            services.like_post(user, post)
            print(f"  {user.username} liked post by {post.author.username}")
        except services.AlreadyLikedException:
            print(f"  {user.username} already liked post by {post.author.username}")
    
    # Like some comments
    comment_likes = [
        (alice, c3),  # Like Eve's N+1 comment
        (bob, c3),
        (diana, c1a1),  # Like Alice's reply
    ]
    
    for user, comment in comment_likes:
        try:
            services.like_comment(user, comment)
            print(f"  {user.username} liked comment by {comment.author.username}")
        except services.AlreadyLikedException:
            print(f"  {user.username} already liked comment")
    
    print("\n✅ Database seeded successfully!")
    print("\nSummary:")
    print(f"  Users: {User.objects.count()}")
    print(f"  Posts: {Post.objects.count()}")
    print(f"  Comments: {Comment.objects.count()}")
    print(f"  Post Likes: {PostLike.objects.count()}")
    print(f"  Comment Likes: {CommentLike.objects.count()}")
    print(f"  Karma Events: {KarmaEvent.objects.count()}")


if __name__ == '__main__':
    seed_database()
