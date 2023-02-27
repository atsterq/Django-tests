from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Post
from posts.paginator import paginator


def index(request):
    post_list = Post.objects.all()
    context = {
        "page_obj": paginator(request, post_list),
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        "group": group,
        "page_obj": paginator(request, post_list),
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    following = user.following.exists()
    context = {
        "author": user,
        "page_obj": paginator(request, post_list),
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        "post": post,
        "form": form,
        "comments": comments,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {"form": form}
    if not request.method == "POST":
        return render(request, "posts/create_post.html", context)
    if not form.is_valid():
        return render(request, "posts/create_post.html", context)
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("posts:profile", post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect("posts:post_detail", post.pk)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if not form.is_valid():
        template = "posts/create_post.html"
        context = {
            "form": form,
            "is_edit": True,
            "post": post,
        }
        return render(request, template, context)
    form.save()
    return redirect("posts:post_detail", post.pk)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    follower = Follow.objects.filter(user=request.user).values_list(
        "author_id", flat=True
    )
    posts_list = Post.objects.filter(author_id__in=follower)
    context = {
        "page_obj": paginator(request, posts_list),
        "title": "Избранные посты",
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:follow_index")


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect("posts:follow_index")
