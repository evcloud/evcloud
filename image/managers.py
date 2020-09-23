from django.db.models import Q

from .models import Image, ImageType
from compute.managers import CenterManager, ComputeError
from utils.errors import ImageError


class ImageManager:
    """
    镜像管理器
    """
    def get_image_by_id(self, image_id: int, related_fields: tuple = ()):
        """
        通过id获取镜像元数据模型对象
        :param image_id: 镜像id
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            Image() # success
            None    #不存在

        :raise ImageError
        """
        if not isinstance(image_id, int) or image_id < 0:
            raise ImageError(msg='镜像ID参数有误')

        try:
            if related_fields:
                return Image.objects.select_related(*related_fields).filter(id=image_id).first()
            return Image.objects.filter(id=image_id).first()
        except Exception as e:
            raise ImageError(msg=f'查询镜像时错误,{str(e)}')

    def get_image_type_queryset(self):
        '''
        可用镜像类型查询集
        :return:
            QuerySet()
        '''
        return ImageType.objects.all()

    def get_image_queryset(self):
        '''
        可用镜像查询集
        :return:
            QuerySet()
        '''
        return Image.objects.filter(enable=True).all()

    def get_image_queryset_by_center(self, center_or_id):
        '''
        获取一个分中心下的所有镜像查询集

        :param center_or_id: 分中心对象或id
        :return:
             images: QuerySet   # success
        :raise ImageError
        '''
        try:
            pool_ids = CenterManager().get_pool_ids_by_center(center_or_id)
        except ComputeError as e:
            raise ImageError(msg=str(e))
        return self.get_image_queryset().filter(ceph_pool__in=pool_ids).all()

    def get_image_queryset_by_type(self, type_or_id):
        '''
        获取一个镜像类型的所有镜像查询集

        :param type_or_id: 类型对象或id
        :return:
             images: QuerySet   # success
        :raise ImageError
        '''
        return self.get_image_queryset().filter(type=type_or_id).all()

    def get_image_queryset_by_systype(self, sys_type:int):
        '''
        获取一个系统类型的所有镜像查询集

        :param sys_type: 系统类型
        :return:
             images: QuerySet   # success
        :raise ImageError
        '''
        return self.get_image_queryset().filter(sys_type=sys_type).all()

    def get_image_queryset_by_tag(self, tag:int):
        '''
        获取一个标签的所有镜像查询集

        :param tag: 镜像标签
        :return:
             images: QuerySet   # success
        :raise ImageError
        '''
        return self.get_image_queryset().filter(tag=tag).all()

    def filter_image_queryset(self, center_id:int, sys_type:int, tag:int, search:str,
                              all_no_filters: bool = False, related_fields:tuple=()):
        '''
        通过条件筛选镜像查询集

        :param center_id: 分中心id,大于0有效
        :param sys_type: 系统类型,大于0有效
        :param tag: 镜像标签,大于0有效
        :param user_id: 用户id,大于0有效
        :param search: 关键字筛选条件
        :param all_no_filters: 筛选条件都无效时；True: 返回所有； False: 抛出错误
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            QuerySet()

        :raises: ImageError
        '''
        if center_id <= 0 and sys_type <= 0 and tag <= 0 and not search:
            if not all_no_filters:
                raise ImageError(msg='查询条件无效')

            return self.get_image_queryset().select_related(*related_fields).all()

        queryset = None
        if center_id > 0:
            queryset = self.get_image_queryset_by_center(center_id)

        if sys_type > 0:
            if queryset is not None:
                queryset = queryset.filter(sys_type=sys_type).all()
            else:
                queryset = self.get_image_queryset_by_systype(sys_type)

        if tag > 0:
            if queryset is not None:
                queryset = queryset.filter(tag=tag).all()
            else:
                queryset = self.get_image_queryset_by_tag(tag)

        if search:
            if queryset is not None:
                queryset = queryset.filter(Q(desc__icontains=search) | Q(name__icontains=search)).all()
            else:
                queryset = self.get_image_queryset().filter(Q(desc__icontains=search) | Q(name__icontains=search)).all()

        return queryset.select_related(*related_fields).all()

