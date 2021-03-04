from django.shortcuts import render


def docs(request, *args, **kwargs):
    """
    文档函数视图
    """
    return render(request, 'index.html')
