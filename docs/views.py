from django.shortcuts import render

# Create your views here.
def docs(request, *args, **kwargs):
    '''
    文档函数视图
    '''
    return render(request, 'index.html')
