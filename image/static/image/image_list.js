;'use strict';
(function () {

    var VM_STATUS_CN = {
        0: '故障0', //无状态
        1: '运行',
        2: '阻塞',
        3: '暂停',
        4: '关机',
        5: '关机',
        6: '崩溃',
        7: '暂停',
        8: '故障',  //libvirt预留状态码
        9: '无法访问宿主机',  //宿主机连接失败
        10: '云主机丢失',  //虚拟机丢失
        11: '云主机不存在'
    };

    var VM_STATUS_LABEL = {
        0: 'default',
        1: 'success',
        2: 'info',
        3: 'info',
        4: 'info',
        5: 'info',
        6: 'danger',
        7: 'info',
        8: 'default',
        9: 'danger',
        10: 'warning',
        11: 'warning'
    };

    //
    // 页面刷新时执行
    window.onload = function () {
        // 虚拟机列表运行状态查询更新
        update_vms_status(get_image_list_uuid_array());
    };


    //
    // 获取table中所有镜像的id数组
    //
    function get_image_list_uuid_array() {
        var arr = [];
        let bucket_list_checked = $(".table-vm-list :hidden.item-checkbox");
        bucket_list_checked.each(function (i) {
            arr.push($(this).val());
        });

        return arr;
    }

    // 获取并设置虚拟机的运行状态
    function get_vm_status(vmid) {
        let node_status = $("#vm_status_" + vmid);
        node_status.html(`<i class="fa fa-spinner fa-pulse"></i>`);
        let api = build_absolute_url('image/image-vm-operate/');
        $.ajax({
            url: api,
            type: 'post',
            data: {'image_id': vmid, 'operation': 'get-vm-status'},
            dataType: "json",
            success: function (data, status, xhr) {
                if (xhr.status === 200) {
                    node_status.html('<span class="badge  badge-' + VM_STATUS_LABEL[data.status.status_code] + '">' + VM_STATUS_CN[data.status.status_code] + "</span>");
                } else {
                    node_status.html('<span class="badge  badge-danger">查询失败</span>');
                }
            },
            error: function (xhr) {
                node_status.html('<span class="badge  badge-danger">查询失败</span>');
                ;
            },
            complete: function () {

            }
        })
    }

    function update_vms_status(vmids) {
        for (let i in vmids) {
            get_vm_status(vmids[i]);
        }
    }

    // 刷新虚拟机状态点击事件
    $(".btn-update-vm-status").click(function (e) {
        e.preventDefault();
        update_vms_status(get_image_list_uuid_array());
    });

    // VNC点击事件
    $(".btn-vnc-open").click(function (e) {
        e.preventDefault();
        let image_id = $(this).attr('data-image-id');
        let api = build_absolute_url('image/image-vm-operate/');
        $.ajax({
            url: api,
            type: 'post',
            data: {'image_id': image_id, 'operation': 'get-vnc-url'},
            dataType: "json",
            success: function (data, status, xhr) {
                if (xhr.status === 200) {
                    window.open(data.vnc_url, '_blank');
                } else {
                    alert("打开vnc失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '打开vnc失败!';
                try {
                    msg = msg + xhr.responseJSON.code_text;
                } catch (e) {
                }
                alert(msg);
            },
            complete: function () {

            }
        })

    });

    // 更新镜像点击事件
    $(".btn-image-update").click(function (e) {
        e.preventDefault();
        let api = build_absolute_url('image/');
        let image_id = $(this).attr('data-image-id');
        let json_data = JSON.stringify({'image_id': image_id});
        $.ajax({
            url: api,
            type: 'put',
            data: {'image_id': image_id},
            dataType: "json",
            success: function (data, status, xhr) {
                if (xhr.status === 200) {
                    if (confirm('镜像更新成功,刷新查看？')) {
                        window.location = '/image/';
                    }
                } else {
                    alert("镜像更新失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '镜像更新失败!';
                try {
                    msg = msg + xhr.responseJSON.code_text;
                } catch (e) {
                }
                alert(msg);
            },
            complete: function () {

            }
        })
    });

    // 开机点击事件
    $(".btn-vm-start").click(function (e) {
        e.preventDefault();
        let image_id = $(this).attr('data-image-id');
        let api = build_absolute_url('image/image-vm-operate/');
        let node_status = $("#vm_status_" + image_id);
        node_status.html(`开机中`);
        $.ajax({
            url: api,
            type: 'post',
            dataType: "json",
            data: {'image_id': image_id, 'operation': 'start-vm'},
            success: function (data, status, xhr) {
                if (xhr.status === 200) {
                    get_vm_status(image_id)
                } else {
                    alert("虚拟机启动失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '开机操作失败!';
                try {
                    msg = msg + xhr.responseJSON.code_text;
                } catch (e) {
                }
                alert(msg);
            },
            complete: function () {

            }
        })
    });

    // 关机点击事件
    $(".btn-vm-shutdown").click(function (e) {
        e.preventDefault();
        let image_id = $(this).attr('data-image-id');
        let api = build_absolute_url('image/image-vm-operate/');
        let node_status = $("#vm_status_" + image_id);
        node_status.html(`关机中`);
        $.ajax({
            url: api,
            type: 'post',
            dataType: "json",
            data: {'image_id': image_id, 'operation': 'shutdown-vm'},
            success: function (data, status, xhr) {
                if (xhr.status === 200) {
                    get_vm_status(image_id)
                } else {
                    alert("虚拟机启动失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '关机操作失败!';
                try {
                    msg = msg + xhr.responseJSON.code_text;
                } catch (e) {
                }
                alert(msg);
            },
            complete: function () {

            }
        })
    });


    // 强制断电虚拟机点击事件
    $(".btn-vm-poweroff").click(function (e) {
        e.preventDefault();
        let image_id = $(this).attr('data-image-id');
        let api = build_absolute_url('image/image-vm-operate/');
        let node_status = $("#vm_status_" + image_id);
        node_status.html(`强制断电中`);
        $.ajax({
            url: api,
            type: 'post',
            dataType: "json",
            data: {'image_id': image_id, 'operation': 'poweroff-vm'},
            success: function (data, status, xhr) {
                if (xhr.status === 200) {
                    get_vm_status(image_id)
                } else {
                    alert("虚拟机启动失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '镜像更新失败!';
                try {
                    msg = msg + xhr.responseJSON.code_text;
                } catch (e) {
                }
                alert(msg);
            },
            complete: function () {

            }
        })
    });

})();

