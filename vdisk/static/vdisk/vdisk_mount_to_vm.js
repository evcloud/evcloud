;(function () {

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
        9: '宿主机连接失败',  //宿主机连接失败
        10: '云主机丢失'  //虚拟机丢失
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
            10: 'default'
    };

    //API域名
    let DOMAIN_NAME = get_domain_url();
    let API_VERSION = 'v3';

    // 获取API域名
    function get_api_domain_name(){
        return DOMAIN_NAME;
    }

    // 构建带域名url
    function build_absolute_url(url){
        let domain = get_api_domain_name();
        domain = domain.rightStrip('/');
        if(!url.startsWith('/'))
            url = '/' + url;
        return domain + url;
    }

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

        // 虚拟机操作api构建
    function build_vm_operations_api(vm_uuid){
        let url = 'api/v3/vms/' + vm_uuid + '/operations/';
        return build_absolute_url(url);
    }

    // 虚拟机运行状态api构建
    function build_vm_status_api(vm_uuid){
        let url = 'api/v3/vms/' + vm_uuid + '/status/';
        return build_absolute_url(url);
    }

    // 关机虚拟机
    function shutdown_vm(vm_uuid){
        let api = build_vm_operations_api(vm_uuid);
        $.ajax({
            url: api,
            type: 'patch',
            data: {
                'op': 'shutdown',
            },
            success: function (data, status_text) {
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '虚拟机关机失败,';
                if (data.hasOwnProperty('code_text')){
                    msg = '虚拟机关机失败,' + data.code_text;
                }
                alert(msg);
            },
            complete:function (xhr, ts) {
                let api = build_vm_status_api(vm_uuid);
                get_vm_status(api, vm_uuid);
            }
        });
    }

    // 关机虚拟机点击事件
    $(".btn-vm-shutdown").click(function (e) {
        e.preventDefault();

        if(!confirm('确定关闭虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        shutdown_vm(vm_uuid);
    });

    // 强制断电虚拟机
    function poweroff_vm(vm_uuid){
        let api = build_vm_operations_api(vm_uuid);
        $.ajax({
            url: api,
            type: 'patch',
            data: {
                'op': 'poweroff',
            },
            success: function (data, status_text) {
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '强制断电失败,';
                if (data.hasOwnProperty('code_text')){
                    msg = '强制断电失败,' + data.code_text;
                }
                alert(msg);
            },
            complete:function (xhr, ts) {
                let api = build_vm_status_api(vm_uuid);
                get_vm_status(api, vm_uuid);
            }
        });
    }

    // 强制断电虚拟机点击事件
    $(".btn-vm-poweroff").click(function (e) {
        e.preventDefault();

        if(!confirm('确定强制断电虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        poweroff_vm(vm_uuid);
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