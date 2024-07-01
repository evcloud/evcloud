# 公共镜像上传
import hashlib
import os
import subprocess
import sys
import time
import argparse
from pathlib import Path

import math
import requests
from django import setup
from django.utils import timezone

# 将项目路径添加到系统搜寻路径当中，查找方式为从当前脚本开始，找到要调用的django项目的路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
# print(f'sds - {str(Path(__file__).resolve().parent.parent.parent)}')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_site.settings')
setup()

from image.models import MirrorImageTask, Image
from utils.loggers import config_script_logger
from ceph.models import CephCluster, CephPool
from ceph.managers import get_rbd_manager

mirror_image_task_logger = config_script_logger(name='app-mirror-image-task', filename='app_mirror_image_task.log')

parser = argparse.ArgumentParser(description='')
parser.add_argument('-t', '--task_id', type=int, help='镜像任务id')
parser.add_argument('-o', '--operate', type=str, help='上传下载（push/pull）')
args = parser.parse_args()

read_chunk_size = (1024 ** 2) * 100


class MirrorImageHandler:

    def get_mirror_image_task(self, task_id: int) -> MirrorImageTask:
        return MirrorImageTask.objects.filter(id=task_id).first()

    def get_image(self, name: str, version: str) -> Image:
        return Image.objects.get(name=name, version=version).first()

    def create_os_image(self, ceph_id, task: MirrorImageTask):
        sys_type_dict = {'Windows': 1, 'Linux': 2, 'Unix': 3, 'MacOS': 4, 'Android': 5, '其他': 6}

        release_dict = {'Windows Desktop': 1, 'Windows Server': 2, 'Ubuntu': 3, 'Fedora': 4, 'Centos': 5, 'Rocky': 6,
                        'Unknown': 7}

        architecture_dict = {'x86-64': 1, 'i386': 2, 'arm-64': 3, 'unknown': 4}

        boot_mode_dict = {'UEFI': 1, 'BIOS': 2}

        mirror_image_sys_type = sys_type_dict[
            task.mirror_image_sys_type] if task.mirror_image_sys_type in sys_type_dict else sys_type_dict['其他']

        mirror_image_release = release_dict[
            task.mirror_image_release] if task.mirror_image_release in release_dict else release_dict['Unknown']

        mirror_image_architecture = architecture_dict[
            task.mirror_image_architecture] if task.mirror_image_architecture in architecture_dict else \
            architecture_dict['unknown']

        mirror_image_boot_mode = boot_mode_dict[
            task.mirror_image_boot_mode] if task.mirror_image_boot_mode in boot_mode_dict else boot_mode_dict['BIOS']

        image_os = Image.objects.filter(name=task.mirror_image_name).first()

        if image_os:
            raise Exception(f'操作系统镜像({task.mirror_image_name})已存在，不能重复添加')

        try:
            obj = Image.objects.create(
                name=task.mirror_image_name,
                sys_type=mirror_image_sys_type,
                version=task.mirror_image_version,
                release=mirror_image_release,
                architecture=mirror_image_architecture,
                boot_mode=mirror_image_boot_mode,
                ceph_pool_id=ceph_id,
                tag=1,
                base_image=task.mirror_image_base_image,
                enable=task.mirror_image_enable,
                xml_tpl_id=task.mirror_image_xml_tpl,
                # user_id=task.user,
                default_user=task.mirror_image_default_user,
                default_password=task.mirror_image_default_password,
                size=task.mirror_image_size,
                mirror_image_market=True
            )
        except Exception as e:
            raise Exception(f'保存系统镜像出错：{str(e)}')

        return obj

    def ceph_image_exists(self, ceph, pool_name, image_name):
        """镜像是否存在"""
        try:
            rbd = get_rbd_manager(ceph=ceph, pool_name=pool_name)
            return rbd.image_exists(image_name=image_name)
        except Exception as e:
            raise e

    def remove_ceph_image(self, ceph, pool_name, image_name):
        """删除ceph 镜像"""
        try:
            rbd = get_rbd_manager(ceph=ceph, pool_name=pool_name)
            return rbd.remove_image(image_name=image_name)
        except Exception as e:
            raise e

    def delete_local_image(self, image_local_path):

        if os.path.exists(image_local_path):

            try:
                os.remove(image_local_path)
            except Exception as e:
                raise Exception(f'删除本地镜像({image_local_path})失败： {str(e)}')

    def get_local_ceph_id(self):

        try:
            # Run the ceph -s command and capture its output
            process = subprocess.Popen(['ceph', '-s'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            # Decode stdout assuming UTF-8 (adjust if necessary)
            output = stdout.decode('utf-8')

            # Split the output by lines
            lines = output.strip().split('\n')

            # Find the line containing the cluster ID
            for line in lines:
                if 'id:' in line:
                    cluster_id = line.split(':')[1].strip()
                    return cluster_id
            else:
                mirror_image_task_logger.error(f'使用 ceph -s 命令， 未找到Cluster ID')

            # Handle stderr if needed
            if stderr:
                mirror_image_task_logger.error(f'subproces命令查询错误: {stderr.decode("utf-8")}')
                return None

        except Exception as e:
            mirror_image_task_logger.error(f'subprocess 查询错误: {e}')
            return None

    def get_ceph_pool(self):
        ceph_uuid = self.get_local_ceph_id()
        if not ceph_uuid:
            raise Exception(f'数据库未找到有关 {ceph_uuid} ceph 的配置数据')

        # ceph_cluster = CephCluster.objects.filter(uuid=ceph_uuid).first()
        # if not ceph_cluster:
        #     return None

        ceph = CephPool.objects.filter(ceph__uuid=ceph_uuid, pool_name='vm').first()
        if not ceph:
            raise Exception(f'数据库未找到 vm 存储池数据')

        return ceph

    def export_rbd_image(self, export_image_path, image_name, linux_node):
        """

        :param export_image_path: 导出镜像路径(包括镜像名称)
        :param image_name: 镜像名称
        :param linux_node: linux 的服务节点
        :param canonical_name: 镜像规范名称 系统发行版本__系统发行编号_系统架构_系统启动方式_时间戳 centos_7_x86_bios_11111.qcow2
        """

        ceph = self.get_ceph_pool()
        cpeh_pool_name = ceph.pool_name
        # os.makedirs(export_image_path, exist_ok=True, mode=0o755)  # 目录权限 755

        if export_image_path.endswith('/'):
            raise Exception(f'下载到本地的路径拼写有误，格式为（/xxx/xxx/123.qcow2）, 现在的格式（{export_image_path}）')

        if not os.path.exists(export_image_path):
            image_local_path_dir = export_image_path.rsplit('/', 1)[0]
            try:
                os.makedirs(image_local_path_dir, exist_ok=True)
            except Exception as e:
                raise Exception(f'创建({image_local_path_dir})路径失败：{str(e)}')

        # 定义导出镜像为 qcow2 格式的命令
        # export_command = f'rbd export {cpeh_pool_name}/{image_name} {export_image_path} --format=qcow2'
        export_command = f'qemu-img convert -f raw -O qcow2 rbd:{cpeh_pool_name}/{image_name} {export_image_path}'

        # 使用 subprocess 运行命令
        process = subprocess.Popen(export_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # 检查命令是否成功执行
        if process.returncode == 0:
            msg = f'节点 {linux_node} - 成功从池 {cpeh_pool_name} 导出镜像 {image_name} 到 {export_image_path}，格式为 qcow2。'
            mirror_image_task_logger.info(msg)
        else:
            msg = f'节点 {linux_node} - 导出 {image_name} 到 qcow2 格式失败。错误信息: {stderr.decode("utf-8")}'
            mirror_image_task_logger.error(msg)
            raise Exception(msg)

    def import_rbd_image(self, import_image_path, image_name, linux_node, cpeh_pool_name):
        """

        :param import_image_path: 导入镜像路径  到镜像名称：xx/xx/xx.qcow2
        :param image_name: 镜像任务中的镜像
        """

        # 查询镜像是否存在，存在报错，不能删除需要管理员去操作

        try:
            # 定义导出镜像为 qcow2 格式的命令
            import_command = f'qemu-img convert -p -f qcow2 -O raw {import_image_path} rbd:{cpeh_pool_name}/{image_name}'

            # 使用 subprocess 运行命令
            process = subprocess.Popen(import_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            # 检查命令是否成功执行
            if process.returncode == 0:
                msg = f'节点 {linux_node} - 成功将镜像 {image_name} 导入到 {cpeh_pool_name} 池中，{import_image_path} 格式为 qcow2。'
                mirror_image_task_logger.info(msg)
            else:
                msg = f'节点 {linux_node} - 将 {import_image_path} 导入 {cpeh_pool_name}/{image_name} 池失败， 错误信息: {stderr.decode("utf-8")}'
                raise Exception(msg)

        except Exception as e:
            msg = f'节点 {linux_node} - 导入镜像时出错：{e}'
            raise Exception(msg)
            # 数据库有标记是否重新下载，旧的会删除

    def read_in_chunks(self, file_path, chunk_size=read_chunk_size):
        try:
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except FileNotFoundError:
            return Exception(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            return Exception(f"Error reading file '{file_path}': {e}")

    def request_upload_chunk(self, chunk, url, bucket_token, bucket_name, objpath, offset):
        """上传块"""
        if not url.endswith('/'):
            url = url + '/'

        if objpath.startswith('/'):
            objpath = objpath.split('/', 1)[1]

        url = f'{url}api/v2/obj/{bucket_name}/{objpath}?offset={offset}'

        # print(f'{offset} - {len(chunk)} - {url}')

        m = hashlib.md5()
        m.update(chunk)

        header = {
            "Authorization": f"BucketToken {bucket_token}",
            'Content-MD5': m.hexdigest()
        }

        req = requests.post(
            url=url, data=chunk, headers=header
        )
        if req.status_code == 200:
            return
        else:
            raise Exception(f'上传块错误: {req.text}')

    def get_remote_image(self, url, bucket_name, objpath, bucket_token):
        url = f'{url}api/v1/metadata/{bucket_name}/{objpath}/'

        header = {
            "Authorization": f"BucketToken {bucket_token}",
        }

        req = requests.get(
            url=url, headers=header
        )

        if req.status_code == 200:
            return req.json()['obj']

        msg = f'公共镜像中查找 {objpath}，错误信息：{req.text}'
        raise Exception(msg)

    def write_local_image_path(self, chunk, image_local_path):
        """将镜像写入路径"""
        if image_local_path.endswith('/'):
            raise Exception(f'下载到本地的路径拼写有误，格式为（/xxx/xxx/123.qcow2）, 现在的格式（{image_local_path}）')

        if not os.path.exists(image_local_path):
            image_local_path_dir = image_local_path.rsplit('/', 1)[0]
            try:
                os.makedirs(image_local_path_dir, exist_ok=True)
            except Exception as e:
                raise Exception(f'创建({image_local_path_dir})路径失败：{str(e)}')

        try:
            with open(image_local_path, 'ab+') as f:
                f.write(chunk)
        except Exception as e:
            raise Exception(f'镜像写入文件失败：{str(e)}')

    def conversion_file_unit(self, size: int):

        unit_size = size / (1024 ** 3)  # GB

        return math.ceil(unit_size)

    def request_download_image(self, url, bucket_token, bucket_name, objpath, image_local_path):
        """下载镜像"""

        if not url.endswith('/'):
            url = url + '/'

        remote_image_obj = self.get_remote_image(url=url, bucket_name=bucket_name, objpath=objpath,
                                                 bucket_token=bucket_token)

        remote_image_obj_size = remote_image_obj['si']

        header = {
            "Authorization": f"BucketToken {bucket_token}",
        }

        chunk_size = read_chunk_size
        offset = 0
        count = 1
        base_url = f'{url}api/v1/obj/{bucket_name}/{objpath}/'
        while True:

            if chunk_size > remote_image_obj_size:
                chunk_size = remote_image_obj_size

            url = f'{base_url}?offset={offset}&size={chunk_size}'

            # print(f'第 {count} 块 {offset} - {chunk_size} - {remote_image_obj_size}')

            req = requests.get(url=url, headers=header)
            if req.status_code == 200:
                try:

                    self.write_local_image_path(chunk=req.content, image_local_path=image_local_path)
                except Exception as e:
                    raise Exception(f'{image_local_path} 位置 {offset} {str(e)}')
            else:
                raise Exception(f'{image_local_path} 位置 {offset} 下载块错误: {req.text}')

            if (remote_image_obj_size - offset) < chunk_size:
                # 下载完成
                mirror_image_task_logger.info(f'{image_local_path} 下载成功')

                return self.conversion_file_unit(remote_image_obj_size)

            little_chunk_size = remote_image_obj_size - offset
            if little_chunk_size < chunk_size:
                chunk_size = little_chunk_size

            offset += chunk_size
            count += 1

    def upload_image(self, image_path, image_task):
        """上传镜像"""
        if not os.path.exists(image_path):
            raise Exception(f'未找到 {image_path} 文件')

        chunks = self.read_in_chunks(file_path=image_path)

        offset = 0
        count = 1
        for chunk in chunks:
            try:
                print(f'第 {count} 块 ')
                self.request_upload_chunk(chunk=chunk, url=image_task.mirrors_image_service_url,
                                          bucket_token=image_task.token, bucket_name=image_task.bucket_name,
                                          objpath=image_task.file_path, offset=offset)
            except Exception as e:
                mirror_image_task_logger.error(
                    f'镜像地址：{image_path}， 上传偏移：{offset}, 上传到远程：{image_task.mirrors_image_service_url}, 上传远程的位置：{image_task.file_path}，{str(e)} ')
                raise e
            offset += len(chunk)
            count += 1

    def push_image(self, task):

        if task.status == MirrorImageTask.NONESTATUS:
            mirror_image_task_logger.error(f'任务({task.id}) 未导入镜像前停止服务')
            return

        image_local_path = f'{task.update_local_path}{task.mirror_image_base_image}'

        # 删除镜像
        try:
            self.delete_local_image(image_local_path)
        except Exception as e:
            msg = f'删除本地镜像时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 5
            task.save(update_fields=['error_msg', 'status'])
            return

        if task.status == MirrorImageTask.NONESTATUS:
            mirror_image_task_logger.error(f'任务({task.id}) 未导出镜像前停止服务')
            return

        # 先导出镜像
        task.export_date = timezone.now()
        task.save(update_fields=['export_date'])

        try:
            self.export_rbd_image(export_image_path=image_local_path,
                                  image_name=task.mirror_image_base_image,
                                  linux_node=task.local_hostname)
        except Exception as e:
            msg = f'导出镜像时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 5
            task.save(update_fields=['error_msg', 'status'])
            return

        task.export_date_complate = timezone.now()
        task.save(update_fields=['export_date_complate'])

        if task.status == MirrorImageTask.NONESTATUS:
            mirror_image_task_logger.error(f'任务({task.id}) 未上传镜像前停止服务')
            return

        # 上传镜像
        try:
            self.upload_image(image_local_path, task)
        except Exception as e:
            msg = f'上传镜像时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 5
            task.save(update_fields=['error_msg', 'status'])
            return

        task.status = 4  # 上传完成
        task.download_or_upload_status = True  # 上传完成
        task.save(update_fields=['status', 'download_or_upload_status'])

        # 删除镜像
        try:
            self.delete_local_image(image_local_path)
        except Exception as e:
            msg = f'镜像上传后删除本地镜像时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.save(update_fields=['error_msg'])
            return

    def pull_image(self, task: MirrorImageTask, download_flag=True):

        if task.status == MirrorImageTask.NONESTATUS:
            mirror_image_task_logger.error(f'任务({task.id}) 未导入镜像前停止服务')
            return

        image_local_path = f'{task.download_local_path}{task.file_path.split("/")[-1]}'  # 本地的镜像路径

        # 先查询 镜像是否存在 mirror_image_base_image

        try:
            ceph_pool = self.get_ceph_pool()
        except Exception as e:
            msg = f'获取本地ceph信息时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 6
            task.save(update_fields=['error_msg', 'status'])
            return

        try:

            image_exists_bool = self.ceph_image_exists(ceph=ceph_pool.ceph, pool_name=ceph_pool.pool_name,
                                                       image_name=task.mirror_image_base_image)
        except Exception as e:
            msg = f'查询该镜像（{task.mirror_image_base_image}）是否存在本地ceph中存储池（{ceph_pool.pool_name}）时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 6
            task.save(update_fields=['error_msg', 'status'])
            return

        if image_exists_bool:
            task.error_msg = f"ceph(uuid={ceph_pool.ceph.uuid}), 存储池({ceph_pool.pool_name}), 镜像({task.mirror_image_base_image})存在，等管理员处理"
            task.status = 6
            task.save(update_fields=['error_msg', 'status'])
            return

        if task.status == MirrorImageTask.NONESTATUS:
            mirror_image_task_logger.error(f'任务({task.id}) 未下载镜像前停止服务')
            return

        if download_flag:
            # 查询本地镜像是否存在：如果存在删除
            try:
                self.delete_local_image(image_local_path)
            except Exception as e:
                msg = str(e)
                mirror_image_task_logger.error(msg)
                task.error_msg = msg
                task.status = 6
                task.save(update_fields=['error_msg', 'status'])
                return

            # 下载 镜像
            try:
                size = self.request_download_image(url=task.mirrors_image_service_url, bucket_name=task.bucket_name,
                                                   bucket_token=task.token, objpath=task.file_path,
                                                   image_local_path=image_local_path)
            except Exception as e:
                msg = f'从公共镜像下载时：{str(e)}'
                mirror_image_task_logger.error(msg)

                task.error_msg = msg
                task.status = 6
                task.save(update_fields=['error_msg', 'status'])
                return

            task.import_date = timezone.now()
            task.mirror_image_size = size
            task.download_or_upload_status = True
            task.save(update_fields=['import_date', 'mirror_image_size', 'download_or_upload_status'])

        if task.status == MirrorImageTask.NONESTATUS:
            mirror_image_task_logger.error(f'任务({task.id}) 未导入镜像前停止服务')
            return

        try:
            self.import_rbd_image(import_image_path=image_local_path, cpeh_pool_name=ceph_pool.pool_name,
                                  linux_node=task.local_hostname, image_name=task.mirror_image_base_image)
        except Exception as e:
            msg = f'导入qcow2镜像时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 6
            task.save(update_fields=['error_msg', 'status'])
            return

        task.import_date_complate = timezone.now()
        task.status = 2  # 下载完成
        task.save(update_fields=['import_date_complate', 'status'])

        if task.status == MirrorImageTask.NONESTATUS:
            mirror_image_task_logger.error(f'任务({task.id}) 未创建操作系统镜像信息前停止服务')
            return

        try:
            self.create_os_image(ceph_id=ceph_pool.id, task=task)
        except Exception as e:
            msg = f'创建操作系统镜像数据时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 6
            task.save(update_fields=['error_msg', 'status'])
            return

        task.create_os_image = True
        task.save(update_fields=['create_os_image'])

        # 删除镜像
        try:
            self.delete_local_image(image_local_path)
        except Exception as e:
            msg = f'镜像导入后删除本地镜像时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.save(update_fields=['error_msg'])
            return

    def ceph_image_exists_delete(self, task):
        """导出"""

        try:
            ceph_pool = self.get_ceph_pool()
        except Exception as e:
            msg = f'获取本地ceph信息时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 6
            task.save(update_fields=['error_msg', 'status'])
            return

        try:

            image_exists_bool = self.ceph_image_exists(ceph=ceph_pool.ceph, pool_name=ceph_pool.pool_name,
                                                       image_name=task.mirror_image_base_image)
        except Exception as e:
            msg = f'查询该镜像（{task.mirror_image_base_image}）是否存在本地ceph中存储池（{ceph_pool.pool_name}）时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 6
            task.save(update_fields=['error_msg', 'status'])
            return

        if not image_exists_bool:
            return

        try:
            self.remove_ceph_image(ceph=ceph_pool.ceph, pool_name=ceph_pool.pool_name,
                                   image_name=task.mirror_image_base_image)
        except Exception as e:
            msg = f'删除镜像（{task.mirror_image_base_image}）在本地ceph中存储池（{ceph_pool.pool_name}）时：{str(e)}'
            mirror_image_task_logger.error(msg)
            task.error_msg = msg
            task.status = 6
            task.save(update_fields=['error_msg', 'status'])
            return


def loacl_node_run_server(task: MirrorImageTask, operate):
    """此节点能否运行服务"""

    hostname = os.uname().nodename
    if not task.local_hostname:
        if task.operate == 1:
            task.status = 6
        else:
            task.status = 5
        task.error_msg = '任务中没有执行的节点信息'
        task.save(update_fields=['status', 'error_msg'])
        return

    # 检查基本的信息

    if task.status in [2, 4]:  # 下载完成或上传完成
        return

    if task.operate == 1 and task.status == 3:
        msg = f'命令错误：操作是下载，而状态是上传中'
        mirror_image_task_logger.error(msg)
        task.error_msg = msg
        task.status = 6
        task.save(update_fields=['error_msg', 'status'])

        return
    if task.operate == 2 and task.status == 1:
        msg = f'命令错误：操作是上传，而状态是下载中'
        mirror_image_task_logger.error(msg)
        task.error_msg = msg
        task.status = 6
        task.save(update_fields=['error_msg', 'status'])

        return

    handler = MirrorImageHandler()

    image_name = task.file_path.split("/")[-1]

    if not image_name.endswith('.qcow2'):
        msg = f'file_path 文件名称错误，格式/xxx/xxx.qcow2'
        mirror_image_task_logger.error(msg)
        task.error_msg = msg
        task.status = 6
        task.save(update_fields=['error_msg', 'status'])

        return

    image_local_path = f'{task.download_local_path}{task.file_path.split("/")[-1]}'

    if task.status == 6:  # 下载失败：
        if hostname == task.local_hostname:

            task.status = 1
            task.save(update_fields=['status'])

        else:
            task.local_hostname = hostname
            task.save(update_fields=['local_hostname'])
            return handler.pull_image(task)  # 镜像导入报错需要管理员操作

        if not task.download_or_upload_status:
            # 没有下载完成， 重新下载
            return handler.pull_image(task)
        elif not task.import_date:
            # 没有导入，查看文件是否存在
            return handler.pull_image(task)

        elif not task.import_date_complate:
            # handler.ceph_image_exists_delete(task)
            return handler.pull_image(task)  # 不需要查看本地文件重新下载
        elif not task.create_os_image:

            try:
                ceph_pool = handler.get_ceph_pool()
            except Exception as e:
                msg = f'获取本地ceph信息时：{str(e)}'
                mirror_image_task_logger.error(msg)
                task.error_msg = msg
                task.status = 6
                task.save(update_fields=['error_msg', 'status'])
                return

            try:
                handler.create_os_image(ceph_id=ceph_pool.id, task=task)
            except Exception as e:
                msg = f'创建系统镜像信息时：{str(e)}'
                mirror_image_task_logger.error(msg)
                task.error_msg = msg
                task.status = 6
                task.save(update_fields=['error_msg', 'status'])
                return

            task.create_os_image = True
            task.status = 2
            task.save(update_fields=['create_os_image', 'status'])
            handler.delete_local_image(image_local_path)

            return

    if task.status == 5:  # 上传失败
        if hostname == task.local_hostname:
            task.status = 2
            task.save(update_fields=['status'])

        else:
            task.local_hostname = hostname
            task.save(update_fields=['local_hostname'])
            return handler.push_image(task)

        return handler.push_image(task)

    if operate == 'pull':
        if task.status == 1:
            return
        task.status = 1
        task.save(update_fields=['status'])
        return handler.pull_image(task=task)

    if operate == 'push':
        if task.status == 3:
            return
        task.status = 3
        task.save(update_fields=['status'])
        return handler.push_image(task=task)


def main(task_id, operate):
    if operate not in ['pull', 'push']:
        mirror_image_task_logger.error(f'命令执行方法不正确 {operate}')
        return

    # 确定目录空间

    mirror_image_handler = MirrorImageHandler()
    image_task = mirror_image_handler.get_mirror_image_task(task_id=task_id)
    if not image_task:
        # 写日志
        mirror_image_task_logger.error(f'未找到 id={task_id} 的公共镜像任务信息')
        return

    try:
        loacl_node_run_server(task=image_task, operate=operate)
    except Exception as e:
        mirror_image_task_logger.error(f'报错信息：{str(e)}')
        return


if __name__ == '__main__':
    main(args.task_id, args.operate)
