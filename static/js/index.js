$(function () {
    var elem = $("#form");
    var inputs = elem.find("input");
    var len = inputs.length;
    inputs.each(function (index, item) {
        var $item = $(item);
        $item.on('focus', function () {
            if ($(this).val() != '') {
                $(this).select();
            }
            elem.addClass('focus');
            $(this).addClass('focus');
        });
        $item.on('blur', function () {
            $(this).removeClass('focus');
            elem.removeAttr('focus');
        });
        $item.on("keyup", function (e) {
            var thisinput = $(this);
            var v = $(this).val();
            // 输入↓或→键自动跳到下一个输入框内
            if ((e.keyCode == 39 || e.keyCode == 40) && index < len - 1) {
                inputs.eq(index + 1).focus();
            }
            // 输入↓或→键自动跳到上一个输入框内
            else if ((e.keyCode == 38 || e.keyCode == 37) && index != 0) {
                inputs.eq(index - 1).focus();
            } // 输入3个字符自动跳到下一个输入框内
            else if (v.length == 1 && index < len - 1) {
                inputs.eq(index + 1).focus();
            }
            // 删除的时候，一个输入框没有了字符，自动跳回上一个输入框
            else if (v == "" && e.keyCode == 8 && index != 0) {
                inputs.eq(index - 1).focus();
            }
        })
    })
    $("input[name^='c']").bind('keyup', function () {
        var info = $("#c1").val() + $("#c2").val() + $("#c3").val() + $("#c4").val() + $("#c5").val();
        if (info.length == 5) {
            post_form(info);

        }
    });
    //监听modal事件
    const myModalEl = document.getElementById('modal-upload')
    myModalEl.addEventListener('hidden.bs.modal', event => {
        $('#upload')[0].reset();
        document.querySelector('.needs-validation').classList.remove('was-validated')
    })
    myModalEl.addEventListener('shown.bs.modal', event => {
        var value = document.querySelector("input[type='radio']:checked").value;
        if (value == "1") {
            $("#post-text").attr("hidden", "hidden");
            $("#post-file").removeAttr("hidden");
        }
    })
    // var myform = document.querySelector('.needs-validation');
    // myform.addEventListener('submit', event => {
    //     if (!myform.checkValidity()) {
    //         event.preventDefault()
    //         event.stopPropagation()
    //     }
    //     myform.classList.add('was-validated')
    //     }, false)
});

function qrcodeUrl(code) {
    return 'https://api.qrserver.com/v1/create-qr-code/?data=' + window.location.href + '?code=' + code
};

function get_upload_files(e, data) {
    var code = data.code;
    var img_html = qrcodeUrl(code);
    html = '<div class="card py-3">\n' +
        '    <div class="row row-0">\n' +
        '        <div class="col">\n' +
        '            <div class="card-body">\n' +
        '                取件码: <b class="g-font-size-16">' + data.code + '</b>\n' +
        '                <div class="text-muted">文件名: ' + data.name + '</div>\n' +
        '            </div>\n' +
        '        </div>\n' +
        '        <div class="col-auto col-md-3">\n' +
        '            <img src="' + img_html + '" class="rounded-start" alt="二维码" width="80" height="80">\n' +
        '        </div>\n' +
        '  </div>\n' +
        '</div>'
    var f = document.getElementById(e);
    f.innerHTML += html

};

function get_rece_files(e, data) {
    var code = data.code;
    if (data.type == "text") {
        var link = '<div class="card border-0">\n' +
            '  <div class="card-body">\n' + '<code>' +
            '    <p>' + data.text + '</p>\n' + '</code>' +
            '  </div>\n' +
            '</div>'
    } else {
        var link = '<p>链 接: <a href="' + data.text + '"  target="_blank" type="primary">下载</a></p>'
    }
    html = '<div class="row">\n' +
        '  <div class="col">\n' +
        '    <div class="text-truncate">\n' +
        '      取件码: <strong>' + code + '</strong>\n' +
        '    </div>\n' +
        '    <div class="text-muted">文件名: <strong>' + data.name + '</strong></div>\n' + link
    '    <h2 class="fs-5">Popover in a modal</h2>' +
        '  </div>\n' +
        '</div>'
    var f = document.getElementById(e);
    f.innerHTML += html
    const myModal = new bootstrap.Modal('#modal-receive-files')
    myModal.show(document.getElementById("modal-receive-files"))


};

function post_form(e) {
    $("input[name^='c']").prop('disabled', true);
    var url = "/api/?code=" + e
    $.ajax({
        type: "post",
        url: url,
        data: {},
        complete: function (data) {
            $("input[name^='c']").val("");
            $("input[name^='c']").prop('disabled', false);
            $("#c1").focus();
        },
        success: function (data) {
            ShowSToast(data.detail);
            $("#rece-empty").addClass("d-none");
            $("#rece-list-items").removeClass("d-none");
            get_rece_files("rece-list-items", data.data)
        },
        error: function (data) {
            var info = data.responseJSON.detail;
            ShowAToast(info);
        }
    });
}

function ShowToast(info, e, k) {
    document.getElementById(e).innerHTML = info || 'error'
    new bootstrap.Toast(document.getElementById(k)).show()
}