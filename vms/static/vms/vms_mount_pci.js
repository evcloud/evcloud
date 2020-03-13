;(function () {

    //API域名
    let DOMAIN_NAME = get_domain_url();
    let API_VERSION = 'v3';

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

    //
    // 页面刷新时执行
    window.onload = function() {
        // 激活虚拟机列表导航栏
        $("#nav_vm_list").addClass("active");
    };

    $(".btn-pci-mount").click(function (e) {
        e.preventDefault();
        if(!confirm("确定挂载此设备吗？"))
            return;

        let vm_uuid = $("#id-mount-vm-uuid").text();
        let pci_id = $(this).attr("data-pci-id");
        let api = build_absolute_url('api/' + API_VERSION + '/pci/' + pci_id + '/mount/?vm_uuid=' + vm_uuid);
        $.ajax({
            url: api,
            type: 'post',
            success: function (data, status_text) {
                $("#tr_" + pci_id).remove();
                alert('已成功挂载设备');
            },
            error: function (xhr, msg, err) {
                let data = xhr.responseJSON;
                msg = '挂载设备失败';
                if (data && data.hasOwnProperty('code_text')){
                    msg = data.code_text;
                }
                alert(msg);
            }
        });
    })
})();
