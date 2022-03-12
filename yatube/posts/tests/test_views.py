import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post, User
from posts.views import POST_LIMIT

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = TEMP_MEDIA_ROOT
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='Тест_автор'
        )
        cls.auth_author_client = Client()
        cls.auth_author_client.force_login(cls.author)
        cls.user_another = User.objects.create_user(
            username='Неавтор'
        )
        cls.authorized_not_author_client = Client()
        cls.authorized_not_author_client.force_login(cls.user_another)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            group=cls.group,
            author=cls.author,
            image=cls.uploaded
        )
        cls.templ_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                args=[cls.group.slug]
            ): 'posts/group_list.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': cls.post.pk}
                    ): 'posts/create_post.html',
            reverse('posts:profile',
                    args=[cls.author.username]
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': cls.post.id}
                    ): 'posts/post_detail.html',
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in PostPagesTest.templ_names.items():
            with self.subTest(template=template):
                response = PostPagesTest.auth_author_client.get(
                    reverse_name
                )
                self.assertTemplateUsed(response, template)

    def test_new_show_correct_context(self):
        """Шаблон posts:post_create сформирован с правильным контекстом."""
        response = PostPagesTest.auth_author_client.get(
            reverse('posts:post_create')
        )
        for value, expected in PostPagesTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_index_page_list_is_1(self):
        """На страницу posts:index передается ожидаемое количество объектов."""
        response = PostPagesTest.auth_author_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get(
            'page_obj'
        ).object_list), 1)

    def test_group_page_list_is_1(self):
        """На страницу posts:group_list
        передается ожидаемое количество объектов.
        """
        response = PostPagesTest.auth_author_client.get(
            reverse('posts:group_list', args=[PostPagesTest.group.slug])
        )
        correct_post = response.context.get(
            'page_obj'
        ).object_list[0]
        self.assertEqual(len(response.context.get('page_obj').object_list), 1)
        self.assertEqual(correct_post, PostPagesTest.post)

    def test_index_show_correct_context(self):
        """Шаблон posts:index сформирован с правильным контекстом."""
        response = PostPagesTest.guest_client.get(reverse('posts:index'))
        post = PostPagesTest.post
        response_post = response.context.get('page_obj').object_list[0]
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, PostPagesTest.author)
        self.assertEqual(post_group, PostPagesTest.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)

    def test_index_show_correct_profile(self):
        """Шаблон posts:profile сформирован с правильным контекстом."""
        response = PostPagesTest.guest_client.get(
            reverse('posts:profile', args=[PostPagesTest.author.username])
        )
        post = PostPagesTest.post
        author = PostPagesTest.author
        response_author = response.context.get('author')
        response_count = response.context.get('count')
        response_post = response.context.get('page_obj').object_list[0]
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, author)
        self.assertEqual(post_group, PostPagesTest.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)
        self.assertEqual(author, response_author)
        self.assertEqual(1, response_count)

    def test_index_show_correct_post_view(self):
        """Шаблон posts:post_detail сформирован с правильным контекстом."""
        response = PostPagesTest.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTest.post.pk}
            )
        )
        post = PostPagesTest.post
        author = PostPagesTest.author
        response_post = response.context.get('post')
        response_author = response.context.get('author')
        response_count = response.context.get('count')
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, author)
        self.assertEqual(post_group, PostPagesTest.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)
        self.assertEqual(post, response_post)
        self.assertEqual(author, response_author)
        self.assertEqual(1, response_count)

    def test_post_edit_show_correct_context(self):
        """Шаблон posts:post_edit сформирован с правильным контекстом."""
        response = PostPagesTest.auth_author_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTest.post.pk}
                    )
        )
        for value, expected in PostPagesTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_slug_show_correct_context(self):
        """Шаблон posts:group_list сформирован с правильным контекстом."""
        response = PostPagesTest.auth_author_client.get(
            reverse('posts:group_list', args=[PostPagesTest.group.slug])
        )
        post = PostPagesTest.post
        response_post = response.context.get('page_obj').object_list[0]
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, PostPagesTest.author)
        self.assertEqual(post_group, PostPagesTest.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)

    def test_follow_user_another(self):
        """Follow на другого пользователя работает корректно"""
        PostPagesTest.authorized_not_author_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTest.author.username}))
        follow_exist = Follow.objects.filter(
            user=PostPagesTest.user_another,
            author=PostPagesTest.author).exists()
        self.assertTrue(follow_exist)

    def test_unfollow_user_another(self):
        """Unfollow от другого пользователя работает корректно"""
        PostPagesTest.authorized_not_author_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTest.author.username}))
        PostPagesTest.authorized_not_author_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostPagesTest.author.username}))
        follow_exist = Follow.objects.filter(
            user=PostPagesTest.user_another,
            author=PostPagesTest.author).exists()
        self.assertFalse(follow_exist)

    def test_new_post_follow_index_show_correct_context(self):
        """Новая запись автора появляется в ленте подписчиков
         и не появляется в ленте тех, кто не подписан
        """
        PostPagesTest.authorized_not_author_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTest.author.username}))
        follow_exist = Follow.objects.filter(
            user=PostPagesTest.user_another,
            author=PostPagesTest.author).exists()
        self.assertTrue(follow_exist)
        response = PostPagesTest.authorized_not_author_client.get(
            reverse(('posts:follow_index'))
        )
        count0 = len(response.context.get('page_obj'))
        first_object = response.context.get('page_obj').object_list[0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group.slug
        self.assertEqual(post_author_0, PostPagesTest.post.author)
        self.assertEqual(post_text_0, PostPagesTest.post.text)
        self.assertEqual(post_group_0, PostPagesTest.group.slug)

        PostPagesTest.authorized_not_author_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostPagesTest.author.username}))
        follow_exist = Follow.objects.filter(
            user=PostPagesTest.user_another,
            author=PostPagesTest.author).exists()
        self.assertFalse(follow_exist)
        response = PostPagesTest.authorized_not_author_client.get(
            reverse(('posts:follow_index'))
        )
        count1 = len(response.context.get('page_obj'))
        self.assertEqual(count0 - 1, count1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = TEMP_MEDIA_ROOT
        cls.author = User.objects.create_user(username='Тест_автор')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание'
        )
        for i in range(31):
            cls.post = Post.objects.create(
                text=f'Тестовый текст поста{i}',
                group=cls.group,
                author=cls.author
            )

        cls.templates = {
            1: reverse('posts:index'),
            2: reverse('posts:group_list', args=[cls.group.slug]),
            3: reverse('posts:profile', args=[cls.author.username])
        }

    def test_first_page_contains_ten_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на первую страницую."""
        for i in PaginatorViewsTest.templates.keys():
            with self.subTest(i=i):
                response = self.client.get(self.templates[i])
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), POST_LIMIT)

    def test_second_page_contains_ten_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на вторую страницую."""
        for i in PaginatorViewsTest.templates.keys():
            with self.subTest(i=i):
                response = self.client.get(self.templates[i] + '?page=2')
                self.assertEqual(len(response.context.get(
                    'page_obj'
                ).object_list), POST_LIMIT)


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = TEMP_MEDIA_ROOT
        cls.author = User.objects.create_user(username='Тест_автор')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            group=cls.group,
            author=cls.author,
        )

    def test_cache_index(self):
        """Проверка хранения и обновления кэша для /."""
        response = CacheViewsTest.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Тестовый текст нового поста',
            author=CacheViewsTest.author,
        )
        response_old = CacheViewsTest.authorized_client.get(
            reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts,
                         'Не возвращается кэшированная страница.')
        cache.clear()
        response_new = CacheViewsTest.authorized_client.get(
            reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Не сбрасывается кэш.')
