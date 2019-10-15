from .models import Image

from vms import errors
from vms.errors import VmError


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

        :raise VmError
        '''
        if not isinstance(image_id, int) or image_id < 0:
            raise VmError(code=errors.ERR_IMAGE_ID, msg='镜像ID参数有误')

        try:
            return Image.objects.filter(id=image_id).first()
        except Exception as e:
            raise VmError(msg=f'查询镜像时错误,{str(e)}')
