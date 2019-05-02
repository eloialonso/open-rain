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

    /* Function called when the socket is opened. */
    ws.onopen = function(evt) {
        $("#ws-status").html("Connected");
    };

    /* Function called when the socket is closed. */
    ws.onclose = function(evt) {
        $("#ws-status").html("Disconnected");
    };

    /* Function called when the socket receives a message */
    ws.onmessage = function(evt) {
        // Parse input dictionary
        var messageDict = JSON.parse(evt.data);

        // Sensor measure: display the received value
        if (messageDict.type == "sensor_measure") {
            $("#measure_value").html(messageDict.value + " L")
        }
    };

    /* When a slider is modified, send a message in the socket. */
    $('.relay').change(function() {

        if (this.checked) {
            ws.send(this.id + '_on');
        } else {
            ws.send(this.id + '_off');
        }

    });

    /* Measure button */
    var measureInterval = null;
    var measureButton = document.getElementById("button_measure");
    measureButton.addEventListener("click", startMeasure);

    function startMeasure(){
        measureInterval = setInterval(function(){ws.send("do_measure");}, 1500);
        measureButton.removeEventListener("click", startMeasure);
        measureButton.addEventListener("click", stopMeasure);
        measureButton.value = "Stop";
    }

    function stopMeasure(){
        clearInterval(measureInterval);
        measureButton.removeEventListener("click", stopMeasure);
        measureButton.addEventListener("click", startMeasure);
        measureButton.value = "Measure";
    }

});
