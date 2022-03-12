from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='Автор'
        )
        cls.authorized_author_client = Client()
        cls.authorized_author_client.force_login(cls.author)
        cls.user_another = User.objects.create_user(
            username='Неавтор'
        )
        cls.authorized_not_author_client = Client()
        cls.authorized_not_author_client.force_login(cls.user_another)
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            group=cls.group,
            author=cls.author
        )
        cls.post_edit_url = f'/posts/{cls.post.id}/edit/'
        cls.public_urls = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.author.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        cls.private_urls = {
            '/create/': 'posts/create_post.html',
            cls.post_edit_url: 'posts/create_post.html',
        }
        cls.templates_url_names = cls.public_urls.copy()
        cls.templates_url_names.update(cls.private_urls)
        cls.form_comment_data = {
            'text': 'Новый комментарий',
        }

    def test_pages_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        for url, code in StaticURLTests.public_urls.items():
            with self.subTest(url=url, code=code):
                response = StaticURLTests.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_post_create_exists_at_desired_location_authorized(self):
        """Страница /create/ доступна авторизованому пользователю."""
        response = StaticURLTests.authorized_not_author_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страницы /create/ и /posts/<int:post_id>/edit/ доступны автору."""
        for url, code in StaticURLTests.private_urls.items():
            with self.subTest(url=url, code=code):
                response = StaticURLTests.authorized_author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_post_create_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = StaticURLTests.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_redirect_client_on_post_page(self):
        """Страница /posts/<int:post_id>/edit/ перенаправит неавтора поста
        на страницу поста.
        """
        response = StaticURLTests.authorized_not_author_client.get(
            f'/posts/{StaticURLTests.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/posts/{StaticURLTests.post.pk}/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in StaticURLTests.templates_url_names.items():
            with self.subTest(url=url):
                response = StaticURLTests.authorized_author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_commenting_is_available_only_authorized_user(self):
        """Комментирование доступно только авторизованному пользователю."""
        response_authorized = StaticURLTests.authorized_not_author_client.get(
            reverse('posts:add_comment', kwargs={
                'post_id': StaticURLTests.post.pk}
            ),
            data=StaticURLTests.form_comment_data,
            follow=True
        )
        self.assertEqual(response_authorized.status_code, HTTPStatus.OK.value)

    def test_сommenting_is_not_available_to_an_anonymous_user(self):
        """Комментирование недоступно анонимному пользователю."""
        response_not_authorized = StaticURLTests.guest_client.get(
            reverse('posts:add_comment', kwargs={
                'post_id': StaticURLTests.post.pk}
            ),
            data=StaticURLTests.form_comment_data
        )
        self.assertEqual(
            response_not_authorized.status_code,
            HTTPStatus.FOUND.value
        )

    def test_post_create_redirect_anonymous_on_login(self):
        """Страница 'posts/<int:post_id>/comment/' перенаправит
        анонимного пользователя на страницу логина.
        """
        response = StaticURLTests.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': StaticURLTests.post.pk}
            ),
            data=StaticURLTests.form_comment_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{StaticURLTests.post.pk}/comment/'
        )

    def test_response_status_code_404(self):
        """При запросе несуществующей страницы сервер возвращает код 404."""
        response = StaticURLTests.guest_client.get('/posts/тест}')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
