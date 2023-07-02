;
var VM_TASK_CN = {
    'start': '启动',
    'reboot': '重启',
    'shutdown': '关闭',
    'poweroff': '关闭电源',
    'delete': '删除',
    'reset': '重置',
    'delete_force': '强制删除',
    'miss_fix': '丢失恢复'
};

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
    10: '未找到'  //虚拟机丢失
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
        10: 'warning'
};

// 虚拟机操作api构建
function build_vm_operations_api(vm_uuid){
    let url = 'api/v3/vms/' + vm_uuid + '/operations/';
    return build_absolute_url(url);
}

// 虚拟机系统快照创建api构建
function build_vm_snap_create_api(vm_uuid, remarks){
    let url = 'api/v3/vms/' + vm_uuid + '/snap/' + '?remark=' + remarks;
    return build_absolute_url(url);
}

function get_err_msg_or_default(xhr, default_msg) {
    msg = default_msg;
    try {
        data = xhr.responseJSON;
        if (data.hasOwnProperty('code_text')) {
            msg = default_msg + data.code_text;
        }
    }catch (e) {

    }
    return msg;
}

// 启动虚拟机
function start_vm_ajax(vm_uuid, before_func, complate_func){
    let api = build_vm_operations_api(vm_uuid);
    if(typeof(before_func) === "function"){
        before_func();
    }
    $.ajax({
        url: api,
        type: 'patch',
        data: {
            'op': 'start',
        },
        success: function (data, status_text) {
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, '启动虚拟机失败;');
            alert(msg);
        },
        complete:function (xhr, ts) {
            if(typeof(complate_func) === "function"){
                complate_func();
            }
        }
    });
}

// 重启虚拟机
function reboot_vm_ajax(vm_uuid, before_func, complate_func){
    let api = build_vm_operations_api(vm_uuid);
    if(typeof(before_func) === "function"){
        before_func();
    }
    $.ajax({
        url: api,
        type: 'patch',
        data: {
            'op': 'reboot',
        },
        success: function (data, status_text) {
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, '重启虚拟机失败;');
            alert(msg);
        },
        complete:function (xhr, ts) {
            if(typeof(complate_func) === "function"){
                complate_func();
            }
        }
    });
}

// 关机虚拟机
function shutdown_vm_ajax(vm_uuid, before_func, complate_func){
    let api = build_vm_operations_api(vm_uuid);
    if(typeof(before_func) === "function"){
        before_func();
    }
    $.ajax({
        url: api,
        type: 'patch',
        data: {
            'op': 'shutdown',
        },
        success: function (data, status_text) {
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, '虚拟机关机失败;');
            alert(msg);
        },
        complete:function (xhr, ts) {
            if(typeof(complate_func) === "function"){
                complate_func();
            }
        }
    });
}

// 强制断电虚拟机
function poweroff_vm_ajax(vm_uuid, before_func, complate_func){
    let api = build_vm_operations_api(vm_uuid);
    if(typeof(before_func) === "function"){
        before_func();
    }
    $.ajax({
        url: api,
        type: 'patch',
        data: {
            'op': 'poweroff',
        },
        success: function (data, status_text) {
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, '强制断电失败;');
            alert(msg);
        },
        complete:function (xhr, ts) {
            if(typeof(complate_func) === "function"){
                complate_func();
            }
        }
    });
}

// 删除虚拟机
function delete_vm_ajax(vm_uuid, op='delete', before_func, success_func, complate_func){
    let api = build_vm_operations_api(vm_uuid);
    if(typeof(before_func) === "function"){
        before_func();
    }
    $.ajax({
        url: api,
        type: 'patch',
        data: {
            'op': op,
        },
        success: function (data, status_text) {
            if(typeof(success_func) === "function"){
                success_func();
            }
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, '删除虚拟机失败;');
            alert(msg);
            if(typeof(complate_func) === "function"){
                complate_func();
            }
        }
    });
}


// 创建虚拟机系统快照
function create_snap_vm_ajax(vm_uuid, remarks, before_func, success_func, complate_func){
    let api = build_vm_snap_create_api(vm_uuid, remarks);
    if(typeof(before_func) === "function"){
        before_func();
    }
    $.ajax({
        url: api,
        type: 'post',
        success: function (data, status_text) {
            if(typeof(success_func) === "function"){
                success_func(data);
            }
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, '创建主机快照失败;');
            alert(msg);
        },
        complete:function (xhr, ts) {
            if(typeof(complate_func) === "function"){
                complate_func();
            }
        }
    });
}


// 虚拟机丢失恢复
function vm_miss_fix_ajax(vm_uuid, before_func, success_func, complate_func){
    let api = build_absolute_url("api/v3/vms/" + vm_uuid + '/miss-fix/');
    if(typeof(before_func) === "function"){
        before_func();
    }
    $.ajax({
        url: api,
        type: 'post',
        success: function (data, status_text) {
            if(typeof(success_func) === "function"){
                success_func(data);
            }
        },
        error: function (xhr, msg, err) {
            console.log(xhr);
            let d = xhr.responseJSON;
            if (d.hasOwnProperty('err_code')){
                if (d.err_code === 'VmNotExist'){
                    msg = '此虚拟主机不存在，无法恢复，请刷新网页后重试。'
                }else if (d.err_code === 'VmDiskImageMiss'){
                    msg = '此虚拟主机的系统盘镜像已丢失，无法恢复。'
                }else if (d.err_code === 'HostDown'){
                    msg = '宿主机可能宕机或网络问题，无法访问宿主机，可以选择等待宿主机恢复；也可以尝试迁移此虚拟主机到其他宿主机。'
                }else if(d.err_code === 'VmAlreadyExist') {
                    msg = '此虚拟主机未丢失，无需恢复。'
                }else{
                    msg = get_err_msg_or_default(xhr, '尝试恢复丢失的虚拟主机失败;');
                }
            }else{
                msg = get_err_msg_or_default(xhr, '尝试恢复丢失的虚拟主机失败;');
            }

            alert(msg);
        },
        complete:function (xhr, ts) {
            if(typeof(complate_func) === "function"){
                complate_func();
            }
        }
    });
}
