import os

import rados, rbd  #yum install python36-rbd.x86_64 python-rados.x86_64

from .models import CephCluster


class RadosError(rados.Error):
    '''def __init__(self, message, errno=None)'''
    pass

class RbdManager:
    '''
    ceph rbd 操作管理接口
    '''
    def __init__(self, conf_file:str, keyring_file:str, pool_name:str):
        '''
        raise RadosError
        '''
        if not os.path.exists(conf_file):
            raise RadosError("参数有误，配置文件路径不存在")
        self._conf_file = conf_file

        if keyring_file and not os.path.exists(keyring_file):
            raise RadosError("参数有误，keyring配置文件路径不存在")
        self._keyring_file = keyring_file

        self.pool_name = pool_name
        self._cluster = None
        self._cluster = self.get_cluster()    # 与ceph连接的Rados对象

    def __enter__(self):
        self.get_cluster()
        return self

    def __exit__(self, type_, value, traceback):
        self.shutdown()
        return False  # __exit__返回的是False，有异常不被忽略会向上抛出。

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        '''关闭与ceph的连接'''
        if self._cluster:
            self._cluster.shutdown()
            self._cluster = None

    def get_cluster(self):
        '''
        获取已连接到ceph集群的Rados对象
        :return:
            success: Rados()
        :raises: class:`RadosError`
        '''
        if self._cluster and self._cluster.state == 'connected':
            return self._cluster

        try:
            self._cluster = rados.Rados(conffile=self._conf_file, conf={'keyring': self._keyring_file})
            self._cluster.connect(timeout=5)
            return self._cluster
        except rados.Error as e:
            msg = e.args[0] if e.args else 'error connecting to the cluster'
            raise RadosError(msg)

    def create_snap(self,image_name:str, snap_name:str):
        '''
        为一个rbd image(卷)创建快照

        :param image_name: 要创建快照的rbd卷名称
        :param snap_name: 快照名称
        :return:
            True    # success
            raise RadosError # failed

        :raise class: `RadosError`
        '''
        cluster = self.get_cluster()
        try:
            with cluster.open_ioctx(self.pool_name) as ioctx:
                with rbd.Image(ioctx=ioctx, name=image_name) as image:
                    image.create_snap(snap_name)  # Create a snapshot of the image.
        except Exception as e:
            raise RadosError(f'create_snap error:{str(e)}')

        return True

    def rename_image(self, image_name:str, new_name:str):
        '''
        重命名一个rbd image

        :param image_name: 被重命名的image卷名称
        :param new_name: image的新名称
        :return:
            True    # success
            raise RadosError # failed

        :raise class: `RadosError`
        '''
        cluster = self.get_cluster()
        try:
            with cluster.open_ioctx(self.pool_name) as ioctx:
                rbd.RBD().rename(ioctx=ioctx, src=image_name, dest=new_name)
        except rbd.ImageNotFound as e:
            raise RadosError('rename_image error: image not found')
        except Exception as e:
            raise RadosError(f'rename_image error:{str(e)}')

        return True

    def remove_image(self, image_name:str):
        '''
        删除一个rbd image

        :param image_name: image name
        :return:
            True    # success
            raise RadosError # failed

        :raise class: `RadosError`
        '''
        cluster = self.get_cluster()
        try:
            with cluster.open_ioctx(self.pool_name) as ioctx:
                rbd.RBD().remove(ioctx=ioctx, name=image_name)
        except rbd.ImageNotFound as e:
            return True
        except Exception as e:
            raise RadosError(f'remove_image error:{str(e)}')

        return True

    def clone_image(self, snap_image_name:str, snap_name:str, new_image_name:str):
        '''
        从快照克隆一个rbd image

        :param snap_image_name: 快照父image名称
        :param snap_name: 快照名称
        :param new_image_name: 新克隆的image名称
        :return:
            True    # success
            raise RadosError # failed

        :raise class: `RadosError`
        '''
        cluster = self.get_cluster()
        try:
            with cluster.open_ioctx(self.pool_name) as p_ioctx:
                c_ioctx = p_ioctx   # 克隆的image保存在同一个pool
                rbd.RBD().clone(p_ioctx=p_ioctx, p_name=snap_image_name, p_snapname=snap_name, c_ioctx=c_ioctx,
                                c_name=new_image_name)
        except Exception as e:
            raise RadosError(f'rename_image error:{str(e)}')

        return True

    def list_images(self):
        '''
        获取pool中所有image

        :return:
            list    # success
            raise RadosError # failed

        :raise class: `RadosError`
        '''
        cluster = self.get_cluster()
        try:
            with cluster.open_ioctx(self.pool_name) as ioctx:
                return  rbd.RBD().list(ioctx)  # 返回 Image name list
        except Exception as e:
            raise RadosError(f'rename_image error:{str(e)}')


class CephClusterManager:
    '''
    CEPH集群管理器
    '''

    def get_ceph_by_id(self, ceph_id: int):
        '''
        通过id获取ceph集群配置对象

        :param ceph_id: ceph集群id
        :return:
            Host() # success
            None    #不存在
        :raise RadosError
        '''
        if not isinstance(ceph_id, int) or ceph_id <= 0:
            raise RadosError('CEPH集群ID参数有误')

        try:
            return CephCluster.objects.filter(id=ceph_id).first()
        except Exception as e:
            raise RadosError(f'查询CEPH集群时错误,{str(e)}')




