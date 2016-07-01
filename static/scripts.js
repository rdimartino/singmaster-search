var DEBUG_MODE=false

function debugLog(obj) {
    if (DEBUG_MODE) {
        console.log(obj);
    }
}

$(document).ready(function() {
    setButtons();
    $('.nav-tabs a[href="#viz01"]').tab("show");
    $.ajax({
        url: "./reload",
        beforeSend: function() {
            $("#terminal > pre").html("");
            $(`<div class="spinner"></div>`).appendTo($("#terminal").css("position", "relative"));
            $(`<div class="spinner"></div>`).appendTo($("#viz01").css("position", "relative"));
            $(`<div class="spinner"></div>`).appendTo($("#viz02").css("position", "relative"));
        },
        success: function(data) {
            var lines = data.logs;
            var centers = data.viz;
            if (lines) {
                putLogLines(lines,"yes");
            };
            if (centers) {
                viz_data = centers.map(cleanData);
            };
            viz_refresh();
        },
        complete: function() {
            $(".spinner").parent().css("position", "");
            $(".spinner").remove();
        }
    });
    openSteam();
});


function setButtons(buttonDict) {
    buttonDict = (typeof buttonDict === "object") ? buttonDict : {}
    $(".js-control").each(function(){
        var id = $(this).attr("id");
        var state;
        var label;
        if(buttonDict.hasOwnProperty(id)) {
            if(buttonDict[id].hasOwnProperty("state")) {
                $(this).data("btn-state", buttonDict[id]["state"]);
            };
            if(buttonDict[id].hasOwnProperty("label")) {
                $(this).text(buttonDict[id]["label"]);
            };
        };
        var state = ($(this).data("btn-state").toString().toLowerCase() === "true");
        var label = $.trim($(this).text());
        if(state) {
            $(this).removeClass("disabled");
        } else {
            $(this).addClass("disabled");
        };
    });
};

function clickButton(btn) {
    var link = btn.attr("href");
    setButtons({"start-btn": {"state": false},
                "stop-btn": {"state": false},
                "reset-btn": {"state": false}});
    if (btn.is("#start-btn")) {
        if (stream_source.readyState == 2) {
            openSteam();
        };
    } else if (btn.is("#stop-btn")) {
        $("#start-btn").html("Resume");
    } else if (btn.is("#reset-btn")) {
        $("#start-btn").html("Start");
        $("#terminal > pre").html("");
        updateProgress({data:'{"item":0, "p":0}'});
    } else {
        console.log("Button exception!");
    };
    $.get(link, function(response) {
            console.log(response.log);
            setButtons(response.buttons);
            alertBox(response.alert);
    });
};

function setModalButton(btn) {
    $("#dataConfirmOK").unbind("click");
    $("#dataConfirmOK").on("click", function (event) {
        event.preventDefault();
        clickButton(btn);
    });
};

function alertBox(msg) {
    if(!msg) {
        msg = {"title": "Info: ",
               "body": "A button was pressed.",
               "flag": 1};
    };
    var msgClass
    if (msg.flag==1) {
        msgClass = "alert-info";
    } else if (msg.flag==10) {
        msgClass = "alert-primary";
    } else if (msg.flag==100) {
        msgClass = "alert-success";
    } else if (msg.flag==-10) {
        msgClass = "alert-warning";
    } else if (msg.flag==-100) {
        msgClass = "alert-danger";
    } else {
        msgClass = "";
    }
    $("#alert_holder").append(
`
<div class="alert fade in ` + msgClass + `">
    <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>
    <strong>`+ msg.title +`</strong>`+ msg.body + `
</div>
`
    );
    alertTimeout(5000);
};

function alertTimeout(wait){
    setTimeout(function(){
        $('#alert_holder').children('.alert:first-child').remove();
    }, wait);
};

$(".js-confirm").on("click", function(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
    setModalButton($(this));
    $("#dataConfirmModal").find(".modal-body").text($(this).data("modal-msg"));
    $("#dataConfirmModal").modal({show:true});
});

$(".js-control").on("click", function(event) {
    event.preventDefault();
    clickButton($(this));
});

$(".js-nav-panel").on("click", function(event) {
    var href = $(this).data("target");
    $('.nav-tabs a[href="'+ $(this).data("target") +'"]').tab("show");
});

$(".dropdown").on("show.bs.dropdown", function(event){
    $(".dropdown-menu > li").removeClass("active");
});

$("#about-more").on("click", (function(event) {
    var count = 0;
    var txt = "Read less";

    return function(e) {
        count++;
        if (count == 2) {
            txt = "Read more again...";
            count = 0;
        } else {
            txt = "Read less";
        };
        $(this).blur();
        $(this).text(txt);
    };
})());

var stream_source;
var viz_data = [{x: 2, y:0.0001, m:1}];

function openSteam() {
    console.log("Opening status stream")
    stream_source = new EventSource("./dataStream");
    stream_source.addEventListener("close", closeStream, false);
    stream_source.addEventListener("progress", updateProgress, false);
    stream_source.addEventListener("data", function(e) {
        var data = JSON.parse(e.data);
        viz_data.push(cleanData(data));
        viz_refresh();
        //console.log(data);
    });

    stream_source.onmessage = function(e) {
        var status = JSON.parse(e.data);
        //console.log(status);
        //terminalStatus(status);
        putLogLines(status,"manual");
    };
    stream_source.onerror = function(e) {
        console.log('Error: server sent events error');
    };
};

function closeStream() {
    console.log("Closing status stream");
    stream_source.close();
    viz_data = [{x: 2, y:0.0001, m:1}];
};

function terminalStatus(status) {
    var keepScrolling = ($("#terminal")[0].scrollHeight - $("#terminal")[0].clientHeight <= $("#terminal").scrollTop()+5);
    $("#terminal > pre").append(formatLogLine(status));
    if (keepScrolling) {
       $("#terminal").scrollTop($("#terminal")[0].scrollHeight);
    }
    console.log("console line");
};

function putLogLines(lines, scroll) {
    var keepScrolling;
    if (scroll=="yes") {
        keepScrolling = true;
    } else if (scroll=="manual") {
        keepScrolling = ($("#terminal")[0].scrollHeight - $("#terminal")[0].clientHeight <= $("#terminal").scrollTop()+50);
    } else {
        keepScrolling = false;
    }
    if (Array.isArray(lines)) {
        $("#terminal > pre").append(lines.map(formatLogLine).join(""));
    } else {
        $("#terminal > pre").append(formatLogLine(lines));
    }
    if (keepScrolling) {
       $("#terminal").scrollTop($("#terminal")[0].scrollHeight);
    }
}

function formatLogLine(line) {
    var msgClass;
    var paddedHeader;
    if (line.flag==1) {
        msgClass = "bg-info";
    } else if (line.flag==10) {
        msgClass = "bg-primary";
    } else if (line.flag==100) {
        msgClass = "bg-success";
    } else if (line.flag==-10) {
        msgClass = "bg-warning";
    } else if (line.flag==-100) {
        msgClass = "bg-danger";
    } else {
        msgClass = "";
    }
    paddedHeader = ("     ".slice(0,Math.floor((10.0-line.header)/2.0))+line.header+"     ".slice(0,Math.ceil((10.0-line.header)/2.0))).toUpperCase();
    return "[" + line.ts + "] <span class=\"" + msgClass + "\">[" + paddedHeader + "]</span> == " + line.message + "\n";
};

function updateProgress(e) {
    var progress = JSON.parse(e.data);
    progressPercent = progress.p*100
    $(".progress-bar").prop("aria-valuenow", progressPercent);
    $(".progress-bar").prop("style", "width:" + progressPercent + "%");
    $(".progress-bar > span").html("Center: " + progress.center + " - (" + progressPercent.toFixed(1) + "% complete)");
};
