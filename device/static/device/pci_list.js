;(function f() {

    // 页面刷新时执行
    window.onload = function() {
        nav_active_display();
    };
    // 激活虚拟机列表导航栏
    function nav_active_display() {
        $("#nav_pci_list").addClass("active");
    }

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

    $('select[name="type"]').change(function () {
        this.form.submit();
    });

    // 卸载设备
    $(".btn-pci-unmount").click(function (e) {
        e.preventDefault();

        if(!confirm(gettext("确定卸载设备？")))
            return;

        let pci_id = $(this).attr("data-pci-id");
        let api = build_absolute_url('api/v3/pci/' + pci_id + '/umount/');
        $.ajax({
            url: api,
            type: 'post',
            success: function (data, status_text) {
                alert(gettext('已成功卸载设备'));
            },
            error: function (xhr, msg, err) {
                let data = xhr.responseJSON;
                msg = gettext('卸载设备失败');
                if (data && data.hasOwnProperty('code_text')){
                    msg = data.code_text;
                }
                alert(msg);
            }
        });
    });

})();