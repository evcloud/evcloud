var VM_TASK_CN = {
	'start': '启动',
	'reboot': '重启',
	'shutdown': '关闭',
	'poweroff': '关闭电源',
	'delete': '删除',
	'reset': '重置'
}

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
    9: '宿主机故障',  //宿主机连接失败
    10: '云主机故障'  //虚拟机丢失
}

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
}

function action(url, vmid, action, success_callback, error_callback, complete_callback) {
	$.ajax({
		url: url,
		type: 'post',
		data: {
			'vmid': vmid,
			'op': action,
		},
		success:success_callback,
		error: error_callback,
		complete:complete_callback
		
	}, 'json');
}

function update_status(url, vmids, interval){
	for(var i in vmids) {
		setInterval("get_status('"+url+"', '" + vmids[i] + "')", interval);
		get_status(url, vmids[i]);
	}
}

function get_status(url, vmid) {
	$.ajax({
		url: url,
		type: 'post',
		data: {
			'vmid': vmid,
		},
		cache:false,
		success: function(data) {
			if (data.res == true){
				$("#" + window.vm_status_tag + data.vmid).html("<span class='label label-" + VM_STATUS_LABEL[data.status] + "'>" + VM_STATUS_CN[data.status] + "</span>");
			}
		},
	}, 'json');
}

function vm_reboot(url, vmid){
	if(!confirm('确定重启虚拟机？'))
		return;
	$("#" + window.vm_task_tag + vmid).html(VM_TASK_CN["reboot"]);
	action(url, vmid, 'reboot',
		function(data){
			if(data.res) {
				alert('重启成功！');
			} else {
				alert('重启失败： ' + data.error);
			}
		},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");
		}
		);
}

function vm_shutdown(url, vmid){
	if(!confirm('确定关闭虚拟机？'))
		return;
	$("#" + window.vm_task_tag + vmid).html(VM_TASK_CN["shutdown"]);
	action(url, vmid, 'shutdown',
		function(data){
			if(data.res) {
			} else {
				alert('关闭虚拟机失败： ' + data.error);
			}
		},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");}
		);
}

function vm_poweroff(url, vmid){
	if(!confirm('确定强制关闭虚拟机电源？'))
		return;
	$("#" + window.vm_task_tag + vmid).html(VM_TASK_CN["poweroff"]);
	action(url, vmid, 'poweroff',
		function(data){
			if(data.res) {
			} else {
				alert('关闭电源失败： ' + data.error);
			}
		},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");}
		);
}

function vm_start(url, vmid){
	$("#" + window.vm_task_tag + vmid).html(VM_TASK_CN["start"]);
	action(url, vmid, 'start',
		function(data){
			if(data.res) {
			} else {
				alert('启动失败： ' + data.error);
			}
		},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");}
		);
}

function vm_delete(url, vmid,need_refresh){

	if(!confirm('确定删除虚拟机？'))
		return;
	$("#" + window.vm_task_tag + vmid).html(VM_TASK_CN["delete"]);
	action(url, vmid, 'delete',
		function(data){
			if (data.res == true) {
				if(need_refresh === 'false'){
					$("#tr_" + vmid).remove();
					$("#next_tr_" + vmid).remove();

				}else {
					window.location.reload();
				}


			} else {
				alert('删除失败： ' + data.error);
			}
		},
		function(data){},
		function(data){
			// get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");}
		);
}

function vm_delete_force(url, vmid,need_refresh) {
	if (!confirm('强制删除虚拟机记录，是否确定？'))
		return;
	$("#" + window.vm_task_tag + vmid).html(VM_TASK_CN["delete"]);
	action(url, vmid, 'delete_force',
		function (data) {
			if (data.res == true) {
				if(need_refresh === 'false'){
					$("#tr_" + vmid).remove();
					$("#next_tr_" + vmid).remove();

				}else {
					window.location.reload();
				}
			} else {
				alert('删除失败： ' + data.error);
			}
		},
		function (data) { },
		function (data) {
			// get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");
		}
	);
}

function vm_reset(url, vmid){
	if(!confirm('确定重置虚拟机？'))
		return;
	$("#" + window.vm_task_tag + vmid).html(VM_TASK_CN["reset"]);
	action(url, vmid, 'reset',
		function(data){
			if(data.res) {
				alert('重置成功！');
			} else {
				alert('重置失败： ' + data.error);
			}
		},
		function(data){},
		function(data){
			get_status(window.vm_status_url , vmid);
			$("#" + window.vm_task_tag + vmid).html("");
		}
		);
}


//批量操作: by lzx 20180712
function batch_action(url, vmid_list, action, success_callback, error_callback, complete_callback) {
	$.ajax({
		url: url,
		type: 'post',
		data: {
			'vmid_list': vmid_list,
			'op': action,
		},
		success:success_callback,
		error: error_callback,
		complete:complete_callback
		
	}, 'json');
}
