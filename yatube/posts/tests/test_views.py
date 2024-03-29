import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="test_user")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text="Тестовый пост",
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text="Тестовый комментарий",
        )
        cls.second_user = User.objects.create(username="second_user")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def post_info_assert(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): "posts/profile.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.pk}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.pk}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse("posts:index"))
        self.post_info_assert(response.context["page_obj"][0])

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        self.assertEqual(response.context["group"].title, self.group.title)
        self.assertEqual(response.context["group"].slug, self.group.slug)
        self.assertEqual(
            response.context["group"].description, self.group.description
        )
        self.post_info_assert(response.context["page_obj"][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username})
        )
        self.assertEqual(
            response.context["author"].username, self.user.username
        )
        self.post_info_assert(response.context["page_obj"][0])

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk})
        )
        self.post_info_assert(response.context["post"])

    def test_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон редактирования edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.pk})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Пост создается на страницах с выбранной группой."""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_new_post_show_in_group_context(self):
        """Пост с группой не появляется в новой группе."""
        new_group = Group.objects.create(
            title="Тестовая группа 2", slug="test_slug2"
        )
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": new_group.slug})
        )
        context = response.context["page_obj"].object_list
        self.assertNotIn(self.post, context)

    def test_comments(self):
        """Тестирование комментария."""
        form_data = {
            "post": self.post,
            "author": self.user,
            "text": "Комментарий для теста комментариев",
        }
        self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertTrue(
            Comment.objects.filter(
                text="Комментарий для теста комментариев",
                author=self.user,
            ).exists()
        )

    def test_check_cache(self):
        """Тестирование кеша."""
        response = self.guest_client.get(reverse("posts:index")).content
        Post.objects.get(id=1).delete()
        response2 = self.guest_client.get(reverse("posts:index")).content
        self.assertEqual(response, response2)
        cache.clear()
        cleared_cache_response = self.guest_client.get(
            reverse("posts:index")
        ).content
        self.assertNotEqual(response, cleared_cache_response)

    def test_follow_action(self):
        """Тестирование подписки."""
        self.authorized_client.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.second_user.username},
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user, author=self.second_user
            ).exists()
        )

    def test_unfollow_action(self):
        """Тестирование отписки."""
        Follow.objects.create(user=self.user, author=self.second_user)
        self.authorized_client.get(
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": self.second_user.username},
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user, author=self.second_user
            ).exists()
        )

    def test_follow_page_for_follower(self):
        """Тестирование ленты подписанного пользователя."""
        new_post = Post.objects.create(
            author=self.second_user,
            text="Тестирование ленты",
        )
        Follow.objects.create(user=self.user, author=self.second_user)
        response = self.authorized_client.get(
            reverse("posts:follow_index")
        ).context["page_obj"]
        self.assertIn(new_post, response)

    def test_follow_page_for_non_follower(self):
        """Тестирование ленты неподписанного пользователя."""
        new_user = User.objects.create(username="new_user")
        new_post = Post.objects.create(
            author=self.second_user,
            text="Тестирование ленты",
        )
        Follow.objects.create(user=new_user, author=self.second_user)
        response = self.authorized_client.get(
            reverse("posts:follow_index")
        ).context["page_obj"]
        self.assertNotIn(new_post, response)


class PaginatorViewsTest(TestCase):
    """Пажинатор работает правильно."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username="test_user")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
        )
        posts = (
            Post(text=f"{cls.post.text}{i}", group=cls.group, author=cls.user)
            for i in range(12)
        )
        Post.objects.bulk_create(posts)[:10]
        cls.template_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:profile", kwargs={"username": cls.user.username}
            ): "posts/profile.html",
            reverse(
                "posts:group_list", kwargs={"slug": cls.group.slug}
            ): "posts/group_list.html",
        }

    def test_first_page_contains_ten_records(self):
        for reverse_name in self.template_pages_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(len(response.context["page_obj"]), 10)

    def test_second_page_contains_three_records(self):
        for reverse_name in self.template_pages_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get((reverse_name) + "?page=2")
                self.assertEqual(len(response.context["page_obj"]), 3)
