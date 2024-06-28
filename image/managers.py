from django.db.models import Q

from .models import Image, MirrorImageTask, VmXmlTemplate
from compute.managers import CenterManager, ComputeError
from utils.errors import ImageError, BadRequestError, Error


class ImageManager:
    """
    镜像管理器
    """

    @staticmethod
    def get_image_by_id(image_id: int, related_fields: tuple = ()):
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

    @staticmethod
    def get_image_queryset():
        """
        可用镜像查询集
        :return:
            QuerySet()
        """
        return Image.objects.all()

    def get_image_queryset_by_center(self, center_or_id):
        """
        获取一个数据中心下的所有镜像查询集

        :param center_or_id: 数据中心对象或id
        :return:
             images: QuerySet   # success
        :raise ImageError
        """
        try:
            pool_ids = CenterManager().get_pool_ids_by_center(center_or_id)
        except ComputeError as e:
            raise ImageError(msg=str(e))
        return self.get_image_queryset().filter(ceph_pool__in=pool_ids).all()

    def get_image_queryset_by_type(self, type_or_id):
        """
        获取一个镜像类型的所有镜像查询集

        :param type_or_id: 类型对象或id
        :return:
             images: QuerySet   # success
        :raise ImageError
        """
        return self.get_image_queryset().filter(type=type_or_id).all()

    def get_image_queryset_by_systype(self, sys_type: int):
        """
        获取一个系统类型的所有镜像查询集

        :param sys_type: 系统类型
        :return:
             images: QuerySet   # success
        :raise ImageError
        """
        return self.get_image_queryset().filter(sys_type=sys_type).all()

    def get_image_queryset_by_tag(self, tag: int):
        """
        获取一个标签的所有镜像查询集

        :param tag: 镜像标签
        :return:
             images: QuerySet   # success
        :raise ImageError
        """
        return self.get_image_queryset().filter(tag=tag).all()

    def filter_image_queryset(self, center_id: int, sys_type: int, tag: int, search: str,
                              all_no_filters: bool = False, related_fields: tuple = ()):
        """
        通过条件筛选镜像查询集

        :param center_id: 数据中心id,大于0有效
        :param sys_type: 系统类型,大于0有效
        :param tag: 镜像标签,大于0有效
        :param search: 关键字筛选条件
        :param all_no_filters: 筛选条件都无效时；True: 返回所有； False: 抛出错误
        :param related_fields: 外键字段；外键字段直接一起获取，而不是惰性的用时再获取
        :return:
            QuerySet()

        :raises: ImageError
        """
        if center_id <= 0 and sys_type <= 0 and tag <= 0 and not search:
            if not all_no_filters:
                return self.get_image_queryset().filter(enable=True).select_related(*related_fields).all()
            else:
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
        if not all_no_filters:
            return queryset.filter(enable=True).select_related(*related_fields).all()
        else:
            return queryset.select_related(*related_fields).all()

    def get_xml_template(self):

        return VmXmlTemplate.objects.all()


class MirrorImageManager:
    """公共镜像任务管理"""

    def get_mirror_image_task(self):
        """获取公共镜像任务所有数据"""

        return MirrorImageTask.objects.all()

    def get_mirror_image_queryset(self, task_id: int = None, status: int = None):

        query = self.get_mirror_image_task()
        if task_id:
            query = query.filter(id=int(task_id))

        if status:
            query = query.filter(status=int(status))

        return query

    def add_mirror_image_pull_task(self, task_dict):

        if 'mirror_image_name' not in task_dict or 'mirror_image_base_image' not in task_dict:
            raise BadRequestError(msg=f'mirror_image_name 和 mirror_image_base_image 必填且不能为string')

        try:
            obj = MirrorImageTask.objects.create(**task_dict)
        except Exception as e:
            raise Error(msg=str(e))

        return obj

    def modify_mirror_image_pull_task(self, task_dict, task_id):
        obj = MirrorImageTask.objects.filter(id=task_id).first()

        if not obj:
            raise BadRequestError(msg=f'未找到{task_id}信息')
        try:
            MirrorImageTask.objects.filter(id=task_id).update(**task_dict)
        except Exception as e:
            raise Error(msg=f'修改信息失败：{str(e)}')

        return obj

    def add_mirror_image_push_task(self, task_dict, image_id):

        image = Image.objects.filter(id=image_id).first()

        if not image:
            raise BadRequestError(msg=f'image_id 内容填写不正确')

        mirror_image_obj = MirrorImageTask.objects.filter(mirror_image_name=image.name, mirror_image_version=image.version, operate=2).first()
        if mirror_image_obj:
            raise BadRequestError(msg=f'请删除任务(id={mirror_image_obj.id})后重新操作，不允许添加重复的数据。')

        try:
            obj = MirrorImageTask.objects.create(
                mirror_image_name=image.name,
                mirror_image_sys_type=image.get_sys_type_display(),
                mirror_image_version=image.version,
                mirror_image_release=image.get_release_display(),
                mirror_image_architecture=image.get_architecture_display(),
                mirror_image_boot_mode=image.get_boot_mode_display(),
                mirror_image_base_image=image.base_image,
                mirror_image_enable=image.enable,
                mirror_image_xml_tpl=image.xml_tpl_id,
                mirror_image_default_user=image.default_user,
                mirror_image_default_password=image.default_password,
                mirror_image_size=image.size,
                **task_dict
            )
        except Exception as e:
            raise Error(msg=str(e))

        return obj
