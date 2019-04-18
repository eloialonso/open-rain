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

    /* Function called when the socket receives a message */
    ws.onmessage = function(evt) {
        // Parse input dictionary
        var messageDict = JSON.parse(evt.data);

        // Sensor measure
        if (messageDict.type == "sensor_measure") {
            $("#measure_value").html(messageDict.value + " L")
        }
    };

    ws.onclose = function(evt) {
        $("#ws-status").html("Disconnected");
    };

    /* Called when touching a slider (to switch relay state) */
    $('.relay').change(function() {

        if (this.checked) {
            ws.send(this.id + '_on');
        } else {
            ws.send(this.id + '_off');
        }

    });


// var myVar = setInterval(myTimer, 1000);

// function myTimer() {
//   var d = new Date();
//   var t = d.toLocaleTimeString();
//   document.getElementById("demo").innerHTML = t;
// }

// function myStopFunction() {
//   clearInterval(myVar);
// }



    /* Called when clicking on the measure button */
    var measureInterval = null;
    var measureButton = document.getElementById("button_measure");
    measureButton.addEventListener("click", StartMeasure);

    function StartMeasure(){
        measureInterval = setInterval(function(){ws.send("do_measure");}, 1500);
        measureButton.removeEventListener("click", StartMeasure);
        measureButton.addEventListener("click", StopMeasure);
        measureButton.value = "Stop";
    }

    function StopMeasure(){
        clearInterval(measureInterval);
        measureButton.removeEventListener("click", StopMeasure);
        measureButton.addEventListener("click", StartMeasure);
        measureButton.value = "Mesurer";
    }

});
