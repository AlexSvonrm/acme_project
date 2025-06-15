
forms.py
from django import forms

from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.models import User

from .models import Post, Comment


class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


# 31/05/2025
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title', 'text', 'pub_date',
            'location', 'category', 'image'
        ]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }

views.py

from datetime import datetime

from django.core.paginator import Paginator

from django.core.exceptions import PermissionDenied

from django.contrib.auth.decorators import login_required

from django.contrib.auth.forms import UserChangeForm

from django.contrib.auth.models import User

from django.shortcuts import render, redirect, get_object_or_404

from django.http import Http404

from django.utils import timezone

from .models import Post, Category

from .forms import RegisterForm, PostForm, CommentForm

POSTS_LIMIT = 10


def get_published_posts(queryset=None):
    if queryset is None:
        queryset = Post.objects.all()
    return queryset.select_related('category').filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )


def index(request):
    posts = Post.objects.visible_to_user(request.user).filter(
        is_published=True,
        category__is_published=True
    )
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.pub_date > timezone.now() or not post.is_published or not post.category.is_published:
        if not request.user.is_authenticated or post.author != request.user:
            raise Http404("Пост не найден или еще не опубликован")

    form = CommentForm()
    return render(request, 'blog/detail.html', {'post': post, 'form': form})


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    posts = Post.objects.visible_to_user(request.user).filter(
        category=category,
        is_published=True
    )
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
    posts = Post.objects.visible_to_user(request.user).filter(author=user)
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': user,
        'page_obj': page_obj
    }
    return render(request, 'blog/profile.html', context)


# 26.05.2025
def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)


def handler500(request):
    return render(request, 'pages/500.html', status=500)


# 28.05.2025
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


# 31/05/2025
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

    return render(request, 'blog/add_comment.html', {'form': form})


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
    
    post.delete()
    return redirect('blog:index')




urls.py
from django.urls import path

from django.conf import settings

from django.conf.urls.static import static

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='registration'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'
    ),
    # 31/05/2025
    path('posts/create/', views.create_post, name='create_post'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('posts/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



ввв

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

    return render(request, 'blog/comment.html', {'form': form})


ааа

blogicum/urls.py
from django.contrib import admin

from django.contrib.auth.forms import UserCreationForm

from django.views.generic.edit import CreateView

from django.contrib.auth import views as auth_views

from django.contrib.auth.views import LogoutView

from django.urls import path, include, reverse_lazy


class CustomLogoutView(LogoutView):
    http_method_names = ["get", "post", "options"]

    def get(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


handler404 = 'blog.views.page_not_found'

handler403 = 'blog.views.csrf_failure'

handler500 = 'blog.views.handler500'

urlpatterns = [
    path('', include('blog.urls')),
    path('admin/', admin.site.urls),
    path('pages/', include('pages.urls')),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', CustomLogoutView.as_view(), name='logout'),
    path(
        'password_change/',
        auth_views.PasswordChangeView.as_view(),
        name='password_change'
    ),
    path(
        'password_change/done/',
        auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'
    ),
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'
    ),
    path('accounts/', include('django.contrib.auth.urls')),
    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('blog:index'),
        ),
        name='registration',
    ),
]
20:36
blog/views.py
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


def get_published_posts(queryset=None):
    if queryset is None:
        queryset = Post.objects.all()
    return queryset.select_related('category').filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )


def index(request):
    posts = Post.objects.visible_to_user(request.user).filter(
        is_published=True,
        category__is_published=True
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
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
        is_published=True
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
    posts = Post.objects.visible_to_user(request.user).filter(
        author=user
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
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


def csrf_failure(request, reason=''):
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

    return render(request, 'blog/add_comment.html', {'form': form})


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
    
    post.delete()
    return redirect('blog:index')
20:37
Терминал выдает:
 File "D:\Dev\django-sprint4\venv\Lib\site-packages\django\contrib\auth\decorators.py", line 60, in viewwrapper
    return view_func(request, args, *kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Dev\django-sprint4\blogicum\blog\views.py", line 240, in delete_comment
    raise PermissionDenied("Вы не можете удалить этот комментарий")
django.core.exceptions.PermissionDenied: Вы не можете удалить этот комментарий
[04/Jun/2025 22:33:14] "GET /posts/48/delete_comment/57/ HTTP/1.1" 500 79109
D:\Dev\django-sprint4\blogicum\blog\views.py changed, reloading.
В новой версии этот параметр похоже приходить стал. Добавь **kwargs в параметры представления. Он в себя примет этот параметр 



def csrf_failure(request, reason=None, exception=None, template_name="pages/403csrf.html"):
    # Эта функция может быть вызвана как для CSRF-сбоев (с аргументом 'reason'),
    # так и для других ошибок 403 (с аргументом 'exception', если handler403 указывает сюда).
    # В данном простом случае мы не используем 'reason' или 'exception' в шаблоне.
    # Если бы 'reason' был обязателен, можно было бы сделать:
    # if reason is None and exception is not None: reason = str(exception)
    return render(request, template_name, status=403)





