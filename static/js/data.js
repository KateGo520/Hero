$(document).ready(function () {
    $.ajax({
        url: '/data',
        success: function (res) {
            datas = res.data
            for (tr = 1; tr < datas.length; tr++) {
                str = ""
                one = datas[tr]
                if (tr == 0) {

                    continue;
                } else {
                    str += "<tr class='td td_font'>"
                    if (tr < 30) {
                        for (td = 0; td < one.length; td++) {
                            if (td == 0) {
                                str += "<td class='th td_font color table_width_ID' style='border-right: 1px solid #70C99E'>" + one[td] + "</td>"
                            } else if (td == 1) {
                                str += "<td class='td_font table_width_ProjectName'>" + one[td] + "</td>"
                            } else if (td == 2) {
                                str += "<td class='td_font table_width_CommitID'>" + one[td] + "</td>"
                            } else if (td == 3) {
                                str += "<td class='td_font table_width_LastUpdateTime'>" + one[td] + "</td>"
                            } else if (td == 4) {
                                str += "<td class='td_font table_width_IssueID'><a href='" + one[td + 1] + "' style='color: white'> " + one[td] + "</a></td>"
                            } else if (td == 5) {
                                continue
                            } else if (td == 6) {
                                str += "<td class='td_font table_width_IssueType'>" + one[td] + "</td>"
                            }else{
                                str += "<td class='td_font table_width_IssueStatus'>" + one[td] + "<span style ='color: red'>♠</span></td>"
                            }
                        }
                    } else {
                        for (td = 0; td < one.length; td++) {
                            if (td == 0) {
                                str += "<td class='th td_font color table_width_ID' style='border-right: 1px solid #70C99E'>" + one[td] + "</td>"
                            } else if (td == 1) {
                                str += "<td class='td_font table_width_ProjectName'>" + one[td] + "</td>"
                            } else if (td == 2) {
                                str += "<td class='td_font table_width_CommitID'>" + one[td] + "</td>"
                            } else if (td == 3) {
                                str += "<td class='td_font table_width_LastUpdateTime'>" + one[td] + "</td>"
                            } else if (td == 4) {
                                str += "<td class='td_font table_width_IssueID'><a href='" + one[td + 1] + "' style='color: white'> " + one[td] + "</a></td>"
                            } else if (td == 5) {
                                continue;
                            } else if (td == 6) {
                                str += "<td class='td_font table_width_IssueType'>" + one[td] + "</td>"
                            }else {
                                str += "<td class='td_font table_width_IssueStatus'>" + one[td] + "</td>"
                            }
                        }
                    }
                }
                str += '</tr>'
                $("#data").append(str)
            }
                $("tr:odd").attr("bgColor", "#236360")
                $("tr:even").attr("bgColor", "#328E75").css({opacity:0.9})
        }
    });

    $(".top_menu li").click(function () {
        flag = $(this).index()
        if(flag == 0){
            flag = 5
        }else if(flag == 1){
            flag = 4
        }else if(flag == 2){
            flag = 3
        }else if(flag == 3){
            flag = 2
        }else if(flag == 4){
            flag = 1
        }//else if(flag == 5){
        //     flag = 2
        // }else if(flag == 6){
        //     flag = 1
        //}
        else{
            flag = 0
        }

        $(".main_content li").removeClass("aa").eq(flag).addClass("aa");

    });
    $("#start").click(function(){
             $(".head_menu").removeClass("active");
             $(".head_menu").eq(4).addClass("active");
             $(".main_content li").removeClass("aa").eq(1).addClass("aa");
        });

        $("#How").click(function(){
             $(".head_menu").removeClass("active");
             $(".head_menu").eq(0).addClass("active");
             $(".main_content li").removeClass("aa").eq(5).addClass("aa");
        });
})
