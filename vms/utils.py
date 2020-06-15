import random
import string


def rand_string(length=10):
    """
    生成随机字符串

    :param length: 字符串长度
    :return:
        str
    """
    if length <= 0:
        return ''

    return ''.join(random.sample(string.ascii_letters + string.digits, length))
