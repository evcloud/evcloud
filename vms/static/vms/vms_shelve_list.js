;(function () {
    // 搁置虚拟机点击事件
    $(".btn-vm-shelve").click(function (e) {
        e.preventDefault();

        if(!confirm('确定搁置虚拟机？'))
            return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        shelve_vm_ajax(vm_uuid, function () {
            },
            function () {
                let node_vm_task = $("#vm_task_" + vm_uuid);
                    node_vm_task.parents('tr').remove();
            });
    });


    // 恢复搁置虚拟机点击事件
    $(".btn-vm-unshelve").click(function (e) {
        e.preventDefault();

        if (!confirm('确定恢复虚拟机？'))
            return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        let mac_ip_id = $(this).attr('data-ip-id');

        unshelve_vm_ajax(vm_uuid, mac_ip_id,function () {
            },
            function () {
                // node_vm_task.parents('tr').remove();
                alert("虚拟机已恢复")
                setTimeout(() => window.location.href = '/', 3000)
            });
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

// 恢复搁置虚拟机
function unshelve_vm_ajax(vm_uuid, mac_ip_id, before_func, success_func, complate_func) {
    let api = build_vm_unshelve_api(vm_uuid);
    if (typeof (before_func) === "function") {
        before_func();
    }

    $.ajax({
        url: api + '?mac_ip_id=' +  mac_ip_id,
        type: 'post',
        success: function (data, status_text) {
            if (typeof (success_func) === "function") {
                success_func();
            }
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, '虚拟机恢复失败;');
            alert(msg);
        },
        complete: function (xhr, ts) {
            if (typeof (complate_func) === "function") {
                complate_func();
            }
        }
    });
}