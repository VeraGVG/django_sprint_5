"""
Файл с кастомной функцией для страницы создания пользователя.
Переопределение функции для страницы создания пользователя нужно было
для добавления возможности отправки письма
"""
from django.contrib.auth import get_user_model
from .forms import MyUserCreationForm
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import login

UserModel = get_user_model()


def create_user(request):
    form = MyUserCreationForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        email = form.cleaned_data['email']
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password1'])
        user.save()
        send_mail(
            subject='Регистрация',
            message='Спасибо за регистрацию!',
            from_email='from@example.com',
            recipient_list=[email],
            fail_silently=True,
        )
        login(request, user)
        return redirect('blog:index')
    return render(request, 'registration/registration_form.html', context)
