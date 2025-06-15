views.py
from django.db.models import Count
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import Http404
from django.utils import timezone
from .models import Post, Category, Comment
from .forms import RegisterForm, PostForm, CommentForm
POSTS_LIMIT = 10

# def get_published_posts(queryset=None):
#     if queryset is None:
#         queryset = Post.objects.all()
#     return queryset.select_related('category').filter(
#         is_published=True,
#         pub_date__lte=timezone.now(),
#         category__is_published=True
#     )

def index(request):
    posts = Post.objects.visible_to_user(request.user).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/index.html', {'page_obj': page_obj})

def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if (post.pub_date > timezone.now() or
        not post.is_published or
        not post.category.is_published):
        if not request.user.is_authenticated or post.author != request.user:
            raise Http404("Пост не найден или еще не опубликован")
    comments = post.comments.filter(is_published=True).select_related('author')
    comment_count = comments.count()
    comment_id = request.GET.get('edit_comment_id') or request.POST.get(
        'comment_id'
    )
    form = CommentForm()
    if comment_id:
        comment = get_object_or_404(Comment, id=comment_id)
        if comment.author == request.user:
            form = CommentForm(instance=comment)
        else:
            raise PermissionDenied(
                "Вы не можете редактировать этот комментарий"
            )
    if request.method == 'POST':
        if comment_id:
            comment = get_object_or_404(Comment, id=comment_id)
            if comment.author != request.user:
                raise PermissionDenied(
                    "Вы не можете редактировать этот комментарий"
                )
            form = CommentForm(request.POST, instance=comment)
            if form.is_valid():
                form.save()
        else:
            form = CommentForm(request.POST)
            if form.is_valid():
                new_comment = form.save(commit=False)
                new_comment.post = post
                new_comment.author = request.user
                new_comment.save()
        return redirect('blog:post_detail', post_id=post.id)
    elif request.GET.get('edit_comment_id'):
        pass
    context = {
        'post': post,
        'form': form,
        'comments': comments,
        'comment_count': comment_count,
    }
    return render(request, 'blog/detail.html', context)

def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = Post.objects.visible_to_user(request.user).filter(
        category=category,
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user)
    if request.user != user:
        posts = posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )
    posts = posts.annotate(comment_count=Count('comments')).order_by('-pub_date')
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': user,
        'page_obj': page_obj
    }
    return render(request, 'blog/profile.html', context)

def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)

def csrf_failure(request, *args, **kwargs):
    return render(request, 'pages/403csrf.html', status=403)

def handler500(request):
    return render(request, 'pages/500.html', status=500)

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm(initial={
            'pub_date': timezone.now()
        })
    return render(request, 'blog/create.html', {'form': form})

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    form = PostForm()
    return render(request, 'blog/create.html', {
        'post': post,
        'form': form,
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, 'blog/user.html', {'form': form})

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm()
    return render(request, 'blog/comment.html', {'form': form})

@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        raise PermissionDenied("Вы не можете редактировать этот комментарий")
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)
    context = {'form': form, 'comment': comment}
    return render(request, 'blog/comment.html', context)

@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        raise PermissionDenied("Вы не можете удалить этот комментарий")
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {
        'comment': comment,
        'post_id': post_id,
    })
###########################################################################
models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
User = get_user_model()

class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)
    def visible_to_user(self, user):
        return self.get_queryset().visible_to_user(user)

class Post(models.Model):
    title = models.CharField(
        max_length=256,
        verbose_name='Заголовок',
        help_text='Максимальная длина - 256 символов'
    )
    text = models.TextField(
        verbose_name='Текст'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        default=timezone.now,
        help_text=(
            'Если установить дату и время в будущем '
            '— можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='posts_images/',
        blank=True,
        null=True,
        help_text='Загрузите картинку'
    )
    objects = PostManager()
    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ['-pub_date']
    def __str__(self):
        return self.title

class Category(models.Model):
    title = models.CharField(
        max_length=256,
        verbose_name='Заголовок',
        help_text='Максимальная длина - 256 символов'
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )
    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ['title']
    def __str__(self):
        return self.title

class Location(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название места',
        help_text='Максимальная длина - 256 символов'
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )
    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'
        ordering = ['name']
    def __str__(self):
        return self.name

class Comment(models.Model):
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите текст комментария'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
        help_text='Пост, к которому относится комментарий'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время публикации комментария'
    )
    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть комментарий'
    )
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
    def __str__(self):
        return f'Комментарий от {self.author} к посту "{self.post.title}"'

class PostQuerySet(models.QuerySet):
    def visible_to_user(self, user):
        base_filters = Q(is_published=True) & Q(pub_date__lte=timezone.now())
        if not user.is_authenticated:
            return self.filter(base_filters & Q(category__is_published=True))
        elif user.is_superuser or user.is_staff:
            return self.all()
        else:
            return self.filter(
                (base_filters & Q(category__is_published=True))
            )
        
###################3




