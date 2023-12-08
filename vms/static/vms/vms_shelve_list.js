;(function () {
    // 搁置虚拟机点击事件
    $(".btn-vm-shelve").click(function (e) {
        e.preventDefault();

        if (!confirm('确定搁置虚拟机？'))
            return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        shelve_vm_ajax(vm_uuid, function () {
            },
            function () {

                let node_vm_task = $("#vm_task_" + vm_uuid);
                node_vm_task.parents('tr').remove();
            });
    });

    // 删除搁置虚拟机
    $(".btn-vm-delshelve").click(function (e) {
        e.preventDefault();

        if (!confirm('确定删除搁置虚拟机？'))
            return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        delshelve_vm_ajax(vm_uuid, function () {
            },
            function () {
                let node_vm_task = $("#tr_" + vm_uuid);
                node_vm_task.remove();
            });
    });

    // 校验创建虚拟机参数
    function valid_vm_unshelve_data(obj) {
        if ((obj.group_id <= 0) && (obj.host_id <= 0)) {
            alert('机组和宿主机至少选择其一');
            return false;
        }
        if ((obj.group_id <= 0)) {
            delete obj.group_id;
        }
        if ((obj.host_id <= 0)) {
            delete obj.host_id;
        }
        if (!obj.vlan_id || obj.vlan_id <= 0) {
            delete obj.vlan_id;
        }

        return true;
    }

    // 恢复虚拟机表单提交按钮点击事件
    $('#unshelve_submit').click(function (e) {
        e.preventDefault(); // 兼容标准浏览器
        let vm_uuid = $(this).attr('data-vm-uuid');
        let form = $('form#id-form-vm-unshelve');
        let obj_data = getForm2Obj(form);
        if (!valid_vm_unshelve_data(obj_data)) {
            return;
        }
        if (!confirm('确定恢复虚拟机？'))
            return;

        let api = build_vm_unshelve_api(vm_uuid);
        // let json_data = JSON.stringify(obj_data);
        let btn_submit = $(this);
        btn_submit.addClass('disabled'); //鼠标悬停时，使按钮表现为不可点击状态
        btn_submit.attr('disabled', true);//失能对应按钮

        let mac_ip_id = get_select_mac_ip()

        let params = {'group_id': obj_data.group_id, 'host_id': obj_data.host_id, 'mac_ip_id': mac_ip_id}
        let qs = encode_params(params)
        $.ajax({
            url: api + '?' + qs,
            type: 'post',
            // data: json_data,
            contentType: 'application/json',
            success: function (data, status, xhr) {
                if (xhr.status === 201) {
                    if (confirm('恢复成功,是否去主机列表看看？')) {
                        window.location = '/vms/';
                    }
                } else {
                    alert("恢复失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '恢复主机失败!';
                try {
                    msg = msg + xhr.responseJSON.code_text;
                } catch (e) {
                }
                alert(msg);
            },
            complete: function () {
                btn_submit.removeClass('disabled');   //鼠标悬停时，使按钮表现为可点击状态
                btn_submit.attr('disabled', false); //激活对应按钮
            }
        })
    });
})();

// 虚拟机搁置api
function build_vm_shelve_api(vm_uuid) {
    let url = 'api/v3/vms/' + vm_uuid + '/shelve/';
    return build_absolute_url(url);
}

// 虚拟机搁置恢复api
function build_vm_unshelve_api(vm_uuid) {
    let url = 'api/v3/vms/' + vm_uuid + '/unshelve/';
    return build_absolute_url(url);
}

// 虚拟机搁置删除api
function build_vm_delshelve_api(vm_uuid) {
    let url = 'api/v3/vms/' + vm_uuid + '/delshelve/';
    return build_absolute_url(url);
}

function get_select_mac_ip() {
    let mac = document.getElementById('id-ipv4');
    let index = mac.selectedIndex
    if (index === 0) {
        return
    }
    return mac.options[index].title
}


// 搁置虚拟机
function shelve_vm_ajax(vm_uuid, before_func, success_func, complate_func) {
    let api = build_vm_shelve_api(vm_uuid);
    if (typeof (before_func) === "function") {
        before_func();
    }
    $.ajax({
        url: api,
        type: 'post',
        success: function (data, status_text) {
            if (typeof (success_func) === "function") {
                success_func();
            }
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, '虚拟机搁置失败;');
            alert(msg);
        },
        complete: function (xhr, ts) {
            if (typeof (complate_func) === "function") {
                complate_func();
            }
        }
    });
}


// 删除搁置虚拟机
function delshelve_vm_ajax(vm_uuid, before_func, success_func, complate_func) {
    let api = build_vm_delshelve_api(vm_uuid);
    if (typeof (before_func) === "function") {
        before_func();
    }
    $.ajax({
        url: api,
        type: 'delete',
        success: function (data, status_text) {
            if (typeof (success_func) === "function") {
                success_func();
            }
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, '搁置虚拟机删除失败;');
            alert(msg);
        },
        complete: function (xhr, ts) {
            if (typeof (complate_func) === "function") {
                complate_func();
            }
        }
    });
}