"""
Файл с отображениями статичных страниц.
Согласно требованиям задания, view-функции для страниц
с правилами и информацией о сайте заменены на view-классы.
Здесь же переопределены функции для отображения страниц ошибок.
"""
from django.shortcuts import render
from django.views.generic import TemplateView


def about(request):
    template = 'pages/about.html'
    return render(request, template)


class AboutDetailView(TemplateView):
    template_name = 'pages/about.html'


def rules(request):
    template = 'pages/rules.html'
    return render(request, template)


class RulesDetailView(TemplateView):
    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    template = 'pages/404.html'
    return render(request, template, status=404)


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)


def server_error(request):
    return render(request, 'pages/500.html', status=500)
