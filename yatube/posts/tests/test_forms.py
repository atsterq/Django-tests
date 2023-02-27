import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="auth")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

    def test_create_post(self):
        """Тестирование создания поста."""
        posts_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "group": self.group.id,
            "text": "Текст записанный в форму",
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.user.username}),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text="Текст записанный в форму",
                group=self.group.id,
                author=self.user,
            ).exists()
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post(self):
        """Тестирование редактирования поста."""
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="2small.gif", content=small_gif, content_type="image/gif"
        )
        self.post = Post.objects.create(
            text="Тестовый текст", author=self.user, group=self.group
        )
        old_text = self.post
        self.group2 = Group.objects.create(
            title="Тестовая группа2", slug="test-group", description="Описание"
        )
        form_data = {
            "text": "Текст записанный в форму",
            "group": self.group2.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": old_text.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        error_name1 = "Данные поста не совпадают"
        self.assertTrue(
            Post.objects.filter(
                group=self.group2.id,
                author=self.user,
                pub_date=self.post.pub_date,
            ).exists(),
            error_name1,
        )
        self.assertNotEqual(old_text.text, form_data["text"])
        self.assertNotEqual(old_text.group, form_data["group"])
        self.assertTrue(Post.objects.filter(image="posts/2small.gif").exists())

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
        self.assertRedirects(
            response, f"/auth/login/?next=/posts/{self.post.id}/edit/"
        )

    def test_edit_post_forbidden_for_no_auth_user(self):
        """Проверка запрета редактирования не авторизованного пользователя."""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Текст записанный в форму",
            "group": self.group.id,
        }
        response = self.guest_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Post.objects.count(), posts_count + 1)
