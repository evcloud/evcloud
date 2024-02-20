;(function () {

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

})

function saveHostInfo(th, obj, csrf_token) {

    let par = th.parentNode.parentNode // tr
    let realcpu = par.children[2].children[0].innerHTML
    let realcpuarr = realcpu.split('GB')
    let realcpulint = parseInt(realcpuarr[0].trim())

    let vcputotal = par.children[3].children[0].innerHTML

    let vcputotalarr = vcputotal.split('GB')
    let vcputotalint = parseInt(vcputotalarr[0].trim())

    let memtotal = par.children[6].children[0].innerHTML
    let memtotalarr = memtotal.split('GB')
    let memtotalint = parseInt(memtotalarr[0].trim())


    let msg = "物理cpu: " + realcpulint + ", 虚拟cpu: " + vcputotalint + ", 可分配内存: " + memtotalint
    if (!confirm(msg)) {
        return
    }

    // console.log(realcpu, vcputotal, memtotalint)
    //
    $.ajax({
        url: '/reports/host/' + obj, type: 'POST', headers: {
            'X-CSRFToken': csrf_token
        }, data: {'realcpu': realcpu, 'vcputotal': vcputotal, 'memtotalint': memtotalint},

        success: function (data) {
            // Handle success
            alert(data.msg)
            window.location.reload()

        }, error: function (data) {
            // Handle error
            alert('保存数据失败：' + data.responseJSON.msg_error)
        }
    })


}

function detectionHost(th, obj, csrf_token) {

    $.ajax({
        url: '/reports/host/' + obj, type: 'GET', headers: {
            'X-CSRFToken': csrf_token
        },

        success: function (data) {
            // Handle success

            let par = th.parentNode.parentNode //

            console.log(data.msg)

            let dataarr = data.msg.split(',')


            let newChild = document.createElement('span');
            newChild.style.color = 'red'

            par.children[2].innerHTML = par.children[2].innerHTML + '/'
            // let newChild2 = newChild.cloneNode(true);
            par.children[2].appendChild(newChild)
            par.children[2].children[0].innerHTML = dataarr[0]

            par.children[3].innerHTML = par.children[3].innerHTML + '/'
            let newChild3 = newChild.cloneNode(true);
            par.children[3].appendChild(newChild3)
            par.children[3].children[0].innerHTML = dataarr[1]

            // par.children[4].innerHTML = dataarr[2]
            // par.children[5].innerHTML = dataarr[3] + '%'
            par.children[5].innerHTML = par.children[5].innerHTML + '/'
            let newChild5 = newChild.cloneNode(true);
            par.children[5].appendChild(newChild5)
            par.children[5].children[0].innerHTML = dataarr[3] + '%'


            par.children[6].innerHTML = par.children[6].innerHTML + '/'
            let newChild6 = newChild.cloneNode(true);
            par.children[6].appendChild(newChild6)
            par.children[6].children[0].innerHTML = dataarr[4] + 'GB'

            par.children[7].innerHTML = par.children[7].innerHTML + '/'
            let newChild7 = newChild.cloneNode(true);
            par.children[7].appendChild(newChild7)
            par.children[7].children[0].innerHTML = dataarr[5] + 'GB' // 不准确 获取大页内存 如果关机是否占用、如果

            par.children[8].innerHTML = par.children[8].innerHTML + '/'
            let newChild78 = newChild.cloneNode(true);  //  深层副本， 使用同一个newChild 前几个添加的标签都会移动到最后一个
            par.children[8].appendChild(newChild78)
            par.children[8].children[0].innerHTML = dataarr[6] + "%"


        }, error: function (data) {
            // Handle error
            alert('获取数据失败：' + data.responseJSON.msg_error)
        }
    })

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

let batchDetection = document.getElementById('batchdetection-ip')
batchDetection.addEventListener('click', function () {
    let ip_start = document.getElementById('ip-start').value
    let ip_end = document.getElementById('ip-end').value
    let ip_subent = document.getElementById('ip-subnet').value

    if (ip_start.trim() === '' || ip_end.trim() === '' || ip_subent.trim() === '') {
        alert('请将内容填写完整')
        return
    }
    let csrftoken = getCookie('csrftoken');
    $.ajax({
        url: '/reports/host/detect/', type: 'GET', headers: {
            'X-CSRFToken': csrftoken
        }, data: {'ip_start': ip_start, 'ip_end': ip_end, 'ip_subent': ip_subent},

        success: function (data) {
            // Handle success
            // console.log(data.msg)
            let obj = JSON.parse(data.msg)
            let tbody_host = document.getElementById('tbody-host')
            for (let key in obj) {
                if (obj.hasOwnProperty(key)) {
                    // console.log(key + ": " + obj[key]);
                    let data_list = obj[key].split(',')

                    let temp_tr = `<tr>
                                    <td>${key}</td>
                                    <td>无</td>
                                    <td>${data_list[0]}</td>
                                    <td>${data_list[1]}</td>
                                    <td>${data_list[2]}</td>
                                    <td>${data_list[3]}%</td>
                                    <td>${data_list[4]} GB</td>
                                    <td>${data_list[5]} GB</td>
                                    <td>${data_list[6]}%</td>
                                    <td>0</td>
      
                                </tr>`
                    //   <td><a type="button" class="btn btn-primary"
                    //        onclick='detectionHost( this ,"${key}", "{{ csrf_token }}")'
                    //        style="color: #fff;">检测</a>
                    //     | <a
                    //             type="button"
                    //             className="btn btn-primary" style="color: #fff;"
                    //             onClick="saveHostInfo(this, '${key}', '{{ csrf_token }}')">保存</a>
                    // </td>
                    tbody_host.innerHTML = ''
                    tbody_host.insertAdjacentHTML('beforeend', temp_tr);

                }
            }
            $('#exampleModal').modal('hide')

            // console.log(data.error)
            if (data.error !== "{}"){
                alert(data.error)
            }


        }, error: function (data) {
            // Handle error
            $('#exampleModal').modal('hide')
            alert('保存数据失败：' + data.responseJSON.msg_error)
        }
    })

})


let savedetection = document.getElementById('savedetection-ip')
savedetection.addEventListener('click', function () {
    let savedetect_group = $('#id-group-savedetect').val()
    let savedetect_room = $('#id-room-savedetect').val()

    // if(){}

    let tbody_host = document.getElementById('tbody-host')
    let json_host = {}

    let tr_obj = tbody_host.children

    for (let i = 0; i < tr_obj.length; i++) {
        let info = []
        let td_obj = tr_obj[i].children
        info.push(td_obj[2].innerHTML)
        let newStr = td_obj[6].innerHTML.replace(/\s/g, '');
        newStr = newStr.replace(/&nbsp;/g, '');
        newStr = newStr.split('GB')[0]
        info.push(newStr)

        td_obj[1].innerHTML

        json_host[td_obj[0].innerHTML] = info

    }

    let csrftoken = getCookie('csrftoken');
    $.ajax({
        url: '/reports/host/detect/', type: 'POST', headers: {
            'X-CSRFToken': csrftoken
        }, data: {'room': savedetect_room, 'group': savedetect_group, host_info: JSON.stringify(json_host)},

        success: function (data) {
            // Handle success
            $('#exampleModal2').modal('hide')
            alert(data.msg)

        }, error: function (data) {
            // Handle error
            $('#exampleModal2').modal('hide')
            alert('保存数据失败：' + data.responseJSON.msg_error)
        }
    })


})