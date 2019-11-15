;(function () {

    //
    // 页面刷新时执行
    window.onload = function() {
        $("#nav_vdisk_list").addClass("active");// 激活云硬盘列表导航栏
    };

    $('select[name="center"]').change(function () {
        $('select[name="group"]').val('');
        $('select[name="host"]').val('');
        this.form.submit();
    });

    $('select[name="group"]').change(function () {
        $('select[name="host"]').val('');
        this.form.submit();
    });

    $('select[name="quota"]').change(function () {
        this.form.submit();
    });

    $('select[name="user"]').change(function () {
        this.form.submit();
    });

    $('.edit_disk_remark').click(function (e) {
        e.preventDefault();

        vm_uuid = $(this).attr('data-disk-uuid');
        let div_show = $(this).parent();
        div_show.hide();
		div_show.next().show();
    });

    $('.save_disk_remark').click(function (e) {
        e.preventDefault();
        let disk_uuid = $(this).attr('data-disk-uuid');
        let dom_remark = $(this).prev();
        let remark = dom_remark.val();
        let div_edit = dom_remark.parent();
        let div_show = div_edit.prev();

        $.ajax({
			url: build_absolute_url('/api/v3/vdisk/' + disk_uuid + '/remark/?remark='+ remark),
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

    //卸载硬盘
    $('.btn-disk-umount').click(function (e) {
        e.preventDefault();
        if(!confirm("确定要卸载此硬盘吗？")){
            return
        }
        let disk_uuid = $(this).attr('data-disk-uuid');
        $.ajax({
			url: build_absolute_url('/api/v3/vdisk/' + disk_uuid + '/umount/'),
			type: 'patch',
            success: function (data, status_text) {
                alert('已成功卸载硬盘');
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '卸载硬盘失败' + msg;
                if (data.hasOwnProperty('code_text')){
                    msg = data.code_text;
                }
                alert(msg);
            }
		});
    });

    // 销毁此硬盘
    $('.btn-disk-delete').click(function (e) {
        e.preventDefault();
        if(!confirm("确定要销毁此硬盘吗？")){
            return
        }
        let disk_uuid = $(this).attr('data-disk-uuid');
        $.ajax({
			url: build_absolute_url('/api/v3/vdisk/' + disk_uuid + '/'),
			type: 'delete',
            success: function (data, status_text) {
			    $("#tr_" + disk_uuid).remove();
                alert('已成功销毁硬盘');
            },
            error: function (xhr, msg, err) {
                data = xhr.responseJSON;
                msg = '销毁硬盘' + msg;
                if (data.hasOwnProperty('code_text')){
                    msg = data.code_text;
                }
                alert(msg);
            }
		});
    });

})();