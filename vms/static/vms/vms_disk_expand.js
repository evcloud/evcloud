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
    $('#btn-vm-disk-expand').click(function (e) {
        e.preventDefault(); // 兼容标准浏览器

        let form = $('form#id-form-vm');
        let obj_data = getForm2Obj(form);
        let expand_size = obj_data.expand_size;
        if(isNaN(expand_size) || !(/(^[1-9]\d*$)/.test(expand_size))){
            alert('请输入一个大于0的整数');
            return;
        }
        if(!confirm('确定扩容虚拟机系统盘吗？'))
            return;

        let vm_uuid = $("#id-vm-uuid").text();
        let query = encode_params({"expand-size": expand_size})
        let api = build_absolute_url('api/v3/vms/' + vm_uuid + '/sys-disk/expand/?' + query);
        let btn_submit = $(this);
        btn_submit.addClass('disabled'); //鼠标悬停时，使按钮表现为不可点击状态
        btn_submit.attr('disabled', true);//失能对应按钮
        $.ajax({
            url: api,
            type: 'post',
            contentType: 'application/json',
            success: function (data, status, xhr) {
                if (xhr.status === 200){
                    alert('扩容虚拟机系统盘成功');
                }else{
                    alert("扩容虚拟机系统盘失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '扩容虚拟机系统盘失败!';
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

    $('#id-input-expand-size').on('input propertychange', on_change_expand_size)
    function on_change_expand_size(e) {
        e.preventDefault(); // 兼容标准浏览器
        let disk_size = $('#id-vm-sys-disk-size').attr('data-sys-disk-size');
        let node_after_expand = $('#id-expand-after-size');
        let expand_size = $(this).val();
        if(isNaN(expand_size) || !(/(^[1-9]\d*$)/.test(expand_size))){
            expand_size = 0
        }
        let after_size = Number(disk_size) + Number(expand_size);
        node_after_expand.text(after_size);
    }

})();
