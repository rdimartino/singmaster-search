var stream_source;
var viz_data = [];

function open_stream() {
    console.log("Opening status stream")
    stream_source = new EventSource("/status_stream");
    stream_source.addEventListener("close", close_stream, false);
    stream_source.addEventListener("progress", update_progress, false);
    stream_source.addEventListener("viz", function(e) {
        var data = JSON.parse(e.data);
        viz_data.push(data);
    });

    stream_source.onmessage = function(e) {
        var status = JSON.parse(e.data);
        terminal_status(status.msg);
    };
    stream_source.onerror = function(e) {
        console.log('Error: ' + e.data);
    };
};

function terminal_status(msg) {
    $("#terminal > pre").append(msg + "\n");
    $("#terminal").animate({
        scrollTop: $("#terminal")[0].scrollHeight
    }, 0);
};

function close_stream() {
    console.log("Closing status stream");
    stream_source.close();
};

function update_progress(e) {
    var progress = JSON.parse(e.data);
    $(".progress-bar").prop("aria-valuenow", progress.p);
    $(".progress-bar").prop("style", "width:" + progress.p + "%");
    $(".progress-bar > span").html(progress.item + "-" + progress.p.toFixed(1) + "%");
};

//$(".btn").on("click", function() {
//    if (!$(this).hasClass("disabled")) {
//        set_buttons({
//            "start": false,
//            "stop": false,
//            "reset": false
//        });
//        if ($(this).is("#start")) {
//            if (stream_source.readyState == 2) {
//                open_stream();
//            };
//        };
//        if ($(this).is("#stop")) {
//            $("#start").html("Resume");
//            //            close_stream();
//        };
//        if ($(this).is("#reset")) {
////            if(!confirm_modal()){
////                return
////            }
//
//            $("#start").html("Start");
//            $("#terminal > pre").html("");
//        };
//        $.get("/" + $(this).attr("id"), function(response) {
//            console.log(response.log);
//            set_buttons(response.buttons);
//        });
//        alert_box();
//    };
//});


function set_buttons(button_dict) {
    if (button_dict.start) {
        $("#start").removeClass("disabled");
    } else {
        $("#start").addClass("disabled");
    };

    if (button_dict.stop) {
        $("#stop").removeClass("disabled");
    } else {
        $("#stop").addClass("disabled");
    };

    if (button_dict.reset) {
        $("#reset").removeClass("disabled");
    } else {
        $("#reset").addClass("disabled");
    };
};


$(document).ready(function() {
    console.log("Document is ready!");
    $.ajax({
        url: "/terminal",
        //                async: false,
        beforeSend: function() {
            $("#terminal > pre").html("");
//            make a spinner
//            set_buttons({
//                "start": false,
//                "stop": false,
//                "reset": false
//            })
        },
        success: function(data) {
            var lines = data.logs;
            if (lines) {
                for (var i = 0; i < lines.length; i++) {
                    terminal_status(lines[i]);
                };
            };
        },
        complete: function() {
            alert("derp!");
        }
    });
    open_stream();
});

function alert_box () {
    $("#alert_holder").append(
    "<div class=\"alert alert-success fade in\">" + "\n" +
        "<a href=\"#\" class=\"close\" data-dismiss=\"alert\" aria-label=\"close\">&times;</a>" + "\n" +
        "<strong>Success Two!</strong> Indicates another successful or positive action." + "\n" +
    "</div>" +  "\n"
    );
    alertTimeout(2000);
};

function alertTimeout(wait){
    setTimeout(function(){
        $('#alert_holder').children('.alert:first-child').remove();
    }, wait);
};

function confirm_modal() {
    $("#reset_modal").modal()
};

$(".btn").on("click", function() {
    alert("click");
    event.preventDefault();
    return false;
});
