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
});

function ShowAToast(info) {
    document.getElementById("alertinfo").innerHTML = info
    new bootstrap.Toast(document.getElementById('AlertliveToast')).show()
};

function ShowSToast(info) {
    document.getElementById("sinfo").innerHTML = info
    new bootstrap.Toast(document.getElementById('SuccessliveToast')).show()
};

function qrcodeUrl(code) {
    return 'https://api.qrserver.com/v1/create-qr-code/?data=' + window.location.href + '?code=' + code
};

function get_share_files(e, data) {
    var f = document.getElementById(e);
    data.forEach(item => { 
        const code = item.code;
        const img_html = qrcodeUrl(code);
        html = '<div class="list-group-item py-3">\n' +
        '    <div class="row align-items-center">\n' +
        '        <div class="col">\n' +
        '            <div class="card-body">\n' +
        '                取件码: <b class="g-font-size-16">' + code + '</b>\n' +
        '                <div class="text-muted">文件名: ' + item.name + '</div>\n' +
        '            </div>\n' +
        '        </div>\n' +
        '        <div class="col-auto">\n' +
        '            <img src="' + img_html + '" class="rounded-start" alt="二维码" width="80" height="80">\n' +
        '        </div>\n' +
        '  </div>\n' +
        '</div>'
        f.innerHTML += html
    })
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
            $("#rece-empty").addClass("d-none");
            $("#rece-list-items").removeClass("d-none");
            get_rece_files("rece-list-items", data)
            new bootstrap.Offcanvas('#filesBox').show()
        },
        error: function (data) {
            var info = data.responseJSON.detail;
            ShowAToast(info);
        }
    });
}
