;(function () {

    let API_VERSION = 'v3';

    //
    // 页面刷新时执行
    window.onload = function() {
        $("#nav_vdisk_list").addClass("active");// 激活云硬盘列表导航栏
        // 虚拟机列表运行状态查询更新
        update_vms_status(get_vm_list_uuid_array());
    };

    //
    // 获取table中所有的虚拟机的uuid数组
    //
    function get_vm_list_uuid_array() {
        var arr = [];
        let bucket_list_checked = $(".table-vm-list :checkbox.item-checkbox");
        bucket_list_checked.each(function (i) {
            arr.push($(this).val());
        });

        return arr;
    }

    // 获取并设置虚拟机的运行状态
    function get_vm_status(url, vmid) {
        let node_status = $("#vm_status_" + vmid);
        node_status.html(`<img src="/static/images/loading34.gif" width="43px"/>`);
        $.ajax({
            url: url,
            type: 'get',
            cache:false,
            success: function(data) {
                node_status.html("<span class='label label-" + VM_STATUS_LABEL[data.status.status_code] + "'>" + VM_STATUS_CN[data.status.status_code] + "</span>");
            },
        });
    }

    function update_vms_status(vmids){
        for(let i in vmids) {
            let api = build_vm_status_api(vmids[i]);
            get_vm_status(api, vmids[i]);
        }
    }

    // 刷新虚拟机状态点击事件
    $(".btn-update-vm-status").click(function (e) {
        e.preventDefault();
        update_vms_status(get_vm_list_uuid_array());
    });

    // 虚拟机运行状态api构建
    function build_vm_status_api(vm_uuid){
        let url = 'api/' + API_VERSION + '/vms/' + vm_uuid + '/status/';
        return build_absolute_url(url);
    }

    // 关机虚拟机点击事件
    $(".btn-vm-shutdown").click(function (e) {
        e.preventDefault();

        if(!confirm('确定关闭虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        shutdown_vm_ajax(vm_uuid, null, function () {
            let api = build_vm_status_api(vm_uuid);
            get_vm_status(api, vm_uuid);
        });
    });


    // 强制断电虚拟机点击事件
    $(".btn-vm-poweroff").click(function (e) {
        e.preventDefault();

        if(!confirm('确定强制断电虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        poweroff_vm_ajax(vm_uuid, null, function () {
            let api = build_vm_status_api(vm_uuid);
            get_vm_status(api, vm_uuid);
        });
    });

    // 挂载硬盘
    $(".btn-disk-mount").click(function (e) {
        e.preventDefault();

        if(!confirm("确定挂载到此云主机吗？"))
            return;

        let disk_uuid = $("#id-mount-disk-uuid").text();
        let vm_uuid = $(this).attr("data-vm-uuid");
        let api = build_absolute_url('api/' + API_VERSION + '/vdisk/' + disk_uuid + '/mount/?vm_uuid=' + vm_uuid);
        $.ajax({
            url: api,
            type: 'patch',
            success: function (data, status_text) {
                $("#tr_" + disk_uuid).remove();
                alert('已成功挂载硬盘');
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '挂载硬盘失败';
                if (data && data.hasOwnProperty('code_text')){
                    msg = data.code_text;
                }
                alert(msg);
            }
        });
    });

})();