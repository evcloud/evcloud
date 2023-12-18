;(function () {
    // 虚拟机附加点击事件
    $(".btn-vm-attach-ip").click(function (e) {
        e.preventDefault();

        if (!confirm(gettext('确定为虚拟机附加此IP？')))
            return;

        let mac_id = $(this).attr('data-attach-ip-id');
        let vm_uuid = $(this).attr('data-vm-uuid');
        console.log(mac_id);
        console.log(vm_uuid);
        vm_attach_ip(vm_uuid, mac_id)
    });

    $(".btn-vm-detach-ip").click(function (e) {
        e.preventDefault();

        if (!confirm(gettext('确定为虚拟机移除此IP？')))
            return;

        let mac_id = $(this).attr('data-detach-ip-id');
        let vm_uuid = $(this).attr('data-vm-uuid');
        vm_detach_ip(vm_uuid, mac_id)
    });


})();


// 虚拟机附加IP api
function build_vm_attach_api(vm_uuid) {
    let url = 'api/v3/vms/' + vm_uuid + '/attach/';
    return build_absolute_url(url);
}

// 虚拟机分离IP api
function build_vm_detach_api(vm_uuid) {
    let url = 'api/v3/vms/' + vm_uuid + '/detach/';
    return build_absolute_url(url);
}

// 虚拟机附加ip
function vm_attach_ip(vm_uuid, mac_id) {
    let api = build_vm_attach_api(vm_uuid);
    let params = {'ip_id': mac_id}
    let qs = encode_params(params)
    $.ajax({
        url: api + '?' + qs,
        type: 'post',
        success: function (data, status_text) {
            alert(gettext('已成功附加到虚拟机'));
            window.location = '/vms/';
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, gettext('虚拟机附加IP失败;'));
            alert(msg);
        },
    });
}


// 虚拟机分离ip
function vm_detach_ip(vm_uuid, mac_id) {
    let api = build_vm_detach_api(vm_uuid);
    let params = {'ip_id': mac_id}
    let qs = encode_params(params)
    $.ajax({
        url: api + '?' + qs,
        type: 'post',
        success: function (data, status_text) {
            alert(gettext('已成功从虚拟机移除'));
            window.location.reload();
        },
        error: function (xhr, msg, err) {
            msg = get_err_msg_or_default(xhr, gettext('虚拟机移除IP失败;'));
            alert(msg);
        },
    });
}