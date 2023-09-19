;'use strict';
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

//API域名
let DOMAIN_NAME = get_domain_url();

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

/**
 * 拼接params对象为url参数字符串
 * @param {Object} obj - 待拼接的对象
 * @returns {string} - 拼接成的请求字符串
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

// 将 Date 转化为指定格式的String
// 月(M)、日(d)、小时(H)、分(m)、秒(s)、季度(q) 可以用 1-2 个占位符，
// 年(y)可以用 1-4 个占位符，毫秒(S)只能用 1 个占位符(是 1-3 位的数字)
// 例子：
// dateFormat("yyyy-MM-dd HH:mm:ss.S", date) ==> 2006-07-02 08:09:04.423
// dateFormat("yyyy-M-d H:m:s.S", date)      ==> 2006-7-2 8:9:4.18
function dateFormat(fmt, date) {
    let ret;
    let opt = {
        "y+": date.getFullYear().toString(),
        "M+": (date.getMonth() + 1).toString(),
        "d+": date.getDate().toString(),
        "H+": date.getHours().toString(),
        "m+": date.getMinutes().toString(),
        "s+": date.getSeconds().toString(),
        "S+": date.getMilliseconds().toString()
    };
    for (let k in opt) {
        ret = new RegExp("(" + k + ")").exec(fmt);
        if (ret) {
            fmt = fmt.replace(ret[1], (ret[1].length === 1) ? (opt[k]) : (opt[k].padStart(ret[1].length, "0")))
        }
    }
    return fmt;
}

// iso格式时间转本地时间
// "'2020-03-04T09:09:49.032064+07:00'" ==> ""2020-03-04 10:09:49""
function isoTimeToLocal(isoTime) {
    let lTime;
    if (!isoTime){
        return isoTime;
    }
    try{
        let d = new Date(isoTime);
        lTime = dateFormat("yyyy-MM-dd HH:mm:ss", d);
    }catch (e) {
        lTime = isoTime;
    }
    return lTime;
}

 /**
  * 自定义Loading插件，来自网络
  * @param {Object} config
  * {
  * content[加载显示文本]
  * }
  * @param {String} config
  * 加载显示文本
  * @refer 依赖 JQuery-1.9.1及以上、Bootstrap-3.3.7及以上
  * @return {KZ_Loading} 对象实例
  */
 function KZ_Loading(config) {
     if (this instanceof KZ_Loading) {
         const domTemplate = '<div class="modal fade kz-loading" data-kzid="@@KZ_Loadin_ID@@" backdrop="static" keyboard="false"><div style="width: 200px;height:20px; z-index: 20000; position: absolute; text-align: center; left: 50%; top: 50%;margin-left:-100px;margin-top:-10px"> <div class="spinner-border text-primary" role="status"> <span class="sr-only">Loading...</span> </div><h5 style="color: white">@@KZ_Loading_Text@@</h5></div></div>';
         this.config = {
             content: 'loading...'
         };
         if (config != null) {
             if (typeof config === 'string') {
                 this.config = Object.assign(this.config, {
                     content: config
                 });
             } else if (typeof config === 'object') {
                 this.config = Object.assign(this.config, config);
             }
         }
         this.id = new Date().getTime().toString();
         this.state = 'hide';

         /*显示 */
         this.show = function () {
             $('.kz-loading[data-kzid=' + this.id + ']').modal({
                 backdrop: 'static',
                 keyboard: false
             });
             this.state = 'show';
         };
         /*隐藏 */
         this.hide = function (callback) {
             $('.kz-loading[data-kzid=' + this.id + ']').modal('hide');
             this.state = 'hide';
             if (callback) {
                 callback();
             }
         };
         /*销毁dom */
         this.destroy = function () {
             var that = this;
             this.hide(function () {
                 var node = $('.kz-loading[data-kzid=' + that.id + ']');
                 node.next().remove();
                 node.remove();
                 that.show = function () {
                     throw new Error('对象已销毁！');
                 };
                 that.hide = function () {};
                 that.destroy = function () {};
             });
         }

         var domHtml = domTemplate.replace('@@KZ_Loadin_ID@@', this.id).replace('@@KZ_Loading_Text@@', this.config.content);
         $('body').append(domHtml);
     } else {
         return new KZ_Loading(config);
     }
 }