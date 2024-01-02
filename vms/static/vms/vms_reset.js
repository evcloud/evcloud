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
    $('#btn-vm-reset').click(function (e) {
        let event = e || window.event;
        event.preventDefault(); // 兼容标准浏览器
        window.event.returnValue = false; // 兼容IE6~8

        let form = $('form#id-form-vm-reset');
        let obj_data = getForm2Obj(form);
        let image_id = obj_data.image_id;
        if(!image_id || image_id <= 0){
            alert(gettext('请选择一个系统镜像'));
            return;
        }
        if(!confirm(gettext('确定重置虚拟机系统？')))
            return;

        let vm_uuid = $("#id-vm-uuid").text();
        let api = build_absolute_url('api/v3/vms/' + vm_uuid + '/reset/' + image_id + '/');
        let btn_submit = $(this);
        btn_submit.addClass('disabled'); //鼠标悬停时，使按钮表现为不可点击状态
        btn_submit.attr('disabled', true);//失能对应按钮
        $.ajax({
            url: api,
            type: 'post',
            contentType: 'application/json',
            success: function (data, status, xhr) {
                if (xhr.status === 201){
                    alert(gettext('重置系统镜像成功'));
                }else{
                    alert(gettext("创重置系统镜像失败！") + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = gettext('创重置系统镜像失败!');
                try{
                    msg = xhr.responseJSON.code_text;
                }catch (e) {}
                alert(msg);
            },
            complete: function () {
                btn_submit.removeClass('disabled');   //鼠标悬停时，使按钮表现为可点击状态
                btn_submit.attr('disabled', false); //激活对应按钮
            }
        })
    });
})();
