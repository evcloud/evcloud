import urllib
from urllib import parse

from logrecord.models import LogRecord


def extract_string(text):
    """提取操作用户"""

    user_list = text.rsplit(';')

    if len(user_list) == 1:
        return None, user_list[0].rsplit('[user]', 1)[1]

    if '[vo]' in user_list[0]:
        return user_list[0].split('[vo]', 1)[1], user_list[1].rsplit('[user]', 1)[1]

    if '[vo]' in user_list[1]:
        return user_list[1].split('[vo]', 1)[1], user_list[0].rsplit('[user]', 1)[1]


class LogManager:

    def add_log(self, request, operation_content, remark=None):
        """
            添加用户操作
        """
        method = request.method
        full_path = request.get_full_path()
        vo_or_user = request.query_params.get('_who_action', '')
        username = request.user.username
        real_user = ''
        if vo_or_user:
            vo , real_user = extract_string(text=vo_or_user)
            remark = f'项目组：{vo}, {remark}' if vo else remark

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
