from logrecord.models import LogRecord


class LogManager:

    def extract_string(self, text, start_marker, end_marker=None):
        """提取两个标志位中间的字符串"""
        start_index = text.find(start_marker)
        if start_index == -1:
            return None
        start_index += len(start_marker)

        if end_marker:
            end_index = text.find(end_marker, start_index)
            if end_index == -1:
                return None
            return text[start_index:end_index]

        return text[start_index:]

    def add_log(self, request, operation_content, remark=None):
        """
            添加用户操作
            :param :

        """

        method = request.method
        full_path = request.get_full_path()

        real_user , username = self.get_username(request=request, full_path=full_path, remark=remark)

        try:
            LogRecord.objects.create(
                method=method,
                operation_content=operation_content,
                full_path=full_path,
                message=remark,
                username=username,
                real_user=real_user,
            )
        except Exception as e:
            pass

    def get_username(self, request, full_path, remark):
        request_username = request.user.username
        username = self.extract_string(text=full_path, start_marker='[user]')  # 尝试从 url 中 获取数据
        if username :
            # /?_who_action=%5Buser%5Dxxxxx%40cnic.cn&vm_uuid=xxxxx
            if '&' in username:
                username = username.split('&')[0]
            return username, request_username

        username = self.extract_string(text=remark, start_marker='[user]', end_marker=';')  #尝试从 remart 中 获取数据
        if username:
            return username, request_username


        return '', request_username

    def get_log_record(self, kwargs):
        """获取日志"""

        if kwargs:
            return LogRecord.objects.filter(**kwargs).all()

        return LogRecord.objects.all()

    def get_log_records_order_by(self, order_by, kwargs):
        """获取排序后的数据

        :param order_by:排序字段
        """
        return self.get_log_record(kwargs).order_by(order_by)


user_operation_record = LogManager()
