# Technical Explainer

This document explains the key technical decisions and implementations in the Playto Community Feed application.

## Table of Contents

1. [Comment Tree: Modeling & N+1 Prevention](#1-comment-tree-modeling--n1-prevention)
2. [Leaderboard Query](#2-leaderboard-query)
3. [Failure Modes Considered](#3-failure-modes-considered)
4. [AI Audit: Bug Fixes](#4-ai-audit-bug-fixes)

---

## 1. Comment Tree: Modeling & N+1 Prevention

### How Nested Comments are Modeled

We use an **Adjacency List** model with a self-referential foreign key:

```python
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=2000)
    depth = models.PositiveIntegerField(default=0)  # Computed on save
```

### Why Not MPTT (Nested Sets)?

I deliberately avoided django-mptt despite its popularity for tree structures:

1. **Write Performance**: MPTT requires recalculating `lft`/`rght` values for all siblings on every insert. In a discussion forum where comments are created frequently, this is unacceptable.
2. **Complexity**: MPTT adds magic fields and signals that make debugging harder.
3. **Fragility**: Tree corruption from failed transactions is notoriously difficult to recover from.

**My approach**: Adjacency list with a single bulk fetch and O(n) in-memory tree construction. This trades a tiny bit of read complexity for dramatically simpler writes.

**Why Adjacency List over Materialized Path or Nested Sets?**

| Approach | Pros | Cons |
|----------|------|------|
| **Adjacency List** (chosen) | Simple, fast inserts, easy to understand | Naive recursive fetching causes N+1 |
| Materialized Path | Fast subtree queries | Path string maintenance, complex |
| Nested Sets (MPTT) | Fast reads | Very slow writes, fragile |

We chose Adjacency List because:
1. Writes (new comments) are frequent and need to be fast
2. N+1 can be prevented with bulk fetching + Python tree building
3. Simpler to reason about and debug

### How Serialization Avoids N+1 Queries

**The Problem:**
Naive recursive fetching would execute a query for each comment's children:

```python
# BAD: N+1 queries!
def get_children(comment):
    children = Comment.objects.filter(parent=comment)  # Query per comment!
    return [{'comment': c, 'children': get_children(c)} for c in children]
```

**Our Solution:**
Fetch ALL comments for a post in ONE query, then build the tree in Python:

```python
# In services.py - get_comments_for_post()

# Step 1: ONE query to get all comments with annotations
queryset = Comment.objects.filter(post_id=post_id).select_related(
    'author', 'parent'
).annotate(
    _like_count=Count('likes')
)

comments = list(queryset)

# Step 2: Build tree in Python (O(n) algorithm)
def _build_comment_tree(comments):
    # Create lookup map: O(n)
    comment_map = {}
    for comment in comments:
        comment.children = []
        comment_map[comment.id] = comment
    
    # Build relationships: O(n)
    top_level = []
    for comment in comments:
        if comment.parent_id is None:
            top_level.append(comment)
        else:
            parent = comment_map.get(comment.parent_id)
            if parent:
                parent.children.append(comment)
    
    return top_level
```

**Query Count:**
- 1 query: Fetch all comments with `select_related` for author
- 1 query (via annotation): Get like counts
- 1 query (optional): Prefetch user's likes for "is_liked" status

**Total: 2-3 queries regardless of comment count or nesting depth.**

---

## 2. Leaderboard Query

### The Exact Django QuerySet

```python
# In services.py - get_leaderboard()

def get_leaderboard(hours: int = 24, limit: int = 5) -> list:
    cutoff = timezone.now() - timedelta(hours=hours)
    
    leaderboard = (
        KarmaEvent.objects
        .filter(created_at__gte=cutoff)           # 1. Filter last 24h
        .values('user_id', 'user__username')       # 2. GROUP BY user
        .annotate(total_karma=Sum('amount'))       # 3. SUM karma
        .order_by('-total_karma')[:limit]          # 4. ORDER BY + LIMIT
    )
    
    return [
        {
            'user_id': entry['user_id'],
            'username': entry['user__username'],
            'karma': entry['total_karma']
        }
        for entry in leaderboard
    ]
```

### Generated SQL (Equivalent)

```sql
SELECT 
    feed_karmaevent.user_id,
    auth_user.username,
    SUM(feed_karmaevent.amount) AS total_karma
FROM feed_karmaevent
INNER JOIN auth_user ON feed_karmaevent.user_id = auth_user.id
WHERE feed_karmaevent.created_at >= NOW() - INTERVAL '24 hours'
GROUP BY feed_karmaevent.user_id, auth_user.username
ORDER BY total_karma DESC
LIMIT 5;
```

### How Last-24h Filtering Works

1. **`timezone.now()`** - Gets current time (timezone-aware in Django)
2. **`timedelta(hours=hours)`** - Creates a 24-hour duration
3. **Subtraction** - Calculates the cutoff timestamp
4. **`filter(created_at__gte=cutoff)`** - Only includes karma events after cutoff

**Why not store a cached `daily_karma` field?**

- **Consistency**: Cache invalidation is hard. When does "daily" reset?
- **Accuracy**: The leaderboard should be a rolling 24-hour window, not calendar-day
- **Auditability**: Historical KarmaEvent records allow reconstruction
- **Simplicity**: One source of truth, no sync issues

**Performance Considerations:**

The query is efficient because:
1. Index on `(created_at, user_id)` makes filtering fast
2. Aggregation happens in the database, not Python
3. Only returns 5 rows, regardless of total karma events

---

## 3. Failure Modes Considered

Before building, I identified potential failure modes and designed solutions:

| Failure Mode | Risk | Solution |
|--------------|------|----------|
| **Concurrent likes (race condition)** | User gets 2 likes, author gets double karma | DB `UniqueConstraint` catches duplicates atomically |
| **Karma duplication** | Like created but karma fails, or vice versa | `@transaction.atomic` ensures both or neither |
| **Deep comment trees causing N+1** | 50 nested comments = 50 queries | Single bulk fetch + Python tree building |
| **Leaderboard showing stale data** | Cached `daily_karma` field drifts from reality | Dynamic aggregation from `KarmaEvent` table |
| **Self-liking for karma farming** | Users boost own content | Backend check: `if post.author_id != user.id` |
| **24h window ambiguity** | "Daily" could mean calendar day vs rolling | Rolling 24h window from `timezone.now()` |

### Concurrency Deep Dive

The like operation is protected at multiple levels:

```python
@transaction.atomic  # Level 1: Transaction isolation
def like_post(user, post):
    try:
        PostLike.objects.create(user=user, post=post)  # Level 2: DB unique constraint
        KarmaEvent.objects.create(...)  # Only runs if create succeeded
    except IntegrityError:  # Level 3: Graceful error handling
        raise AlreadyLikedException()
```

---

## 4. AI Audit: Bug Fixes

> The prompt explicitly warned: *"AI frequently gets aggregation and recursion wrong — verify everything."*
> 
> Here are concrete examples where AI-generated code was incorrect and how I fixed it.

### Bug #1: Storing Daily Karma as a Cached Field

**AI's Initial Suggestion:**

```python
class User(AbstractUser):
    daily_karma = models.IntegerField(default=0)  # BAD: Cached field
    
def like_post(user, post):
    post.author.daily_karma += 5
    post.author.save()
```

**Why This Was Wrong:**

1. **Violated the requirement**: The prompt explicitly said *"DO NOT store daily_karma or similar fields"*
2. **Reset timing ambiguity**: When does "daily" reset? Midnight UTC? User's timezone?
3. **Rolling window impossible**: A cached field can't represent a sliding 24-hour window
4. **No audit trail**: If karma is wrong, how do you debug it?

**My Fix:**

```python
class KarmaEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()  # +5 or +1
    created_at = models.DateTimeField(auto_now_add=True)
    
# Leaderboard calculated dynamically
KarmaEvent.objects.filter(created_at__gte=cutoff).values('user').annotate(Sum('amount'))
```

---

### Bug #2: Incorrect Aggregation Query

**Initial AI-Generated Code (Buggy):**

```python
# BUGGY VERSION
def get_leaderboard(hours=24, limit=5):
    cutoff = timezone.now() - timedelta(hours=hours)
    
    return (
        User.objects
        .annotate(
            total_karma=Sum(
                'karma_events__amount',
                filter=Q(karma_events__created_at__gte=cutoff)
            )
        )
        .order_by('-total_karma')[:limit]
    )
```

**Why This Was Wrong:**

1. **Includes users with no karma**: The query returns ALL users, including those with `total_karma=None` (no karma events). This clutters the leaderboard.

2. **Inefficient**: Scans all users even if they have no recent karma. With 10,000 users but only 50 active in 24h, this is wasteful.

3. **NULL handling**: Users without karma get `None` instead of 0, causing sorting issues.

**The Fix:**

Query from `KarmaEvent` instead of `User`:

```python
# FIXED VERSION
def get_leaderboard(hours=24, limit=5):
    cutoff = timezone.now() - timedelta(hours=hours)
    
    return (
        KarmaEvent.objects
        .filter(created_at__gte=cutoff)        # Pre-filter to relevant rows
        .values('user_id', 'user__username')   # Group by user
        .annotate(total_karma=Sum('amount'))   # Sum only filtered rows
        .order_by('-total_karma')[:limit]      # Top 5
    )
```

**Why This Is Correct:**

1. **Only includes active users**: Pre-filtering means only users with recent karma appear
2. **Efficient**: Only scans `KarmaEvent` rows in the time window
3. **No NULL issues**: Every row in the result has karma (they wouldn't be there otherwise)
4. **Single query with JOIN**: Gets username in the same query via `user__username`

---

### Bug #3: Race Condition in Likes

**Initial AI-Generated Code (Buggy):**

```python
# BUGGY VERSION
def like_post(user, post):
    # Check if already liked
    if PostLike.objects.filter(user=user, post=post).exists():
        raise AlreadyLikedException("Already liked")
    
    # Create the like
    like = PostLike.objects.create(user=user, post=post)
    
    # Create karma
    KarmaEvent.objects.create(user=post.author, amount=5, ...)
    
    return like
```

**Why This Was Wrong:**

**Race Condition**: Two simultaneous requests can both pass the `exists()` check before either creates the like:

```
Request 1: exists() -> False ─────┐
Request 2: exists() -> False ─────┤ (both pass check)
Request 1: create() -> Success    │
Request 2: create() -> DUPLICATE! ┘ (no constraint = both succeed)
```

Result: User has 2 likes, author gets 10 karma instead of 5.

**My Fix - Rely on database constraint:**

```python
# FIXED VERSION
@transaction.atomic
def like_post(user, post):
    try:
        like = PostLike.objects.create(user=user, post=post)  # Fails if duplicate
        if post.author_id != user.id:
            KarmaEvent.objects.create(user=post.author, amount=5, ...)
        return like
    except IntegrityError:
        raise AlreadyLikedException("Already liked")
```

**Model constraint that makes this work:**

```python
class PostLike(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_post_like')
        ]
```

---

## Summary of Key Design Decisions

| Challenge | Solution | Why |
|-----------|----------|-----|
| N+1 queries for comments | Bulk fetch + Python tree building | 2-3 queries for any depth |
| Leaderboard efficiency | Query from KarmaEvent with filter | Only scans relevant rows |
| Double-like prevention | DB unique constraint + transaction | Race-condition proof |
| Karma tracking | Immutable event records | Auditable, no cache invalidation |
| Comment nesting | Adjacency list with depth field | Simple, fast writes |
| Tree structure choice | Adjacency list over MPTT | Fast writes, simpler debugging |
