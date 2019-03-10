$(document).ready(function(){

    var WEBSOCKET_ROUTE = "/ws";

    if(window.location.protocol == "http:"){
        //localhost
        var ws = new WebSocket("ws://" + window.location.host + WEBSOCKET_ROUTE);
        }
    else if(window.location.protocol == "https:"){
        //Dataplicity
        var ws = new WebSocket("wss://" + window.location.host + WEBSOCKET_ROUTE);
        }

    ws.onopen = function(evt) {
        $("#ws-status").html("Connected");
        };

    ws.onmessage = function(evt) {
        };

    ws.onclose = function(evt) {
        $("#ws-status").html("Disconnected");
        };

    $('#slider1').change(function() {
        // this will contain a reference to the checkbox
        if (this.checked) {
            // the checkbox is now checked
            ws.send("slider1_on")
        } else {
        // the checkbox is now no longer checked
            ws.send("slider1_off")
        }
    });

    $('#slider2').change(function() {
        // this will contain a reference to the checkbox
        if (this.checked) {
            // the checkbox is now checked
            ws.send("slider2_on")
        } else {
        // the checkbox is now no longer checked
            ws.send("slider2_off")
        }
    });


    $('#slider3').change(function() {
        // this will contain a reference to the checkbox
        if (this.checked) {
            // the checkbox is now checked
            ws.send("slider3_on")
        } else {
        // the checkbox is now no longer checked
            ws.send("slider3_off")
        }
    });


    $('#slider4').change(function() {
        // this will contain a reference to the checkbox
        if (this.checked) {
            // the checkbox is now checked
            ws.send("slider4_on")
        } else {
        // the checkbox is now no longer checked
            ws.send("slider4_off")
        }
    });


    $('#slider5').change(function() {
        // this will contain a reference to the checkbox
        if (this.checked) {
            // the checkbox is now checked
            ws.send("slider5_on")
        } else {
        // the checkbox is now no longer checked
            ws.send("slider5_off")
        }
    });


    $('#slider6').change(function() {
        // this will contain a reference to the checkbox
        if (this.checked) {
            // the checkbox is now checked
            ws.send("slider6_on")
        } else {
        // the checkbox is now no longer checked
            ws.send("slider6_off")
        }
    });


    $('#slider7').change(function() {
        // this will contain a reference to the checkbox
        if (this.checked) {
            // the checkbox is now checked
            ws.send("slider7_on")
        } else {
        // the checkbox is now no longer checked
            ws.send("slider7_off")
        }
    });

    $('#slider8').change(function() {
        // this will contain a reference to the checkbox
        if (this.checked) {
            // the checkbox is now checked
            ws.send("slider8_on")
        } else {
        // the checkbox is now no longer checked
            ws.send("slider8_off")
        }
    });
});
