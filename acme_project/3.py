class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'pk'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if not request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=self.object.pk)
        

        if self.object.author != request.user:
            return HttpResponseForbidden("Нельзя редактировать чужой пост")
        
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})


urls: 

path('posts/<int:post_id>/edit/', views.PostUpdateView.as_view(), name='post_edit'),

#####################################
blog/forms.py


from django import forms
from .models import User, Post, Comment

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email")

class PostEditForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ("author", "created_at")
        widgets = {
            "text": forms.Textarea({"rows": "5"}),
            "pub_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

class CommentEditForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        widgets = {
            "text": forms.Textarea({"rows": "3"})
        }


Было в class PostDetailView:     
    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
 , а стало: 

    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        if not post.is_published and post.author != self.request.user:
            raise Http404("Пост не найден")
        return post

