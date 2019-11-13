;(function f() {

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

    //
    // 页面刷新时执行
    window.onload = function() {
        $("#nav_vdisk_list").addClass("active");// 激活云硬盘列表导航栏
    };

    /**
     * 拼接params对象为url参数字符串
     * @param {Object} obj - 待拼接的对象
     * @returns {string} - 拼接成的query参数字符串
     */
    function encode_params(obj) {
        const params = [];

        Object.keys(obj).forEach((key) => {
            let value = obj[key];
            // 如果值为undefined我们将其置空
            if (typeof value === 'undefined') {
                value = ''
            }
            // 对于需要编码的文本我们要进行编码
            params.push([key, encodeURIComponent(value)].join('='))
        });

        return params.join('&');
    }

    // 分中心下拉框选项改变事件
    $('select[name="center_id"]').change(function () {
        this.form.submit();
    });

    // 宿主机组下拉框选项改变事件
    $('select[name="group_id"]').change(function () {
        update_quota_select_items();
    });

    //
    // 加载硬盘存储池配额下拉框渲染模板
    //
    let render_host_select_items = template.compile(`
        <option value="">自动选择</option>
        {{ each results }}
            <option value="{{ $value.id }}">
                {{ $value.name }}(size:{{$value.size_used}}/{{$value.total}}GB, 
                max limit:{{$value.max_vdisk}}GB)
            </option>
        {{/each}}
    `);

    // 加载硬盘存储池配额下拉框
    function update_quota_select_items(){
        let group = $('select[name="group_id"]').val();
        if(!group){
            return;
        }
        let qs = encode_params({group_id:group});
        let api = build_absolute_url('/api/v3/quota/?'+ qs);
        $.ajax({
            url: api,
            type: 'get',
            async: false,
            success: function (data) {
                let html = render_host_select_items(data);
                let host = $('select[name="quota_id"]');
                host.empty();
                host.append(html);
            },
            error: function (xhr) {
                alert('加载硬盘存储池配额下拉框选项失败');
            }
        })
    }

    // 校验创建硬盘参数
    function valid_disk_create_data(obj){
        if((obj.group_id <= 0) && (obj.quota_id <= 0)){
            alert('机组和硬盘存储池至少选择其一');
            return false;
        }
        if ((obj.group_id <= 0)){
            delete obj.group_id;
        }
        if ((obj.quota_id <= 0)){
            delete obj.quota_id;
        }
        if(obj.mem <= 0){
            alert('请选择或输入有效的容量大小');
            return false;
        }
        return true;
    }

    // 创建硬盘表单提交按钮点击事件
    $('form#id-form-create button[type="submit"]').click(function (e) {
        let event = e || window.event;
        event.preventDefault(); // 兼容标准浏览器
        window.event.returnValue = false; // 兼容IE6~8

        let form = $('form#id-form-create');
        let obj_data = getForm2Obj(form);
        if (!valid_disk_create_data(obj_data)){
            return;
        }
        if(!confirm('确定创建硬盘吗？'))
            return;

        let api = build_absolute_url('api/v3/vdisk/');
        let json_data = JSON.stringify(obj_data);
        let btn_submit = $(this);
        btn_submit.addClass('disabled'); //鼠标悬停时，使按钮表现为不可点击状态
        btn_submit.attr('disabled', true);//失能对应按钮
        $.ajax({
            url: api,
            type: 'post',
            data: json_data,
            contentType: 'application/json',
            success: function (data, status, xhr) {
                if (xhr.status === 201){
                    if(confirm('创建成功,是否去硬盘列表看看？')){
                        window.location = '/vdisk/';
                    }
                }else{
                    alert("创建失败！" + data.code_text);
                }
            },
            error: function (xhr) {
                let msg = '创建硬盘失败!';
                try{
                    msg = msg + xhr.responseJSON.code_text;
                }catch (e) {}
                alert(msg);
            },
            complete: function () {
                btn_submit.removeClass('disabled');   //鼠标悬停时，使按钮表现为可点击状态
                btn_submit.attr('disabled', false); //激活对应按钮
            }
        })
    });

})();