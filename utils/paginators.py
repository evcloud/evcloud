from django.core.paginator import Paginator


class NumsPaginator(Paginator):
    '''
    带自定义导航页码的分页器
    '''
    page_query_name = 'page'

    def __init__(self, request, object_list, per_page, **kwargs):
        self.request = request
        super().__init__(object_list, per_page, **kwargs)

    def get_page_nav(self, page):
        '''
        页码导航栏相关信息

        :return: dict
            {
                'previous': query_str, # str or None
                'next': query_str,     # str or None
                'page_list': [
                    [page_num:int or str, query_str:str, active:bool],
                ]
            }
        '''
        page_list = []
        current_page = page.number
        if self.num_pages >= 2:
            page_list = list(range(max(current_page - 2, 1), min(current_page + 2, self.num_pages) + 1))
            # 是否添加'...'
            if (page_list[0] - 1) >= 2:  # '...'在左边
                num = (current_page + 1) // 2
                page_list.insert(0, ('...', num))
            if (self.num_pages - page_list[-1]) >= 2:
                num = (current_page + self.num_pages) // 2
                page_list.append(('...', num))  # '...'在左边
            # 是否添加第1页
            if page_list[0] != 1:
                page_list.insert(0, 1)
            # 是否添加第最后一页
            if page_list[-1] != self.num_pages:
                page_list.append(self.num_pages)

        page_nav = {'page_list': self.get_page_list(page_list, current_page)}

        # 上一页
        if page.has_previous():
            page_nav['previous'] = self.build_page_url_query_str(page.previous_page_number())
        else:
            page_nav['previous'] = None
        # 下一页
        if page.has_next():
            page_nav['next'] = self.build_page_url_query_str(page.next_page_number())
        else:
            page_nav['next'] = None

        return page_nav

    def get_page_list(self, page_nums: list, current_page: int):
        '''
        构建页码导航栏 页码信息

        :param page_nums:
        :param current_page:
        :return:
            [[page_num:int, query_str:str, active:bool], ]
        '''
        page_list = []
        for p in page_nums:
            disp = p    # 页码显示内容
            num = p     # 页码
            if isinstance(p, tuple):
                disp, num = p

            active = False
            query_str = self.build_page_url_query_str(page_num=num)
            if num == current_page:
                active = True

            page_list.append([disp, query_str, active])

        return page_list

    def build_page_url_query_str(self, page_num: int):
        """
        构建页码对应的url query参数字符串

        :param page_num: 页码
        :return:
            str
        """
        querys = self.request.GET.copy()
        querys.setlist(self.page_query_name, [page_num])
        return querys.urlencode()
