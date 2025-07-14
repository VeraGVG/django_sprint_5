"""
Файл с view-функциями для отображений основных страниц сайта.
Добавлены функции для обработки добавления, изменения и удаления постов
и комментариев.
"""
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, ChangeUserInfoForm
from datetime import datetime
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required


User = get_user_model()  # Получение модели пользователя


def index(request):
    """Отображение главной страницы с постами"""
    template = 'blog/index.html'
    posts = Post.objects.select_related(
        'category',
        'location',
        'author').filter(
        pub_date__lte=datetime.now().date(),
        is_published__exact=True,
        category__is_published__exact=True
    ).order_by('-pub_date')
    for obj in posts:  # Добавление атрибута с количеством комментариев
        post_id = obj.id
        count = len(Comment.objects.select_related(
            'post'
        ).filter(post__id__exact=post_id))
        obj.comment_count = count
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, id):
    """Отображение страницы конкретного поста"""
    template = 'blog/detail.html'
    username = request.user.username
    post = get_object_or_404(
        Post.objects.select_related('category', 'location', 'author').filter(
            Q(
                Q(pub_date__lte=datetime.now())
                & Q(is_published=True)
                & Q(category__is_published=True))
            | Q(author__username__exact=username)
        ),
        pk=id)
    comments = Comment.objects.select_related(
        'post',
        'author'
    ).filter(post__id__exact=id)
    form = CommentForm(request.POST or None)
    context = {'post': post, 'form': form, 'comments': comments}
    return render(request, template, context)


def category_posts(request, slug):
    """Отображение списка постов с заданной категорией"""
    template = 'blog/category.html'
    category = get_object_or_404(Category.objects.values(
        'title',
        'description').filter(
        slug__exact=slug,
        is_published=True,))
    post_list = Post.objects.select_related(
        'category',
        'location',
        'author').filter(
        pub_date__lte=datetime.now(),
        is_published=True,
        category__slug__exact=slug
    ).order_by('-pub_date')
    for obj in post_list:  # Добавление атрибута с количеством комментариев
        post_id = obj.id
        count = len(Comment.objects.select_related(
            'post'
        ).filter(post__id__exact=post_id))
        obj.comment_count = count
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'category': category
    }
    return render(request, template, context)


@login_required
def edit_profile(request, username):
    """
    Страница изменения информации в профиле.
    Для изменения профиле необходимо быть залогиненым
    """
    template = 'blog/user.html'
    user = get_object_or_404(User, username=username)
    form = ChangeUserInfoForm(request.POST or None, instance=user)
    context = {'form': form}
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=username)
    return render(request, template, context)


def profile(request, username):
    """Страница профиля"""
    req_username = request.user.username
    template = 'blog/profile.html'
    user = get_object_or_404(User, username=username)
    posts = Post.objects.select_related(
        'category',
        'location',
        'author').filter(Q(author__username__exact=username)
    ).order_by('-pub_date')
    if req_username != username:
        posts = posts.filter(pub_date__lte=datetime.now(),
                             is_published=True,).order_by('-pub_date')
    for obj in posts:  # Добавление атрибута с количеством комментариев
        post_id = obj.id
        count = len(Comment.objects.select_related(
            'post'
        ).filter(post__id__exact=post_id))
        obj.comment_count = count
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'profile': user, 'page_obj': page_obj}
    return render(request, template, context=context)


@login_required
def post(request, id=None):
    """
    Страница создания или изменения поста.
    За определение цели отвечает наличие параметра id
    """
    user = request.user
    username = user.username
    # Если в запросе указан pk (т.е. получен запрос на редактирование объекта):
    if id is not None:
        # Получаем объект модели или выбрасываем 404 ошибку.
        instance = get_object_or_404(Post.objects.select_related(
            'category',
            'location',
            'author'
        ).filter(
            Q(pub_date__lte=datetime.now())
            & Q(is_published=True)
            & Q(category__is_published=True)
            & Q(author__username__exact=username)
        ), pk=id)
    # Если в запросе не указан pk
    # (если получен запрос к странице создания записи):
    else:
        # Связывать форму с объектом не нужно, установим значение None.
        instance = None
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=instance)
    context = {'form': form}
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = user
        new_post.save()
        if id:
            return redirect('blog:post_detail', id=id)
        return redirect('blog:profile', username=username)

    return render(request, 'blog/create.html', context)


@login_required
def edit_post(request, id):
    instance = get_object_or_404(Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        Q(pub_date__lte=datetime.now())
        & Q(is_published=True)
        & Q(category__is_published=True)
    ), pk=id)
    author = instance.author
    if author != request.user:
        return redirect('blog:post_detail', id=id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=instance)
    context = {'form': form}
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', id=id)
    return render(request, 'blog/create.html', context)


@login_required
def delete_post(request, post_id):
    """Страница удаления поста"""
    # Получаем объект модели или выбрасываем 404 ошибку.
    username = request.user.username
    instance = get_object_or_404(Post.objects.select_related(
        'category',
        'location',
        'author').filter(
            Q(pub_date__lte=datetime.now())
            & Q(is_published=True)
            & Q(category__is_published=True)
            & Q(author__username__exact=username), pk=post_id))
    # В форму передаём только объект модели;
    # передавать в форму параметры запроса не нужно.
    form = PostForm(instance=instance)
    context = {'form': form}
    user = request.user
    username = user.username
    if request.method == 'POST':
        # ...удаляем объект:
        instance.delete()
        # ...и переадресовываем пользователя на страницу со списком записей.
        return redirect('blog:profile', username=username)
    # Если был получен GET-запрос — отображаем форму.
    return render(request, 'blog/create.html', context)


@login_required
def comment(request, post_id):
    """Страница создания комментария"""
    post = get_object_or_404(Post.objects.select_related(
        'category',
        'location',
        'author').filter(
            Q(pub_date__lte=datetime.now())
            & Q(is_published=True)
            & Q(category__is_published=True), pk=post_id))
    form = CommentForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('blog:post_detail', id=post_id)
    return render(request, 'blog/detail.html', context=context)


def edit_comment(request, post_id, comment_id):
    """
    Страница изменения комментария.
    Для корректной работы необходимо передавать в контекст
    сам комментарий.
    """
    user = request.user
    username = user.username
    instance = get_object_or_404(Comment.objects.select_related(
        'post',
        'author'
    ).filter(author__username__exact=username), pk=comment_id)
    instance.post_id = post_id  # Добавление атрибута с id поста
    form = CommentForm(request.POST or None, instance=instance)
    context = {'form': form, 'comment': instance}
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', id=post_id)
    return render(request, 'blog/comment.html', context=context)


def delete_comment(request, post_id, comment_id):
    """
    Подтверждение удаления комментария.
    Для корректной работы необходимо передавать в контекст
    сам комментарий.
    """
    user = request.user
    username = user.username
    instance = get_object_or_404(Comment.objects.select_related(
        'author',
        'post'
    ).filter(
        Q(author__username__exact=username)
    ), pk=comment_id)
    instance.post_id = post_id  # Добавление атрибута с id поста
    context = {'comment': instance}
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:post_detail', id=post_id)
    return render(request, 'blog/comment.html', context)
