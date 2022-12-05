;'use strict';
(function () {

    //
    // 页面刷新时执行
    window.onload = function() {
        nav_active_display();
    };

    // 激活虚拟机列表导航栏
    function nav_active_display() {
        $("#nav_vm_list").addClass("active");
    }

    // 表单提交按钮点击事件
    $('#btn-vm-migrate').click(function (e) {
        let event = e || window.event;
        event.preventDefault(); // 兼容标准浏览器
        window.event.returnValue = false; // 兼容IE6~8

        let form = $('form#id-form-vm-migrate');
        let obj_data = getForm2Obj(form);
        let host_id = obj_data.host_id;
        if(!host_id || host_id <= 0){
            alert('请选择迁移的目标宿主机');
            return;
        }
        let vm_uuid = $("#id-vm-uuid").text();
        let api = build_absolute_url('api/v3/vms/' + vm_uuid + '/migrate/' + host_id + '/');
        let msg = "确定迁移云主机吗？";
        let force = obj_data.force;
        if (force === "force"){
            msg += "您已选择强制迁移";
            api += '?force=true'
        }
        if(!confirm(msg))
            return;

        let btn_submit = $(this);
        btn_submit.addClass('disabled'); //鼠标悬停时，使按钮表现为不可点击状态
        btn_submit.attr('disabled', true);//失能对应按钮
        let loading = new KZ_Loading('虚拟机关机迁移中...');
        loading.show();
        $.ajax({
            url: api,
            type: 'post',
            contentType: 'application/json',
            success: function (data, status, xhr) {
                loading.destroy();
                if (xhr.status === 201){
                    alert('云主机迁移成功');
                }else{
                    alert("云主机迁移失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                loading.destroy();
                let msg = '云主机迁移失败!';
                try{
                    msg = xhr.responseJSON.code_text;
                }catch (e) {}
                alert(msg);
            },
            complete: function () {
                loading.destroy();
                btn_submit.removeClass('disabled');   //鼠标悬停时，使按钮表现为可点击状态
                btn_submit.attr('disabled', false); //激活对应按钮
            }
        })
    });
})();
