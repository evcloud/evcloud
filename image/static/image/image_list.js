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
        10: '未找到',  //虚拟机丢失
        11: '虚拟机不存在'
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

    $('.edit_image_remark').click(function (e) {
        e.preventDefault();

        let div_show = $(this).parent();
        div_show.hide();
        div_show.next().show();
    });

    $('.save_image_remark').click(function (e) {
        e.preventDefault();
        let image_id = $(this).attr('data-image-id');
        let dom_remark = $(this).prev();
        let remark = dom_remark.val();
        let div_edit = dom_remark.parent();
        let div_show = div_edit.prev();

        $.ajax({
            url: '/api/v3/image/' + image_id + '/remark/?remark=' + remark,
            type: 'patch',
            success: function (data) {
                div_show.children("span:first").text(remark);
            },
            error: function (e) {
                alert('修改失败');
            },
            complete: function () {
                div_show.show();
                div_edit.hide();
            }
        });

    });


    //
    // 页面刷新时执行
    window.onload = function () {
        $("#nav_image_list").addClass("active");// 激活列表导航栏
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
        let current_button = $(this);
        let snap_element = $('#snap_' + image_id);
        current_button.html(`<i class="fa fa-spinner fa-pulse"></i>`);
        $.ajax({
            url: api,
            type: 'put',
            data: {'image_id': image_id, 'operation': 'snap_update'},
            dataType: "json",
            success: function (data, status, xhr) {
                if (xhr.status === 200) {
                    snap_element.html(data.snap + `<span class="badge badge-secondary">new</span>`)
                    current_button.html(`更新`);
                    // if (confirm('镜像更新成功,刷新查看？')) {
                    //     window.location = '/image/';
                    // }
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

    // 镜像启用开关点击事件
    $('.image-enable-switch').click(function (e) {
        e.preventDefault();
        let image_id = $(this).attr('data-image-id');
        let loading_button = $('#switch_loading_button_' + image_id);
        let checkbox_enable = $('#checkbox_enable_' + image_id);
        loading_button.html(`<i class="fa fa-spinner fa-pulse"></i>`);
        checkbox_enable.prop('disabled', true);

        let api = build_absolute_url('image/');
        $.ajax({
            url: api,
            type: 'put',
            data: {'image_id': image_id, 'operation': 'enable_update'},
            dataType: "json",
            success: function (data, status, xhr) {
                if (xhr.status === 200) {
                    loading_button.html(``);
                    var state = checkbox_enable.prop('checked');
                    checkbox_enable.prop("checked",!state);
                    checkbox_enable.prop('disabled', false);
                } else {
                    alert("镜像启用失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '镜像启用失败!';
                try {
                    msg = msg + xhr.responseJSON.code_text;
                } catch (e) {
                }
                alert(msg);
            },
            complete: function () {

            }
        });
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

     // 删除虚拟机点击事件
    $(".btn-vm-delete").click(function (e) {
        e.preventDefault();
        if(!confirm('确定删除镜像虚拟机（删除虚拟机不会删除镜像）？'))
		    return;
        let image_id = $(this).attr('data-image-id');
        let api = build_absolute_url('image/image-vm-operate/');
        let node_status = $("#vm_status_" + image_id);
        node_status.html(`删除中`);
        $.ajax({
            url: api,
            type: 'post',
            dataType: "json",
            data: {'image_id': image_id, 'operation': 'delete-vm'},
            success: function (data, status, xhr) {
                if (xhr.status === 200) {
                    get_vm_status(image_id)
                } else {
                    alert("虚拟机启动失败！" + data.code_text);
                }
                window.location = '/image/';
            },
            error: function (xhr) {
                let msg = '删除虚拟机操作失败!';
                try {
                    msg = msg + xhr.responseJSON.code_text;
                } catch (e) {
                }
                alert(msg);
                window.location = '/image/';
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

    //展开或关闭表格行
    $(".btn-row-expand-or-collapse").click(function (e) {
        let image_id = $(this).attr('data-image-id');
        let row_id = '#row_collapse_' + image_id;
        let td_selector_id = "#td_selector_" + image_id;
        let td_data_id = "#td_data_" + image_id;
        if ($(this).html().indexOf('fa-angle-right') != -1) {
            $(this).html(`<i class="fa fa-angle-down fa-lg"></i>`);
        } else {
            $(this).html(`<i class="fa fa-angle-right fa-lg"></i>`);
        }
        $(td_selector_id).toggleClass('no-col-border');
        $(td_data_id).toggleClass('no-col-border');
        $(row_id).collapse('toggle')
    });

})();

