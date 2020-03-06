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

})();