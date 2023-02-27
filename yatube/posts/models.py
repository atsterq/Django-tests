from core.models import CreatedModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    text = models.TextField("Текст поста", help_text="Текст нового поста")
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
    )
    image = models.ImageField("Картинка", upload_to="posts/", blank=True)

    def __str__(self) -> str:
        return self.text[:15]

    class Meta:
        ordering = ["-pub_date"]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="comments",
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField(
        "Текст комментария", help_text="Текст нового комментария"
    )

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.text
