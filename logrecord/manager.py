from logrecord.models import LogRecord


class LogManager:

    def extract_string_remark(self, text, start_marker, end_marker):
        """提取两个标志位中间的字符串"""
        start_index = text.find(start_marker)
        if start_index == -1:
            return None
        start_index += len(start_marker)

        end_index = text.find(end_marker, start_index)
        if end_index == -1:
            return None

        return text[start_index:end_index]

    def extract_string_url(self, text, start_marker):
        """提取一个标志位后面的字符串"""

        if not text:
            return None

        start_index = text.find(start_marker)
        if start_index == -1:
            return None
        start_index += len(start_marker)
        #
        # end_index = text.find(end_marker, start_index)
        # if end_index == -1:
        #     return None

        return text[start_index:]

    def add_log(self, request, type: int, action_flag: int, operation_content, remark=None):
        """
            添加用户操作
            :param :

        """

        method = request.method
        full_path = request.get_full_path()

        username , flag = self.get_username(request=request, full_path=full_path, remark=remark)
        if flag:
            operation_content = f'用户({username}), {operation_content}'  # 本地登录用户
        else:
            operation_content = f'用户(cstcloud:{username}), {operation_content}'

        try:
            LogRecord.objects.create(
                method=method,
                action_flag=action_flag,
                operation_content=operation_content,
                resourc_type=type,
                full_path=full_path,
                message=remark,
                username=username
            )
        except Exception as e:
            pass

    def get_username(self, request, full_path, remark):
        flag = False
        username = self.get_request_url_user(url=full_path)  # 尝试从 url 中 获取数据
        if username :
            return username, flag

        username = self.extract_string_remark(text=remark, start_marker='[user]', end_marker=';')  #尝试从 remart 中 获取数据
        if username:
            return username, flag

        username = request.user.username
        if username != 'cstcloud':
                flag = True

        return username, flag


    def get_log_record(self, type_list: list = [], timestamp=None):
        """获取日志"""
        if timestamp:
            return LogRecord.objects.filter(create_time__gt=timestamp).all().exclude(resourc_type__in=type_list)
        return LogRecord.objects.all().exclude(resourc_type__in=type_list)


    def get_request_url_user(self, url):
        """获取请求路径的用户"""
        username = self.extract_string_url(text=url, start_marker='[user]')

        return username



user_operation_record = LogManager()
