from logrecord.models import LogRecord
from utils.iprestrict import IPRestrictor


def extract_string(text):
    """
    提取操作用户

    :retrun: (
        vo_name: str,
        username: str
    )
    正常格式：
        [user]xxx@cnic.cn
        [vo]vo_name;[user]xxx@cnic.cn
    """
    vo_name = ''
    username = ''
    if not text:
        return vo_name, username

    items = text.split(';')
    for s in items:
        try:

            if '[user]' in s:
                username = s.split('[user]')[1]
            elif '[vo]' in s:
                vo_name = s.split('[vo]')[1]
        except Exception as e:
            pass

    return vo_name, username


class LogManager:

    def add_log(self, request, operation_content, remark='', owner=None):
        """
            添加用户操作
        """
        method = request.method
        full_path = request.get_full_path()
        vo_or_user = request.query_params.get('_who_action', '')
        username = request.user.username
        real_user = ''
        if vo_or_user:
            vo, real_user = extract_string(text=vo_or_user)
            remark = f'项目组：{vo}, {remark}' if vo else remark

        if not real_user and owner:
            real_user = owner.username

        try:
            clinet_ip, _ = IPRestrictor().get_remote_ip(request)
            LogRecord.objects.create(
                method=method,
                operation_content=operation_content,
                full_path=full_path,
                message=remark,  # 为None 会报错，导致无法写入数据
                username=username,
                real_user=real_user,
                request_ip=clinet_ip if clinet_ip else '',
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
