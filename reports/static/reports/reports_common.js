;

window.chartColors = {
    red: 'rgb(255, 99, 132)',
    orange: 'rgb(255, 159, 64)',
    yellow: 'rgb(255, 205, 86)',
    green: 'rgb(75, 192, 192)',
    blue: 'rgb(54, 162, 235)',
    purple: 'rgb(153, 102, 255)',
    grey: 'rgb(201, 203, 207)'
};

function chart_init() {
    var canvas_mem = document.getElementById('id-chart-mem').getContext('2d');
    var canvas_cpu = document.getElementById('id-chart-cpu').getContext('2d');
    var canvas_vm = document.getElementById('id-chart-vm').getContext('2d');
    window.chart_mem = new Chart(canvas_mem, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: '预留',
                backgroundColor: window.chartColors.red,
                maxBarThickness: 50,
                data: []
            },{
                label: '已用',
                backgroundColor: window.chartColors.grey,
                maxBarThickness: 50,
                data: []
            }, {
                label: '可用',
                backgroundColor: window.chartColors.green,
                maxBarThickness: 50,
                data: []
            }]
        },
        options: {
            title: {
                display: true,
                text: 'MEM of Group'
            },
            tooltips: {
                mode: 'index',
                intersect: false
            },
            responsive: true,
            scales: {
                xAxes: [{
                    stacked: true,
                }],
                yAxes: [{
                    stacked: true
                }]
            }
        }
    });
    window.chart_cpu = new Chart(canvas_cpu, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: '已用',
                maxBarThickness: 50,
                backgroundColor: window.chartColors.grey,
                data: []
            }, {
                label: '可用',
                maxBarThickness: 50,
                backgroundColor: window.chartColors.green,
                data: []
            }]
        },
        options: {
            title: {
                display: true,
                text: 'CPU of Group'
            },
            tooltips: {
                mode: 'index',
                intersect: false
            },
            responsive: true,
            scales: {
                xAxes: [{
                    stacked: true,
                }],
                yAxes: [{
                    stacked: true
                }]
            }
        }
    });
    window.chart_vm = new Chart(canvas_vm, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: '云主机数量',
                backgroundColor: window.chartColors.blue,
                maxBarThickness: 50,
                data: []
            }]
        },
        options: {
            title: {
                display: true,
                text: 'Vm of Group'
            },
            tooltips: {
                mode: 'index',
                intersect: false
            },
            responsive: true,
            scales: {
                xAxes: [{
                    stacked: true,
                }],
                yAxes: [{
                    stacked: true
                }]
            }
        }
    });
}

function percentageFormat(val, base){
    if ((val === 0) || (base === 0)){
        return '0.00%';
    }
    try{
        let per = (val / base) * 100;
        return per.toFixed(2) + '%';
    }catch (e) {
        return '0.00%';
    }
}

function sizeFormat(val, unit){
    switch (unit) {
        case "KB":
            if (val > 1024){
                val = val / 1024;
                value = sizeFormat(val, 'MB');
            }else{
                value = val.toFixed(2) + 'KB';
            }
             break;
        case "MB":
            if (val > 1024){
                val = val / 1024;
                value = sizeFormat(val, 'GB');
            }else{
                value = val.toFixed(2) + 'MB';
            }
            break;
        case "GB":
            if (val > 1024){
                val = val / 1024;
                value = sizeFormat(val, 'TB');
            }else{
                value = val.toFixed(2) + 'GB';
            }
            break;
        case "TB":
            if (val > 1024){
                val = val / 1024;
                value = sizeFormat(val, 'PB');
            }else{
                value = val.toFixed(2) + 'TB';
            }
            break;
        case "PB":
            value = val.toFixed(2) + 'PB';
            break;
    }

    return value
}


