from .models import Image

class ImageError(Exception):
    '''
    镜像相关错误类型定义
    '''
    def __init__(self, code:int=0, msg:str='', err=None):
        '''
        :param code: 错误码
        :param msg: 错误信息
        :param err: 错误对象
        '''
        self.code = code
        self.msg = msg
        self.err = err

    def __str__(self):
        return self.detail()

    def detail(self):
        '''错误详情'''
        if self.msg:
            return self.msg

        if self.err:
            return str(self.err)

        return '未知的错误'


class ImageManager:
    '''
    镜像管理器
    '''
    def get_image_by_id(self, image_id:int):
        '''
        通过id获取镜像元数据模型对象
        :param image_id: 镜像id
        :return:
            Image() # success
            None    #不存在

        :raise ImageError
        '''
        if not isinstance(image_id, int) or image_id < 0:
            raise ImageError(msg='镜像ID参数有误')

        try:
            return Image.objects.filter(id=image_id).first()
        except Exception as e:
            raise ImageError(msg=f'查询镜像时错误,{str(e)}')





