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

    let largePageMemory = par.children[6].innerHTML.split(' / ')
    let invalidStr = largePageMemory.indexOf("未检测")
    if (invalidStr > -1) {
        // 表示数组含有此字符串
        alert("请重新检测，未找到相应内容数据。")
        return
    }

    $.ajax({
        url: '/reports/host/' + obj, type: 'POST', headers: {
            'X-CSRFToken': csrf_token
        }, data: {'mem_use_num': largePageMemory[0], 'mem_total': largePageMemory[1]},

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

            // console.log(data.msg)

            let dataarr = data.msg.split(',')

            par.children[6].innerHTML = dataarr[4] + " / " + dataarr[5] + " / " + dataarr[6] + "%"
            par.children[6].style.color = 'red'

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


function renderLargePageMemory(element, reslist) {
    // element => getElementById("tbody-host")
    // reslist => {ip: []}

    // console.log(JSON.parse(reslist))  // "{'ip': [' 23', '123', ' 18.70'], 'ip2': [' 23', '123', ' 18.70']}"
    let validJsonString = reslist.replace(/'/g, '"');

    let json_obj = JSON.parse(validJsonString)

    // 遍历表格行
    for (let i = 0; i < element.rows.length; i++) {
        // 获取特定列的内容，这里假设第二列是索引为 1 的列
        let cell = element.rows[i].cells[1].innerHTML;
        if (Object.values(json_obj)[i][0] == '未检测'){
            element.rows[i].cells[6].innerHTML = Object.values(json_obj)[i][0] + " / " + Object.values(json_obj)[i][1] + " / " + Object.values(json_obj)[i][2]

        }else {
            element.rows[i].cells[6].innerHTML = Object.values(json_obj)[i][0] + " / " + Object.values(json_obj)[i][1] + " / " + Object.values(json_obj)[i][2] + "%"
            element.rows[i].cells[6].style.color = 'red'

        }

    }
}

let batchDetection = document.getElementById('one-click-detection')
// let batchDetection = document.getElementById('batchdetection-ip')

// 批量检测
batchDetection.addEventListener('click', function () {
    // 获取页面主机IP
    //  ip --》 {'ip': [0,0,0]}

    ipList = []
    // 找到包含表格的 HTML 元素
    let table = document.getElementById("tbody-host");

    // 遍历表格行
    for (let i = 0; i < table.rows.length; i++) {
        // 获取特定列的内容，这里假设第二列是索引为 1 的列
        let cell = table.rows[i].cells[1];

        // 输出内容到控制台或者执行其他操作
        ipList.push(cell.textContent)
    }

    let csrftoken = getCookie('csrftoken');
    $.ajax({
        url: '/reports/host/detect/',
        type: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        },
        contentType: 'application/json',
        data: JSON.stringify({'ip_list':ipList}),
        // data: {'ip_list':ipList},

        success: function (data) {
            // console.log(data.msg)
            renderLargePageMemory(table, data.msg)

        },
        error: function (data) {
            // Handle error
            $('#exampleModal').modal('hide')
            alert('保存数据失败：' + data.responseJSON.msg_error)
        }
    })

})


let savedetection = document.getElementById('batch-save')
savedetection.addEventListener('click', function () {

    let table = document.getElementById('tbody-host')
    let json_host = {}  // {ip:[x,x,x]}

    // 遍历表格行
    for (let i = 0; i < table.rows.length; i++) {

        let info = []

        // 获取特定列的内容，这里假设第二列是索引为 1 的列
        let cell = table.rows[i].cells[1];

        // 输出内容到控制台或者执行其他操作
        console.log(cell.textContent);
        // ipList.push(cell.textContent)    // ip

        let cell_content = table.rows[i].cells[6].innerHTML.split(' / ')  // 大页内存
        info.push(cell_content[0])
        info.push(cell_content[1])


        json_host[cell.innerHTML] = info

    }


    let csrftoken = getCookie('csrftoken');
    $.ajax({
        url: '/reports/host/batchsave/', type: 'POST', headers: {
            'X-CSRFToken': csrftoken
        }, data: {host_info: JSON.stringify(json_host)},

        success: function (data) {
            // Handle success
            alert(data.msg)
            window.location.reload()

        }, error: function (data) {
            // Handle error
            alert('保存数据失败：' + data.responseJSON.msg_error)
        }
    })


})
