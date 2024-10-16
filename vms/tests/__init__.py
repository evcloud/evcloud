from ceph.models import GlobalConfig
from vms.models import Vm


def config_res_admin(username: str, is_res: bool = True):
    obj = GlobalConfig.objects.filter(name=GlobalConfig.ConfigName.RESOURCE_ADMIN.value).first()
    if obj is None:
        obj = GlobalConfig(
            name=GlobalConfig.ConfigName.RESOURCE_ADMIN.value,
            content='', remark=''
        )
        obj.save(force_insert=True)

    usernames = obj.content.split(',')
    if is_res and username not in usernames:
        usernames.append(username)
        obj.content = ','.join(usernames)
        obj.save(update_fields=['content'])
    elif not is_res and username in usernames:
        usernames.remove(username)
        obj.content = ','.join(usernames)
        obj.save(update_fields=['content'])

    return obj


def create_vm_metadata(uuid, owner, image=None, ceph_pool=None, mac_ip=None, host=None):
    """创建 虚拟机元数据"""
    image_name = image_parent = ''
    if image:
        image_name = image.name
        image_parent = image.name

    vm = Vm(
        disk_type=Vm.DiskType.CEPH_RBD,
        sys_disk_size=10,
        uuid=uuid,
        name=uuid,
        vcpu=2,
        mem=2,
        disk=uuid,
        image=image,
        user=owner,
        xml='#',
        image_name=image_name,
        image_parent=image_parent,
        image_size=10,
        ceph_pool=ceph_pool,
        mac_ip=mac_ip,
        host=host,
    )
    vm.save(force_insert=True)
    return vm
