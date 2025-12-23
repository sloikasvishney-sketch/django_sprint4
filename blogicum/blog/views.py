from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserForm

User = get_user_model()


def get_posts_with_comment_count(queryset=None, filter_published=True):
    """Добавляет количество комментариев к queryset постов.
    
    Args:
        queryset: QuerySet постов. Если None, используется Post.objects.all()
        filter_published: Если True, фильтрует только опубликованные посты.
                         Если False, пропускает фильтрацию (для постов автора).
    """
    if queryset is None:
        queryset = Post.objects.all()
    if filter_published:
        queryset = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by(*Post._meta.ordering)


def get_page_obj(queryset, request, per_page=10):
    """Возвращает объект страницы пагинатора для queryset."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    )
    post_list = get_posts_with_comment_count(post_list, filter_published=True)
    page_obj = get_page_obj(post_list, request)
    
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, id):
    # Первый вызов: извлечение поста по ключу из полной таблицы
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author'),
        id=id
    )
    
    # Второй вызов: для не-авторов проверяем доступ через опубликованные посты
    if request.user != post.author:
        post = get_object_or_404(
            Post.objects.select_related('category', 'location', 'author').filter(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            ),
            id=id
        )
    
    comments = post.comments.all()
    form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = category.post_set.select_related(
        'category', 'location', 'author'
    )
    post_list = get_posts_with_comment_count(post_list, filter_published=True)
    page_obj = get_page_obj(post_list, request)
    
    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', id=post_id)
    return render(request, 'blog/create.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if post.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    
    form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('blog:post_detail', id=post_id)
    return redirect('blog:post_detail', id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', id=post_id)
    
    context = {
        'form': form,
        'comment': comment
    }
    return render(request, 'blog/comment.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)
    
    context = {
        'comment': comment
    }
    return render(request, 'blog/comment.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    
    # Для автора показываем все посты, для остальных - только опубликованные
    post_list = user.post_set.select_related(
        'category', 'location', 'author'
    )
    filter_published = request.user != user
    post_list = get_posts_with_comment_count(post_list, filter_published=filter_published)
    page_obj = get_page_obj(post_list, request)
    
    context = {
        'profile': user,
        'page_obj': page_obj
    }
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    form = UserForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/user.html', {'form': form})


def registration(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')
    return render(request, 'registration/registration_form.html', {'form': form})
