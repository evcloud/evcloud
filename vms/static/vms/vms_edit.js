;(function () {
    //
    // 页面刷新时执行
    window.onload = function() {
        $("#nav_vm_list").addClass("active");
    };

    // 校验虚拟机参数
    function valid_vm_edit_data(obj){
        if(!obj.flavor_id || obj.flavor_id <= 0){
            alert('请选择新的配置样式');
            return false;
        }
        return true;
    }

    // 修改虚拟机表单提交按钮点击事件
    $('form#id-form-vm-edit button[type="submit"]').click(function (e) {
        let event = e || window.event;
        event.preventDefault(); // 兼容标准浏览器
        window.event.returnValue = false; // 兼容IE6~8

        let form = $('form#id-form-vm-edit');
        let obj_data = getForm2Obj(form);
        if (!valid_vm_edit_data(obj_data)){
            return;
        }
        if(!confirm('确定修改虚拟机？'))
            return;

        let vm_uuid = $('#id-edit-vm-uuid').text();
        let api = build_absolute_url('api/v3/vms/'+ vm_uuid + '/');
        let json_data = JSON.stringify(obj_data);
        let btn_submit = $(this);
        btn_submit.addClass('disabled'); //鼠标悬停时，使按钮表现为不可点击状态
        btn_submit.attr('disabled', true);//失能对应按钮
        $.ajax({
            url: api,
            type: 'patch',
            data: json_data,
            contentType: 'application/json',
            success: function (data, status, xhr) {
                if (xhr.status === 200){
                    alert('修改成功');
                    location.reload();
                }else{
                    alert("创建失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '修改主机失败!';
                try{
                    msg = msg + xhr.responseJSON.code_text;
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