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
    $('#btn-vm-live-migrate').click(function (e) {
        e.preventDefault(); // 兼容标准浏览器
        let form = $('form#id-form-vm-live-migrate');
        let obj_data = getForm2Obj(form);
        let host_id = obj_data['host_id'];
        if(!host_id || host_id <= 0){
            alert('请选择迁移的目标宿主机');
            return;
        }
        let vm_uuid = $("#id-vm-uuid").text();
        let api = build_absolute_url('api/v3/vms/' + vm_uuid + '/live-migrate/' + host_id + '/');
        let msg = "确定迁移云主机吗？";
        if(!confirm(msg))
            return;

        let btn_submit = $(this);
        btn_submit.addClass('disabled'); //鼠标悬停时，使按钮表现为不可点击状态
        btn_submit.attr('disabled', true);//失能对应按钮
        $.ajax({
            url: api,
            type: 'post',
            contentType: 'application/json',
            success: function (data, status, xhr) {
                if (xhr.status === 202){
                    $("#id-div-migrate-status").show();
                    display_icon(true);
                    display_icon();
                    $("#id-migrate-result").text('开始迁移');
                    let task_id = data['migrate_task'];
                    window.migrate_status_timer_number = window.setInterval(function () {
                        get_vm_migrate_status(task_id, handle_vm_status_callback);
                    }, 2000);
                }else{
                    alert("云主机动态迁移请求失败！" + data['code_text']);
                }
            },
            error: function (xhr) {
                let msg = '云主机动态迁移请求失败!';
                try{
                    msg = xhr.responseJSON.code_text;
                }catch (e) {}
                alert(msg);
            },
            complete: function () {

            }
        })
    });

    function get_vm_migrate_status(task_id, callback){
        let api = build_absolute_url('api/v3/task/vm-migrate/' + task_id + '/');
        $.ajax({
			url: api,
			type: 'get',
			success: function (data, status_text, xhr) {
                if (xhr.status === 200){
                    callback(data);
                }
            },
            error: function(xhr, msg, err){
			    let data = xhr.responseJSON;
                console.log(data);
            }
		});
    }

    function handle_vm_status_callback(data){
        let dom_result = $("#id-migrate-result");
        let status = data['status']
        let text_class = 'text-dark'
        let status_display = ''
        if (status === 'failed'){
            text_class = 'text-danger';
            status_display = '迁移失败;' + data['content'];
            migrate_complete_do();
        }else if (status === 'in-process'){
            text_class = 'text-info';
            status_display = '正在迁移';
            display_icon();
        }else if (status === 'some-todo'){
            text_class = 'text-warning';
            status_display = '迁移完成，有些需要手动善后的工作;' + data['content'];
            migrate_complete_do();
        }else if (status === 'complete'){
            text_class = 'text-success';
            status_display = '迁移完成';
            migrate_complete_do();
        }

        dom_result.removeClass();
        dom_result.addClass(text_class);
        dom_result.text(status_display);
    }

    function display_icon(clear=false){
        let mod_icons = $("#id-migrate-display-icon");
        if (clear){
            mod_icons.html("");
        }else{
            mod_icons.append("<i class=\"fa fa-truck-moving\"></i>");
        }

    }
    function migrate_complete_do(){
        window.clearInterval(window.migrate_status_timer_number);
        let btn_submit = $("#btn-vm-live-migrate");
        btn_submit.removeClass('disabled');   //鼠标悬停时，使按钮表现为可点击状态
        btn_submit.attr('disabled', false); //激活对应按钮
    }
})();
