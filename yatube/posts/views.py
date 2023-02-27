from django.shortcuts import render, get_object_or_404, redirect
from posts.models import Post, Group
from django.contrib.auth.models import User
from posts.forms import PostForm
from posts.paginator import paginator
from django.contrib.auth.decorators import login_required


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
    context = {
        "author": user,
        "page_obj": paginator(request, post_list),
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    context = {
        "post": post,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
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
    form = PostForm(request.POST or None, instance=post)
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
