from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class PostFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="auth")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title="Тестовая группа", slug="test-slug",
            description="Тестовое описание"
        )

    def test_create_post(self):
        """Тестирование создания поста."""
        posts_count = Post.objects.count()
        form_data = {
            "group": self.group.id,
            "text": "Текст записанный в форму",
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text="Текст записанный в форму",
                group=self.group.id, author=self.user
            ).exists()
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post(self):
        """Тестирование редактирования поста."""
        self.post = Post.objects.create(
            text="Тестовый текст", author=self.user, group=self.group
        )
        old_text = self.post
        self.group2 = Group.objects.create(
            title="Тестовая группа2", slug="test-group", description="Описание"
        )
        form_data = {"text": "Текст записанный в форму",
                     "group": self.group2.id}
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": old_text.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        error_name1 = "Данные поста не совпадают"
        self.assertTrue(
            Post.objects.filter(
                group=self.group2.id, author=self.user,
                pub_date=self.post.pub_date
            ).exists(),
            error_name1,
        )
        self.assertNotEqual(old_text.text, form_data["text"])
        self.assertNotEqual(old_text.group, form_data["group"])

    def test_group_null(self):
        """Проверка что группу можно не указывать."""
        self.post = Post.objects.create(
            text="Тестовый текст", author=self.user, group=self.group
        )
        old_text = self.post
        form_data = {"text": "Текст записанный в форму", "group": ""}
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": old_text.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(old_text.group, form_data["group"])

    def test_reddirect_guest_client(self):
        """Проверка редиректа неавторизованного пользователя."""
        self.post = Post.objects.create(
            text="Тестовый текст", author=self.user, group=self.group
        )
        form_data = {"text": "Текст записанный в форму"}
        response = self.guest_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             f"/auth/login/?next=/posts/{self.post.id}/edit/")

    def test_edit_post_forbidden_for_no_auth_user(self):
        """Проверка запрета редактирования не авторизованного пользователя."""
        posts_count = Post.objects.count()
        form_data = {"text": "Текст записанный в форму",
                     "group": self.group.id}
        response = self.guest_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Post.objects.count(), posts_count + 1)
