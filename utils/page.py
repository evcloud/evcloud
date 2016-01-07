
import re
import random
  
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.conf import settings
from django.shortcuts import render_to_response as dj_render_to_response
from django.template import RequestContext

class Page:
    def __init__(self, objs, c, p):
        self._pageor = Paginator(objs, c)
        if p > self._pageor.num_pages:
            p = self._pageor.num_pages
        elif p < 1:
            p = 1
        
        self._page = self._pageor.page(p)


        self.count = self._pageor.count
        self.num_pages = self._pageor.num_pages
        self.per_page = c
        self.start_page = 1
        self.end_page = self.num_pages

        self.object_list = self._page.object_list
        self.num_cur_page = self._page.number
        self.start_index = self._page.start_index()
        self.end_index = self._page.end_index()


        _t = [self.num_cur_page]
        while len(_t) < 5 and (_t[len(_t)-1] < self.num_pages or _t[0] > 1):
            if _t[0] > 1:
                _t = [_t[0] -1] + _t
            if _t[len(_t)-1] < self.num_pages:
                _t = _t + [_t[len(_t)-1] + 1]
        if len(_t) == 1:
            _t = []  
        self.page_range = _t


    def has_next(self):
        return self._page.has_next()

    def has_previous(self):
        return self._page.has_previous()

    def next_page_number(self):
        return self._page.next_page_number()

    def previous_page_number(self):
        return self._page.previous_page_number()

    def has_other_pages(self):
        return self._page.has_other_pages()

def get_page(objs, request, perpage=0):
    try:
        page_num = int(request.GET.get('page', 1))
    except ValueError:
        page_num = 1    

    if perpage == 0:
        try:
            perpage = int(request.GET.get('perpage', 15))
        except ValueError:
            perpage = 15

    p = Page(objs, perpage, page_num)

    get_list = []
    for g in request.GET.items():
        if g[0] != 'page':
            get_list.append(g[0] + '=' + g[1])
    get_list.append('page=')
    p.link = '?' + '&'.join(get_list)
    return p

