;
/**
 * 去除字符串前后给定字符，不改变原字符串
 * @param char
 * @returns { String }
 */
String.prototype.strip = function (char) {
  if (char){
    return this.replace(new RegExp('^\\'+char+'+|\\'+char+'+$', 'g'), '');
  }
  return this.replace(/^\s+|\s+$/g, '');
};

//返回一个去除右边的给定字符的字符串，不改变原字符串
String.prototype.rightStrip = function(searchValue){
    if(this.endsWith(searchValue)){
        return this.substring(0, this.lastIndexOf(searchValue));
    }
    return this;
};

//返回一个去除左边的给定字符的字符串，不改变原字符串
String.prototype.leftStrip = function(searchValue){
    if(this.startsWith(searchValue)){
        return this.replace(searchValue);
    }
    return this;
};

//
// 从当前url中获取域名
// 如http://abc.com/
function get_domain_url() {
    let origin = window.location.origin;
    origin = origin.rightStrip('/');
    return origin + '/';
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

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

//
//所有ajax的请求的全局设置
//
$.ajaxSettings.beforeSend = function(xhr, settings){
    var csrftoken = getCookie('csrftoken');
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
};

//
//form 表单获取所有数据 封装方法
//
function getForm2Obj(form_node) {
    let o = {};
    let a = $(form_node).serializeArray();
    $.each(a, function () {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });

    return o;
}
