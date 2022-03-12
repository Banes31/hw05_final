import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_create_form(self):
        """Валидная форма создает новый пост."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост 2',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        self.assertTrue(Post.objects.filter(
            text='Новый пост 2',
            group__slug='test-slug',
            image='posts/small.gif').exists()
        )

    def test_edit_form(self):
        """Изменение поста."""
        test_post = Post.objects.create(
            text='Новый пост 3',
            author=self.user,
        )
        form_data_edit = {
            'text': 'Редактированный пост',
            'group': self.group.pk,
        }
        posts_count = Post.objects.count()
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': test_post.pk}),
            data=form_data_edit)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': test_post.pk}))
        self.assertTrue(Post.objects.filter(
            text='Редактированный пост',
            group__slug='test-slug').exists())

    def test_comment(self):
        """Комментарий появляется на странице поста."""
        comment_count = Comment.objects.count()
        post_id = self.post.pk
        form_comment_data = {
            'text': 'Новый комментарий',
        }
        response = self.author_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_comment_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(text='Новый комментарий').exists()
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': post_id}))
