$(document).ready(function () {
    $(".contact").mouseover(function () {
        $(".reproduction").show("slow");
        $(".contact").mouseout(function () {
            $(".reproduction").hide("slow");
        });
    });
})