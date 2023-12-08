$(document).ready(function(jQuery) {
    jQuery(function($) {
        $('select#id_pcserver').on('change', function() {
            let selected_pcserver_id = $(this).children('option:selected').val()
            $.ajax({
                url: '/pcservers?server_id=' + selected_pcserver_id,
                type: 'get',
                async: false,
                success: function (data) {
                    $('.field-ipv4 .readonly').text(data.host_ipv4)
                    $('.field-pc_server_resource .readonly').text(data.real_cpu+'核/'+data.real_mem+'GB')
                },
                error: function (xhr) {
                    alert('加载宿主机下拉框选项失败');
                }
          })
        });
    });
});