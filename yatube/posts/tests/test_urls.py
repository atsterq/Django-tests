from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="test_user")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text="Тестовый пост",
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_index_group_profile_post_id_urls_unauthorized(self):
        """Доступность страниц неавторизованному пользователю."""
        urls: tuple = (
            "/",
            f"/group/{self.group.slug}/",
            f"/profile/{self.user.get_username()}/",
            f"/posts/{self.post.pk}/",
        )
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_index_group_profile_post_id_urls_authorized(self):
        """Доступность страниц авторизованному пользователю."""
        urls: tuple = (
            f"/posts/{self.post.pk}/edit/",
            "/create/",
        )
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_unauthorized_on_login(self):
        """Страницы перенаправят анонимного пользователя на страницу логина."""
        urls: tuple = (
            f"/posts/{self.post.pk}/edit/",
            "/create/",
        )
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f"/auth/login/?next={url}")

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "/": "posts/index.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/profile/{self.user.get_username()}/": "posts/profile.html",
            f"/posts/{self.post.pk}/": "posts/post_detail.html",
            "/create/": "posts/create_post.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
