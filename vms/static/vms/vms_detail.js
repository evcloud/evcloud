;(function () {

    //
    // 页面刷新时执行
    window.onload = function() {
        $("#nav_vm_list").addClass("active");
        get_vm_status();// 虚拟机运行状态查询更新
    };

    // 虚拟机运行状态api构建
    function build_vm_status_api(vm_uuid){
        let url = 'api/v3/vms/' + vm_uuid + '/status/';
        return build_absolute_url(url);
    }

    // 虚拟机vnc api构建
    function build_vm_vnc_api(vm_uuid){
        let url = 'api/v3/vms/' + vm_uuid + '/vnc/';
        return build_absolute_url(url);
    }

    // 获取并设置虚拟机的运行状态
    function get_vm_status() {
        let vmid = $("#id-vm-uuid").text();
        let api = build_vm_status_api(vmid);
        let node_status = $("#vm_status_" + vmid);
        node_status.html(`<img src="/static/images/loading34.gif" width="43px"/>`);
        $.ajax({
            url: api,
            type: 'get',
            cache:false,
            success: function(data) {
                node_status.html("<span class='label label-" + VM_STATUS_LABEL[data.status.status_code] + "'>" + VM_STATUS_CN[data.status.status_code] + "</span>");
            },
        });
    }

    // 获取虚拟机vnc url
    function get_vm_vnc_url(vm_uuid){
        let api = build_vm_vnc_api(vm_uuid);
        $.ajax({
            url: api,
            type: 'post',
            success: function (data, status_text) {
                let vnc = data.vnc.url;
                window.open(vnc, '_blank');
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '打开vnc失败';
                if (data.hasOwnProperty('code_text')){
                    msg = '打开vnc失败,' + data.code_text;
                }
                alert(msg);
            }
        });
    }

    // 打开vnc点击事件
    $(".btn-vnc-open").click(function (e) {
        e.preventDefault();
        let vm_uuid = $(this).attr('data-vm-uuid');
        get_vm_vnc_url(vm_uuid);
    });

    // 刷新虚拟机状态点击事件
    $(".btn-update-vm-status").click(function (e) {
        e.preventDefault();
        get_vm_status();
    });

    //卸载硬盘
    $('.btn-disk-umount').click(function (e) {
        e.preventDefault();
        if(!confirm("确定要卸载此硬盘吗？")){
            return
        }
        let disk_uuid = $(this).attr('data-disk-uuid');
        $.ajax({
			url: build_absolute_url('/api/v3/vdisk/' + disk_uuid + '/umount/'),
			type: 'patch',
            success: function (data, status_text) {
			    $("#tr_" + disk_uuid).remove();
                alert('已成功卸载硬盘');
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '卸载硬盘失败' + msg;
                if (data.hasOwnProperty('code_text')){
                    msg = data.code_text;
                }
                alert(msg);
            }
		});
    });

    // 启动虚拟机点击事件
    $(".btn-vm-start").click(function (e) {
        e.preventDefault();

        let vm_uuid = $(this).attr('data-vm-uuid');
        let node_vm_task = $("#vm_task_" + vm_uuid);
        start_vm_ajax(vm_uuid, function () {
            node_vm_task.html(VM_TASK_CN["start"]);
        }, function () {
            node_vm_task.html("");
            get_vm_status();
        });
    });

    // 重启虚拟机点击事件
    $(".btn-vm-reboot").click(function (e) {
        e.preventDefault();
        if(!confirm('确定重启虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        let node_vm_task = $("#vm_task_" + vm_uuid);
        reboot_vm_ajax(vm_uuid, function () {
            node_vm_task.html(VM_TASK_CN["reboot"]);
        }, function () {
            node_vm_task.html("");
            get_vm_status();
        });
    });

    // 关机虚拟机点击事件
    $(".btn-vm-shutdown").click(function (e) {
        e.preventDefault();

        if(!confirm('确定关闭虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        let node_vm_task = $("#vm_task_" + vm_uuid);
        shutdown_vm_ajax(vm_uuid, function () {
            node_vm_task.html(VM_TASK_CN["shutdown"]);
        }, function () {
            node_vm_task.html("");
            get_vm_status();
        });
    });

    // 强制断电虚拟机点击事件
    $(".btn-vm-poweroff").click(function (e) {
        e.preventDefault();

        if(!confirm('确定强制断电虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        let node_vm_task = $("#vm_task_" + vm_uuid);
        poweroff_vm_ajax(vm_uuid, function () {
            node_vm_task.html(VM_TASK_CN["poweroff"]);
        }, function () {
            node_vm_task.html("");
            get_vm_status();
        });
    });

    function delete_vm(vm_uuid, op){
        let node_vm_task = $("#vm_task_" + vm_uuid);
        delete_vm_ajax(vm_uuid, op,
            function () {
                node_vm_task.html(VM_TASK_CN[op]);
            },
            function () {
                alert('已成功删除云主机');
                let url = $("#id-vm-list-url").attr('href');
                if (url)
                    location.href = url;
            },
            function () {
                node_vm_task.html("");
                get_vm_status();
            }
        );
    }

    // 删除虚拟机点击事件
    $(".btn-vm-delete").click(function (e) {
        e.preventDefault();

        if(!confirm('确定删除虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        delete_vm(vm_uuid, 'delete');
    });

    // 强制删除虚拟机点击事件
    $(".btn-vm-delete-force").click(function (e) {
        e.preventDefault();

        if(!confirm('确定强制删除虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        delete_vm(vm_uuid, 'delete_force');
    });

})();