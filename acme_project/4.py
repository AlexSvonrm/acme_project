from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from django.http import Http404
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.views.generic import (
    CreateView, DeleteView, DetailView, UpdateView, ListView
)
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from .constants import INDEX_POSTS_COUNT
from .models import Category, Post, Comment
from .forms import PostForm, CommentForm, ProfileForm
from .forms import PasswordChangeForm, CustomUserCreationForm
from django.db.models import Count











from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.forms import PasswordChangeForm
# from django.contrib.auth.models import User

from .models import Post, Comment





from django.contrib.auth import get_user_model
from django.db import models
# from django.urls import reverse

from .constants import INDEX_TEXT_LIMIT
from core.models import PublishedModel




from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, reverse_lazy

# from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView


from blog.forms import CustomUserCreationForm




@login_required
def proposal(request):
    """Предлагает новую статью."""
    # form = PostForm(request.POST or None)
    # context = {'form': form}
    # if form.is_valid():
    #     form.save()
    # return render(request, 'blog/profile.html', context)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Пост умпешно опубликован')
            return redirect('blog:post_detail', post_id=post.pk)
        else:
            messages.error(
                request,
                'В вашем сообщении были допущены ошибки. Исправьте их.'
            )

    else:
        form = PostForm()

    context = {'form': form}
    return render(request, 'blog/create.html', context)


PostDetailView:     
    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
 , а стало: 

    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        if not post.is_published and post.author != self.request.user:
            raise Http404("Пост не найден")
        return post

