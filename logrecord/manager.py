from logrecord.models import LogRecord


class LogManager:

    def extract_string(self, text, start_marker, end_marker):
        """提取两个标志位中间的字符串"""
        start_index = text.find(start_marker)
        if start_index == -1:
            return None
        start_index += len(start_marker)

        end_index = text.find(end_marker, start_index)
        if end_index == -1:
            return None

        return text[start_index:end_index]

    def add_log(self, request, type: int, action_flag: int, operation_content, remark=None):
        """
            添加用户操作

        """

        method = request.method
        full_path = request.get_full_path()
        username = request.user.username
        if remark and '[user]' in remark:
            username = self.extract_string(text=remark, start_marker='[user]', end_marker=';')
            if username is None:
                pass
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


user_operation_record = LogManager()