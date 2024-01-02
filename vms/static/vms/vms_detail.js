;(function () {

    //
    // 页面刷新时执行
    window.onload = function() {
        $("#nav_vm_list").addClass("active");
        get_vm_status();// 虚拟机运行状态查询更新
        vm_stats_charts();
    };

    // 虚拟机运行状态api构建
    function build_vm_status_api(vm_uuid){
        let url = 'api/v3/vms/' + vm_uuid + '/status/';
        return build_absolute_url(url);
    }

    // 虚拟机vnc api构建
    function build_vm_vnc_api(vm_uuid){
        let url = 'api/v3/vms/' + vm_uuid + '/vnc/';
        return build_absolute_url(url);
    }

    // 虚拟机snap api构建
    function build_vm_snap_api(snap_id, remarks=null){
        let url = 'api/v3/vms/snap/' + snap_id + '/';
        if (remarks){
            url = url + '?remark=' + remarks;
        }
        return build_absolute_url(url);
    }
    // 虚拟机snap备注 api构建
    function build_vm_snap_remark_api(snap_id, remarks=null){
        let url = 'api/v3/vms/snap/' + snap_id + '/remark/';
        if (remarks){
            url = url + '?remark=' + remarks;
        }
        return build_absolute_url(url);
    }

    // 虚拟机备注 api构建
    function build_vm_remarks_api(vm_uuid, remark){
        let url = '/api/v3/vms/' + vm_uuid + '/remark/?remark='+ remark;
        return build_absolute_url(url);
    }

     // 虚拟机回滚到snap api构建
    function build_vm_rollback_snap_api(vm_uuid, snap_id){
        let url = 'api/v3/vms/' + vm_uuid + '/rollback/' + snap_id + '/';
        return build_absolute_url(url);
    }

    function build_vm_stats_api(vm_uuid){
        let url = 'api/v3/vms/' + vm_uuid + '/stats/';
        return build_absolute_url(url);
    }

    function get_vm_uuid() {
        return $("#id-vm-uuid").text();
    }

    // 获取虚拟机搁置状态
    function get_vm_shelve_status() {
        return $("#vm_status_shelve").attr('title');
    }

    // 获取并设置虚拟机的运行状态
    function get_vm_status() {
        let vmid = get_vm_uuid();
        let api = build_vm_status_api(vmid);
        let node_status = $("#vm_status_" + vmid);
        node_status.html(`<i class="fa fa-spinner fa-pulse"></i>`);
        $.ajax({
            url: api,
            type: 'get',
            cache:false,
            success: function(data) {
                node_status.html('<span class="badge  badge-' + VM_STATUS_LABEL[data.status.status_code] + '">' + VM_STATUS_CN[data.status.status_code] + "</span>");
            },
            error: function (xhr) {
                node_status.html('<span class="badge  badge-danger">查询失败</span>');
            }
        });
    }

    // 获取虚拟机vnc url
    function get_vm_vnc_url(vm_uuid){
        let api = build_vm_vnc_api(vm_uuid);
        $.ajax({
            url: api,
            type: 'post',
            success: function (data, status_text) {
                let vnc = data.vnc.url;
                window.open(vnc, '_blank');
            },
            error: function (xhr, msg, err) {
                msg = gettext('打开vnc失败');
                try{
                    let data = xhr.responseJSON;
                    if (data.hasOwnProperty('code_text')){
                        msg = gettext('打开vnc失败,') + data.code_text;
                    }
                }catch (e) {}
                alert(msg);
            }
        });
    }

    // 打开vnc点击事件
    $(".btn-vnc-open").click(function (e) {
        e.preventDefault();
        let vm_uuid = $(this).attr('data-vm-uuid');
        get_vm_vnc_url(vm_uuid);
    });

    // 刷新虚拟机状态点击事件
    $(".btn-update-vm-status").click(function (e) {
        e.preventDefault();
        get_vm_status();
    });

    //卸载硬盘
    $('.btn-disk-umount').click(function (e) {
        e.preventDefault();
        if(!confirm(gettext("确定要卸载此硬盘吗？"))){
            return
        }
        let disk_uuid = $(this).attr('data-disk-uuid');
        $.ajax({
			url: build_absolute_url('/api/v3/vdisk/' + disk_uuid + '/umount/'),
			type: 'patch',
            success: function (data, status_text) {
			    $("#tr_" + disk_uuid).remove();
                alert(gettext('已成功卸载硬盘'));
            },
            error: function (xhr, msg, err) {
			    msg = gettext('卸载硬盘失败') + msg;
			    try {
                    let data = xhr.responseJSON;
                    if (data.hasOwnProperty('code_text')) {
                        msg = data.code_text;
                    }
                }catch (e) {}
                alert(msg);
            }
		});
    });

    //卸载PCI设备
    $('.btn-pci-unmount').click(function (e) {
        e.preventDefault();
        if(!confirm(gettext("确定要卸载此设备吗？"))){
            return
        }
        let pci_id = $(this).attr('data-pci-id');
        $.ajax({
			url: build_absolute_url('/api/v3/pci/' + pci_id + '/umount/'),
			type: 'post',
            success: function (data, status_text) {
			    $("#tr_" + pci_id).remove();
                alert(gettext('已成功卸载设备'));
            },
            error: function (xhr, msg, err) {
			    msg = gettext('卸载设备失败') + msg;
			    try {
                    let data = xhr.responseJSON;
                    if (data.hasOwnProperty('code_text')) {
                        msg = data.code_text;
                    }
                }catch (e) {}
                alert(msg);
            }
		});
    });

    // 启动虚拟机点击事件
    $(".btn-vm-start").click(function (e) {
        e.preventDefault();

        let vm_uuid = $(this).attr('data-vm-uuid');
        let node_vm_task = $("#vm_task_" + vm_uuid);
        start_vm_ajax(vm_uuid, function () {
            node_vm_task.html(VM_TASK_CN["start"]);
        }, function () {
            node_vm_task.html("");
            get_vm_status();
        });
    });

    // 重启虚拟机点击事件
    $(".btn-vm-reboot").click(function (e) {
        e.preventDefault();
        if(!confirm(gettext('确定重启虚拟机？')))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        let node_vm_task = $("#vm_task_" + vm_uuid);
        reboot_vm_ajax(vm_uuid, function () {
            node_vm_task.html(VM_TASK_CN["reboot"]);
        }, function () {
            node_vm_task.html("");
            get_vm_status();
        });
    });

    // 关机虚拟机点击事件
    $(".btn-vm-shutdown").click(function (e) {
        e.preventDefault();

        if(!confirm(gettext('确定关闭虚拟机？')))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        let node_vm_task = $("#vm_task_" + vm_uuid);
        shutdown_vm_ajax(vm_uuid, function () {
            node_vm_task.html(VM_TASK_CN["shutdown"]);
        }, function () {
            node_vm_task.html("");
            get_vm_status();
        });
    });

    // 强制断电虚拟机点击事件
    $(".btn-vm-poweroff").click(function (e) {
        e.preventDefault();

        if(!confirm(gettext('确定强制断电虚拟机？')))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        let node_vm_task = $("#vm_task_" + vm_uuid);
        poweroff_vm_ajax(vm_uuid, function () {
            node_vm_task.html(VM_TASK_CN["poweroff"]);
        }, function () {
            node_vm_task.html("");
            get_vm_status();
        });
    });

    function delete_vm(vm_uuid, op){
        let node_vm_task = $("#vm_task_" + vm_uuid);
        delete_vm_ajax(vm_uuid, op,
            function () {
                node_vm_task.html(VM_TASK_CN[op]);
            },
            function () {
                alert(gettext('已成功删除虚拟机'));
                let url = $("#id-vm-list-url").attr('href');
                if (url)
                    location.href = url;
            },
            function () {
                node_vm_task.html("");
                get_vm_status();
            }
        );
    }

    // 删除虚拟机点击事件
    $(".btn-vm-delete").click(function (e) {
        e.preventDefault();

        if(!confirm(gettext('确定删除虚拟机？')))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        delete_vm(vm_uuid, 'delete');
    });

    // 强制删除虚拟机点击事件
    $(".btn-vm-delete-force").click(function (e) {
        e.preventDefault();

        if(!confirm(gettext('确定强制删除虚拟机？')))
		    return;

        let vm_uuid = $(this).attr('data-vm-uuid');
        delete_vm(vm_uuid, 'delete_force');
    });

    // 虚拟机备注
    $('.edit_vm_remark').click(function (e) {
        e.preventDefault();

        let div_show = $(this).parent();
        div_show.hide();
		div_show.next().show();
    });
    // 虚拟机备注
    $('.save_vm_remark').click(function (e) {
        e.preventDefault();
        let vm_uuid = $(this).attr('vm_uuid');
        let dom_remark = $(this).prev();
        let remark = dom_remark.val();
        let div_edit = dom_remark.parent();
        let div_show = div_edit.prev();
        let api = build_vm_remarks_api(vm_uuid, remark);
        $.ajax({
			url: api,
			type: 'patch',
			success:function(data){
			    div_show.children("span:first").text(remark);
			},
            error: function(e){
			    alert(gettext('修改失败'));
            },
			complete:function() {
				div_show.show();
				div_edit.hide();
			}
		});
    });

    //art-template渲染模板注册过滤器
    template.defaults.imports.isoTimeToLocal = isoTimeToLocal;

    //
    // 创建快照渲染模板
    //
    let render_vm_snap_item = template.compile(`
        <tr id="tr_snap_{{ snap.id }}">
            <td>{{ snap.id }}</td>
            <td class="line-limit-length" style="max-width: 150px;" title="{{ snap.snap }}">{{ snap.snap }}</td>
            <td>{{ $imports.isoTimeToLocal(snap.create_time) }}</td>
            <td class="mouse-hover">
                <div>
                    <span>{{ snap.remarks }}</span>
                    <span class="mouse-hover-show edit-vm-snap-remark" title="修改备注">
                        <i class="fa fa-edit"></i>
                    </span>
                </div>
                <div style="display:none">
                    <textarea id="remarks">{{ snap.remarks }}</textarea>
                    <span class="save-vm-snap-remark" title="保存备注" data-snap-id="{{ snap.id }}">
                        <i class="fa fa-save"></i>
                    </span>
                </div>
            </td>
            <td>
                <button type="button" class="btn btn-sm btn-danger btn-vm-snap-delete"
                        data-snap-id="{{ snap.id }}">删除
                </button>
                <button type="button" class="btn btn-sm btn-danger btn-vm-snap-rollback"
                        data-snap-id="{{ snap.id }}">回滚
                </button>
            </td>
        </tr>
    `);

    // 创建虚拟机系统快照点击事件
    $(".btn-vm-snap-create").click(function (e) {
        e.preventDefault();

        if(!confirm(gettext('确定创建虚拟机系统快照吗？')))
		    return;

        let remarks = prompt(gettext('请输入快照备注信息：'));
        if (remarks === null)
            return;
        let vm_uuid = $(this).attr('data-vm-uuid');
        create_snap_vm_ajax(vm_uuid, remarks, null,
            function (data) {
                let html = render_vm_snap_item(data);
                let snap_table = $('table.table-vm-snap-list');
                if(snap_table[0]){
                    snap_table.find("tr:first").after(html);
                }else{
                    html = `<p><strong>虚拟机快照</strong></p>
                            <table class="table table-vm-snap-list" style="word-wrap:break-word;word-break:break-all;">
                            <thead class="thead-light">
                            <tr>
                                <th>ID</th>
                                <th>快照</th>
                                <th>创建时间</th>
                                <th>备注</th>
                                <th>操作</th>
                            </tr></thead><tbody>` + html + '</tbody></table>';
                    let snap_dom = $("#id-vm-snap-content");
                    snap_dom.empty();
                    snap_dom.append(html);
                }
                alert("创建快照成功");
            }
        ,null);
    });

    // 删除虚拟机系统快照
    function delete_vm_snap_ajax(snap_id, success_func){
        let api = build_vm_snap_api(snap_id);
        $.ajax({
            url: api,
            type: 'delete',
            success: function (data, status_text, xhr) {
                if (xhr.status === 204){
                    if(typeof(success_func) === "function"){
                        success_func();
                    }
                }else{
                    alert(gettext('删除快照失败'));
                }
            },
            error: function (xhr, msg, err) {
                let data = xhr.responseJSON;
                msg = gettext('删除快照失败');
                if (data.hasOwnProperty('code_text')){
                    msg = gettext('删除快照失败,') + data.code_text;
                }
                alert(msg);
            },
        });
    }

    // 删除虚拟机系统快照点击事件
    $("#id-vm-snap-content").on('click', '.btn-vm-snap-delete', function (e) {
        e.preventDefault();

        if(!confirm(gettext('确定删除此虚拟机系统快照吗？')))
		    return;

        let snap_id = $(this).attr('data-snap-id');
        let tr = $(this).parents('tr');
        delete_vm_snap_ajax(snap_id, function () {
            tr.remove();
            alert(gettext('已成功删除'));
        });
    });

    // 快照备注
    $("#id-vm-snap-content").on('click', '.edit-vm-snap-remark', function (e) {
        e.preventDefault();

        let div_show = $(this).parent();
        div_show.hide();
		div_show.next().show();
    });
    // 快照备注
    $("#id-vm-snap-content").on('click', '.save-vm-snap-remark', function (e) {
        e.preventDefault();
        let id = $(this).attr('data-snap-id');
        let dom_remark = $(this).prev();
        let remark = dom_remark.val();
        let div_edit = dom_remark.parent();
        let div_show = div_edit.prev();
        let api = build_vm_snap_remark_api(id, remark);
        $.ajax({
			url: api,
			type: 'patch',
			success:function(){
			    div_show.children("span:first").text(remark);
			},
            error: function(){
			    alert('修改失败');
            },
			complete:function() {
				div_show.show();
				div_edit.hide();
			}
		});
    });

    // 回滚虚拟机到指定快照
    $("#id-vm-snap-content").on('click', '.btn-vm-snap-rollback', function (e) {
        e.preventDefault();
        if(!confirm(gettext('确定回滚虚拟机到此快照吗？请谨慎操作。')))
		    return;

        let snap_id = $(this).attr('data-snap-id');
        let vm_uuid = get_vm_uuid();
        let api = build_vm_rollback_snap_api(vm_uuid, snap_id);
        $.ajax({
			url: api,
			type: 'post',
			success: function (data, status_text, xhr) {
                if (xhr.status === 201){
                    alert(gettext('回滚主机成功'));
                }else{
                    alert(gettext('回滚主机失败'));
                }
            },
            error: function(xhr, msg, err){
			    let data = xhr.responseJSON;
                msg = gettext('回滚主机失败');
                if (data.hasOwnProperty('code_text')){
                    msg = gettext('回滚主机失败,') + data.code_text;
                }
                alert(msg);
            }
		});
    });


    function calculate_cpu_percent(statsArray, stats){
        let timestamp = stats["timestamp"]
        let cpuTimeAbs = stats["cpu_time_abs"]
        let hostCpus = stats["host_cpus"]
        let guestCpus = stats["guest_cpus"]
        let prevCpuTime = 0
        let prevTimestamp = 0
        let l = statsArray.length
        if (l > 0){
            let preStats = statsArray[l-1]
            prevCpuTime = preStats["cpu_time_abs"]
            prevTimestamp = preStats["timestamp"]
        }
        let cpuTime = cpuTimeAbs - prevCpuTime
        let deltaTime = timestamp - prevTimestamp
        let percentBase = 0
        if (deltaTime !== 0){
            percentBase = ((cpuTime * 100.0) / (deltaTime * 1000.0 * 1000.0 * 1000.0))
        }
        let cpuHostPercent = percentBase / hostCpus
        let cpuGuestPercent = 0
        if (guestCpus > 0){
            cpuGuestPercent = percentBase / guestCpus
        }
        if (cpuGuestPercent < 0){
            cpuGuestPercent = 0
        }else if(cpuGuestPercent > 100){
            cpuGuestPercent = 100
        }

        return cpuGuestPercent
    }

    function calculate_rate(statsArray, stats, key){
        let ret = 0.0
        let l = statsArray.length
        if (l > 0) {
            let preStats = statsArray[l-1]
            let rateDiff = stats[key] - preStats[key]
            let timeDiff = stats["timestamp"] - preStats["timestamp"]
            ret = rateDiff / timeDiff
            if (ret < 0){
                ret = 0.0
            }
        }
        return ret
    }

    function handle_vm_stats_callback(stats){
        // cpu
        let cpuRate = calculate_cpu_percent(window.vm_stats_array, stats)
        window.vm_stats_chart_cpu_data.push(cpuRate);
        // mem
        let mem = stats["curr_mem_percent"]
            window.vm_stats_chart_mem_data.push(mem);

        // disk
        let diskRdRate = calculate_rate(window.vm_stats_array, stats, "disk_rd_kb")
        let diskWrRate = calculate_rate(window.vm_stats_array, stats, "disk_wr_kb")
        window.vm_stats_chart_disk_data.rd_kb.push(diskRdRate);
        window.vm_stats_chart_disk_data.wr_kb.push(diskWrRate);

        // window.vm_stats_chart_disk_data.rd_kb.push(stats["disk_rd_kb"]);
        // window.vm_stats_chart_disk_data.wr_kb.push(stats["disk_wr_kb"]);
        // net io
        let netTxRate = calculate_rate(window.vm_stats_array, stats, "net_tx_kb")
        let netRxRate = calculate_rate(window.vm_stats_array, stats, "net_rx_kb")
        window.vm_stats_chart_net_data.tx_kb.push(netTxRate);
        window.vm_stats_chart_net_data.rx_kb.push(netRxRate);

        // window.vm_stats_chart_net_data.tx_kb.push(stats["net_tx_kb"]);
        // window.vm_stats_chart_net_data.rx_kb.push(stats["net_rx_kb"]);

        window.vm_stats_array.push(stats)
        if (window.vm_stats_array.length > window.vm_stats_chart_labels.length){
            window.vm_stats_array.shift();
            window.vm_stats_chart_cpu_data.shift();
            window.vm_stats_chart_mem_data.shift();
            window.vm_stats_chart_disk_data.rd_kb.shift();
            window.vm_stats_chart_disk_data.wr_kb.shift();
            window.vm_stats_chart_net_data.tx_kb.shift();
            window.vm_stats_chart_net_data.rx_kb.shift();
        }
        window.chart_vm_cpu.update();
        window.chart_vm_mem.update();
        window.chart_vm_disk.update();
        window.chart_vm_network.update();
    }

    function get_vm_stats(callback){
        let vm_uuid = get_vm_uuid();
        let api = build_vm_stats_api(vm_uuid);
        let vm_status = get_vm_shelve_status()
        if (vm_status === 'shelve'){
            // 搁置状态
            return
        }
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

    function vm_stats_charts(){
        window.vm_stats_array = []
        window.vm_stats_chart_labels = new Array(100).fill("");

        window.vm_stats_chart_cpu_data = []
        window.vm_stats_chart_mem_data = []
        window.vm_stats_chart_disk_data = {rd_kb: [], wr_kb: []}
        window.vm_stats_chart_net_data = {tx_kb: [], rx_kb: []}
        window.setInterval(function (){
            get_vm_stats(handle_vm_stats_callback);
        },2000);

        let ctx_chart_vm_cpu = document.getElementById('chart-vm-cpu').getContext('2d');
        let ctx_chart_vm_mem = document.getElementById('chart-vm-mem').getContext('2d');
        let ctx_chart_vm_disk = document.getElementById('chart-vm-disk').getContext('2d');
        let ctx_chart_vm_network = document.getElementById('chart-vm-network').getContext('2d');
        window.chart_vm_cpu = new Chart(ctx_chart_vm_cpu, {
            type: 'line',
            fill: true,
            data: {
                labels: window.vm_stats_chart_labels,
                datasets: [
                    {
                        label: 'CPU',
                        fill: true,
                        borderWidth: 1,
                        borderColor: 'blue',
                        radius: 0,
                        data: window.vm_stats_chart_cpu_data,
                    }
                ]
            },
            options: {
                animation: false,
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'CPU使用率(%)'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        min: 0,
                        max: 100
                    }
                }
            }
        });
        window.chart_vm_mem = new Chart(ctx_chart_vm_mem, {
            type: 'line',
            data: {
                labels: window.vm_stats_chart_labels,
                datasets: [
                    {
                        label: 'Memory',
                        fill: true,
                        borderWidth: 1,
                        borderColor: 'blue',
                        radius: 0,
                        data: window.vm_stats_chart_mem_data,
                    }
                ]
            },
            options: {
                animation: false,
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Memory使用率(%)'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        min: 0,
                        max: 100
                    }
                }
            }
        });
        window.chart_vm_disk = new Chart(ctx_chart_vm_disk, {
            type: 'line',
            data: {
                labels: window.vm_stats_chart_labels,
                datasets: [
                    {
                        label: 'Read IO',
                        fill: false,
                        borderWidth: 1,
                        borderColor: 'green',
                        radius: 0,
                        data: window.vm_stats_chart_disk_data.rd_kb,
                    },
                    {
                        label: 'Write IO',
                        fill: false,
                        borderWidth: 1,
                        borderColor: 'blue',
                        radius: 0,
                        data: window.vm_stats_chart_disk_data.wr_kb,
                    }
                ]
            },
            options: {
                animation: false,
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '硬盘读写IO(Kb/s)'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        min: 0,
                    }
                }
            }
        });
        window.chart_vm_network = new Chart(ctx_chart_vm_network, {
            type: 'line',
            data: {
                labels: window.vm_stats_chart_labels,
                datasets: [
                    {
                        label: 'Rx IO',
                        fill: false,
                        borderWidth: 1,
                        borderColor: 'green',
                        radius: 0,
                        data: window.vm_stats_chart_net_data.rx_kb,
                    },
                    {
                        label: 'Tx IO',
                        fill: false,
                        borderWidth: 1,
                        borderColor: 'blue',
                        radius: 0,
                        data: window.vm_stats_chart_net_data.tx_kb,
                    }
                ]
            },
            options: {
                animation: false,
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '网络读写IO(Kb/s)'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        min: 0,
                    }
                }
            }
        });
    }
})();