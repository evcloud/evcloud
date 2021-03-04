$(function(){
    $('#form-add').ajaxForm(function(data){ 
        if(data.ok === true){
            $('.remove').remove()
            var macips = data.macips
            var str = ''
            for(var i = 0; i < macips.length; i++){
                str += '<tr class="remove"><th>v_' + macips[i][0].replace('.', '_') + '</th><th>' + macips[i][0] + '</th><th>' + macips[i][1] + '</th></tr>'
            }
            $('#table-add').append(str)
            if($('#flag').val() === 'true'){
                alert(data.msg)
            }
        }else{
            alert(data.msg)
        }
    });

    $('#generate').click(function(){
        $('#flag').val('false')
    })

    $('#import').click(function(){
        $('#flag').val('true')
    })

});