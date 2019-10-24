;(function () {

    var VM_TASK_CN = {
        'start': '启动',
        'reboot': '重启',
        'shutdown': '关闭',
        'poweroff': '关闭电源',
        'delete': '删除',
        'reset': '重置',
        'delete_force': '强制删除'
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

    /**
     * 去除字符串前后给定字符，不改变原字符串
     * @param char
     * @returns { String }
     */
    String.prototype.strip = function (char) {
      if (char){
        return this.replace(new RegExp('^\\'+char+'+|\\'+char+'+$', 'g'), '');
      }
      return this.replace(/^\s+|\s+$/g, '');
    };

    //返回一个去除右边的给定字符的字符串，不改变原字符串
    String.prototype.rightStrip = function(searchValue){
        if(this.endsWith(searchValue)){
            return this.substring(0, this.lastIndexOf(searchValue));
        }
        return this;
    };

    //返回一个去除左边的给定字符的字符串，不改变原字符串
    String.prototype.leftStrip = function(searchValue){
        if(this.startsWith(searchValue)){
            return this.replace(searchValue);
        }
        return this;
    };

    //
    // 从当前url中获取域名
    // 如http://abc.com/
    function get_domain_url() {
        let origin = window.location.origin;
        origin = origin.rightStrip('/');
        return origin + '/';
    }

    //API域名
    let DOMAIN_NAME = get_domain_url(); //'http://10.0.86.213:8000/';

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

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    //
    //所有ajax的请求的全局设置
    //
    $.ajaxSettings.beforeSend = function(xhr, settings){
        var csrftoken = getCookie('csrftoken');
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    };

    $('.edit_vm_remark').click(function (e) {
        e.preventDefault();

        vm_uuid = $(this).attr('vm_uuid');
        let div_show = $(this).parent();
        div_show.hide();
		div_show.next().show();
    });

    $('.save_vm_remark').click(function (e) {
        e.preventDefault();
        let vm_uuid = $(this).attr('vm_uuid');
        let dom_remark = $(this).prev();
        let remark = dom_remark.val();
        let div_edit = dom_remark.parent();
        let div_show = div_edit.prev();

        $.ajax({
			url: '/api/v3/vms/' + vm_uuid + '/remark/?remark='+ remark,
			type: 'patch',
			success:function(data){
			    div_show.children("span:first").text(remark);
			},
            error: function(e){
			    alert('修改失败');
            },
			complete:function() {
				div_show.show();
				div_edit.hide();
			}
		});

    });

    //
    // 全选/全不选
    //
    $(":checkbox[data-check-target]").on('click', function () {
        let target = $(this).attr('data-check-target');
        if ($(this).prop('checked')) {
            $(target).prop('checked', true); // 全选
            $(target).parents('tr').addClass('danger'); // 选中时添加 背景色类
        } else {
            $(target).prop('checked', false); // 全不选
            $(target).parents('tr').removeClass('danger');// 不选中时移除 背景色类
        }
    });

    //
    // 表格中每一行单选checkbox
    //
    $(".item-checkbox").on('click', function () {
        if ($(this).prop('checked')){
            $(this).parents('tr').addClass('danger');
        }else{
            $(this).parents('tr').removeClass('danger');
        }
    });

    // 有多少虚拟机被选中
    function get_checked_vm_count() {
        return $(".item-checkbox:checked").size()
    }

    //
    // 检测是否有选中项
    //
    function is_exists_checked() {
        return get_checked_vm_count() !== 0
    }

    //
    // 获取所有的当前选中的虚拟机的uuid数组
    //
    function get_checked_vm_uuid_array() {
        var arr = [];
        let bucket_list_checked = $(".table-vm-list :checkbox:checked.item-checkbox");
        bucket_list_checked.each(function (i) {
            arr.push($(this).val());
        });

        return arr;
    }

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

    // 虚拟机列表运行状态查询更新
    update_vms_status(get_vm_list_uuid_array());

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

    // 启动虚拟机
    function start_vm(vm_uuid){
        let api = build_vm_operations_api(vm_uuid);
        let node_vm_task = $("#vm_task_" + vm_uuid);
        node_vm_task.html(VM_TASK_CN["start"]);
        $.ajax({
            url: api,
            type: 'patch',
            data: {
                'op': 'start',
            },
            success: function (data, status_text) {
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '启动虚拟机失败,';
                if (data.hasOwnProperty('code_text')){
                    msg = '启动虚拟机失败,' + data.code_text;
                }
                alert(msg);
            },
            complete:function (xhr, ts) {
                let api = build_vm_status_api(vm_uuid);
                get_vm_status(api, vm_uuid);
			    node_vm_task.html("");
            }
        });
    }

    // 启动虚拟机点击事件
    $(".btn-vm-start").click(function (e) {
        e.preventDefault();

        let vm_uuid = $(this).attr('data-vm-uuid');
        start_vm(vm_uuid);
    });

    // 重启虚拟机
    function reboot_vm(vm_uuid){
        let api = build_vm_operations_api(vm_uuid);
        let node_vm_task = $("#vm_task_" + vm_uuid);
        node_vm_task.html(VM_TASK_CN["reboot"]);
        $.ajax({
            url: api,
            type: 'patch',
            data: {
                'op': 'reboot',
            },
            success: function (data, status_text) {
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '重启虚拟机失败,';
                if (data.hasOwnProperty('code_text')){
                    msg = '重启虚拟机失败,' + data.code_text;
                }
                alert(msg);
            },
            complete:function (xhr, ts) {
                let api = build_vm_status_api(vm_uuid);
                get_vm_status(api, vm_uuid);
			    node_vm_task.html("");
            }
        });
    }

    // 重启虚拟机点击事件
    $(".btn-vm-reboot").click(function (e) {
        e.preventDefault();
        if(!confirm('确定重启虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        reboot_vm(vm_uuid);
    });

    // 关机虚拟机
    function shutdown_vm(vm_uuid){
        let api = build_vm_operations_api(vm_uuid);
        let node_vm_task = $("#vm_task_" + vm_uuid);
        node_vm_task.html(VM_TASK_CN["shutdown"]);
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
			    node_vm_task.html("");
            }
        });
    }

    // 关机虚拟机点击事件
    $(".btn_vm_shutdown").click(function (e) {
        e.preventDefault();

        if(!confirm('确定关闭虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        shutdown_vm(vm_uuid);
    });


    // 强制断电虚拟机
    function poweroff_vm(vm_uuid){
        let api = build_vm_operations_api(vm_uuid);
        let node_vm_task = $("#vm_task_" + vm_uuid);
        node_vm_task.html(VM_TASK_CN["poweroff"]);
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
			    node_vm_task.html("");
            }
        });
    }

    // 强制断电虚拟机点击事件
    $(".btn_vm_poweroff").click(function (e) {
        e.preventDefault();

        if(!confirm('确定强制断电虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        poweroff_vm(vm_uuid);
    });

    // 删除虚拟机
    function delete_vm(vm_uuid, op='delete'){
        let api = build_vm_operations_api(vm_uuid);
        let node_vm_task = $("#vm_task_" + vm_uuid);
        node_vm_task.html(VM_TASK_CN[op]);

        $.ajax({
            url: api,
            type: 'patch',
            data: {
                'op': op,
            },
            success: function (data, status_text) {
                node_vm_task.parents('tr').remove();
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '删除虚拟机失败,';
                if (data.hasOwnProperty('code_text')){
                    msg = '删除虚拟机失败,' + data.code_text;
                }
                alert(msg);
                let api = build_vm_status_api(vm_uuid);
                get_vm_status(api, vm_uuid);
			    node_vm_task.html("");
            }
        });
    }

    // 删除虚拟机点击事件
    $(".btn_vm_delete").click(function (e) {
        e.preventDefault();

        if(!confirm('确定删除虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        delete_vm(vm_uuid, 'delete');
    });

    // 强制删除虚拟机点击事件
    $(".btn_vm_delete_force").click(function (e) {
        e.preventDefault();

        if(!confirm('确定强制删除虚拟机？'))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        delete_vm(vm_uuid, 'delete_force');
    });


    $('select[name="center"]').change(function () {
        $('select[name="group"]').val('');
        $('select[name="host"]').val('');
        this.form.submit();
    });

    $('select[name="group"]').change(function () {
        $('select[name="host"]').val('');
        this.form.submit();
    });

    $('select[name="host"]').change(function () {
        this.form.submit();
    });

    $('select[name="user"]').change(function () {
        this.form.submit();
    });

    // 批量启动选中的所有虚拟机
    $("#id-btn-batch-vm-start").click(function (e) {
        e.preventDefault();
        if(!is_exists_checked())
            return;
        if(!confirm('确定启动所有选中的虚拟机？'))
		    return;

        let vm_uuids = get_checked_vm_uuid_array();
        for (let i in vm_uuids){
            start_vm(vm_uuids[i]);
        }
    });

    // 批量关机选中的所有虚拟机
    $("#id-btn-batch-vm-shutdown").click(function (e) {
        e.preventDefault();
        if(!is_exists_checked())
            return;
        if(!confirm('确定关闭所有选中的虚拟机？'))
		    return;

        let vm_uuids = get_checked_vm_uuid_array();
        for (let i in vm_uuids){
            shutdown_vm(vm_uuids[i]);
        }
    });

    // 批量断电选中的所有虚拟机
    $("#id-btn-batch-vm-poweroff").click(function (e) {
        e.preventDefault();
        if(!is_exists_checked())
            return;
        if(!confirm('确定强制断电所有选中的虚拟机？'))
		    return;

        let vm_uuids = get_checked_vm_uuid_array();
        for (let i in vm_uuids){
            poweroff_vm(vm_uuids[i]);
        }
    });

    // 批量删除选中的所有虚拟机
    $("#id-btn-batch-vm-delete").click(function (e) {
        e.preventDefault();
        if(!is_exists_checked())
            return;
        if(!confirm('确定删除所有选中的虚拟机？'))
		    return;

        let vm_uuids = get_checked_vm_uuid_array();
        for (let i in vm_uuids){
            delete_vm(vm_uuids[i], 'delete');
        }
    });

    // 批量删除选中的所有虚拟机
    $("#id-btn-batch-vm-delete-force").click(function (e) {
        e.preventDefault();
        if(!is_exists_checked())
            return;
        if(!confirm('确定强制删除所有选中的虚拟机？'))
		    return;

        let vm_uuids = get_checked_vm_uuid_array();
        for (let i in vm_uuids){
            delete_vm(vm_uuids[i], 'delete_force');
        }
    });

})();