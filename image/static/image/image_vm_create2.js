;'use strict';
(function () {

    var IMAGES = {};    // 缓存镜像信息

    function get_image_from_cache(index) {
        if (IMAGES.hasOwnProperty(index)) {
            return IMAGES[index];
        }
        return null;
    }

    function set_image_to_cache(index, html) {
        IMAGES[index] = html;
    }

    //
    // 页面刷新时执行
    window.onload = function () {
        nav_active_display();
        update_vlan_select_items();
        update_host_select_items();
        set_image_to_cache($("#id-image-tag").val(), $('select[name="image_id"]').html())
    };

    // 激活虚拟机列表导航栏
    function nav_active_display() {
        $("#nav_vm_list").addClass("active");
    }

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
    $('select[name="data_center"]').change(function () {
        // this.form.submit();
        update_group_select_items()

    });

    // 宿主机组下拉框选项改变事件
    $('select[name="group_image"]').change(function () {
        update_host_image_select_items()
        update_vlan_image_select_items();

    });

    // $('select[name="host_image"]').change(function () {
    //     update_ipv4_image_select_items();
    // });

    $('select[name="vlan_image"]').change(function () {
        update_ipv4_image_select_items();
    });


    let render_group_select_items = template.compile(`
        <option value="">自动选择</option>
        {{ each results }}
            <option value="{{ $value.center }}">{{ $value.name }}</option>
        {{/each}}
    `);

    function update_group_select_items() {
        let dc = $('select[name="data_center"]').val();
        if (!dc) {
            return;
        }
        let qs = encode_params({center_id: dc});
        let api = build_absolute_url('/api/v3/group/?' + qs);
        $.ajax({
            url: api, type: 'get', async: false, success: function (data) {
                let html = render_group_select_items(data);
                let host = $('select[name="group_image"]');
                host.empty();
                host.append(html);
            }, error: function (xhr) {
                alert(gettext('加载宿主机组下拉框选项失败'));
            }
        })

    }

    let render_host_image_select_items = template.compile(`
        <option value="">自动选择</option>
        {{ each results }}
            <option value="{{ $value.id }}">
                {{ $value.ipv4 }}(vCPU:{{$value.vcpu_allocated}}/{{$value.vcpu_total - $value.vcpu_allocated}}/{{$value.vcpu_total}}, 
                RAM:{{$value.mem_allocated}}Gb/{{$value.mem_total - $value.mem_allocated}}Gb/{{$value.mem_total}}Gb),
                Num:{{$value.vm_created}}/{{$value.vm_limit - $value.vm_created}}/{{$value.vm_limit}}
            </option>
        {{/each}}
    `);

    // 加载宿主机下拉框
    function update_host_image_select_items() {
        let group = $('select[name="group_image"]').val();
        if (!group) {
            return;
        }
        let qs = encode_params({group_id: group, mem_unit: 'GB'});
        let api = build_absolute_url('/api/v3/host/?' + qs);
        $.ajax({
            url: api, type: 'get', async: false, success: function (data) {
                let html = render_host_image_select_items(data);
                let host = $('select[name="host_image"]');
                host.empty();
                host.append(html);
            }, error: function (xhr) {
                alert(gettext('加载宿主机下拉框选项失败'));
            }
        })
    }


    // 加载子网vlan下拉框渲染模板
    let render_vlan_image_select_items = template.compile(`
        <option value="">自动选择</option>
        {{ each results }}
            <option value="{{ $value.id }}">{{ $value.name }}</option>
        {{/each}}
    `);

    // 加载子网vlan下拉框
    function update_vlan_image_select_items() {
        let group = $('select[name="group_image"]').val();
        if (!group) {
            return;
        }
        let qs = encode_params({group_id: group});
        let api = build_absolute_url('/api/v3/vlan/?' + qs);
        $.ajax({
            url: api, type: 'get', async: false, success: function (data) {
                let html = render_vlan_image_select_items(data);
                let vlan = $('select[name="vlan_image"]');
                vlan.empty();
                vlan.append(html);
            }, error: function (xhr) {
                alert(gettext('加载子网vlan下拉框选项失败'));
            }
        })
    }


    // 加载MAC IP下拉框渲染模板
    let render_ipv4_image_select_items = template.compile(`
        <option value="">自动选择</option>
        {{ each results }}
            <option value="{{ $value.ipv4 }}">
                {{ $value.ipv4 }}
            </option>
        {{/each}}
    `);

    // 加载MAC IP下拉框
    function update_ipv4_image_select_items() {
        let vlan = $('select[name="vlan_image"]').val();
        if (!vlan) {
            let html = '<option value="">自动选择</option>';
            let ipv4 = $('select[name="mac_ip"]');
            ipv4.empty();
            ipv4.append(html);
            return;
        }
        let qs = encode_params({vlan_id: vlan, used: false});
        let api = build_absolute_url('/api/v3/macip/?' + qs);
        $.ajax({
            url: api, type: 'get', async: false, success: function (data) {
                let html = render_ipv4_image_select_items(data);
                let ipv4 = $('select[name="mac_ip"]');
                ipv4.empty();
                ipv4.append(html);
            }, error: function (xhr) {
                alert(gettext('加载IP下拉框选项失败'));
            }
        })
    }


    // 校验创建虚拟机参数
    function valid_vm_create_data(obj) {
        if ((obj.group_id <= 0) && (obj.host_id <= 0)) {
            alert(gettext('机组和宿主机至少选择其一'));
            return false;
        }
        if ((obj.group_id <= 0)) {
            delete obj.group_id;
        }
        if ((obj.host_id <= 0)) {
            delete obj.host_id;
        }
        if (!obj.vlan_id || obj.vlan_id <= 0) {
            delete obj.vlan_id;
        }
        if (!obj.flavor_id || obj.flavor_id <= 0) {
            if (isNaN(obj.vcpu) || obj.vcpu <= 0) {
                alert(gettext('配置CPU输入不是有效正整数'));
                return false;
            }
            if (isNaN(obj.mem) || obj.mem <= 0) {
                alert(gettext('配置RAM输入不是有效正整数'));
                return false;
            }

            delete obj.flavor_id;
        } else {
            delete obj.vcpu;
            delete obj.mem;
        }
        return true;
    }

    // 创建虚拟机表单提交按钮点击事件
    $('form#id-form-image-create button[type="submit"]').click(function (e) {
        e.preventDefault(); // 兼容标准浏览器
        var form = $('form#id-form-image-create');
        let obj_data = getForm2Obj(form);
        if (!valid_vm_create_data(obj_data)) {
            return;
        }
        if (!confirm(gettext('确定创建虚拟机？'))) return;

        let api = build_absolute_url('image/create/' + obj_data.image_id + '/');
        let json_data = JSON.stringify(obj_data);
        let btn_submit = $(this);
        btn_submit.addClass('disabled'); //鼠标悬停时，使按钮表现为不可点击状态
        btn_submit.attr('disabled', true);//失能对应按钮
        $.ajax({
            url: api, type: 'post', dataType: "json", data: obj_data, success: function (data, status, xhr) {
                console.log(data, status, xhr)
                if (xhr.status === 201) {
                    if (confirm(gettext('创建成功,是否去镜像列表看看？'))) {
                        window.location = '/image/';
                    }
                } else {
                    alert(gettext("创建失败！") + data.code_text);
                }
            }, error: function (xhr) {
                let msg = gettext('创建主机失败!');
                try {
                    msg = msg + xhr.responseJSON.code_text;
                } catch (e) {
                }
                alert(msg);
            }, complete: function () {
                btn_submit.removeClass('disabled');   //鼠标悬停时，使按钮表现为可点击状态
                btn_submit.attr('disabled', false); //激活对应按钮
            }
        })
    });






})();

