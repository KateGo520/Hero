$(document).ready(function () {
    $.ajax({
        url: '/GT',
        success: function (res) {
            datas = res.data
            for (tr = 0; tr < datas.length; tr++) {
                str = ""
                one = datas[tr]
                if (tr == 0) {
                    continue;
                } else {
                    str += "<tr class='td td_font'>"
                    if(tr == 9 || tr == 22){
                        for (td = 0; td < one.length; td++) {
                            if (td === 0) {
                                str += "<td class='th td_font table03_width_ID color' style='border-right: 1px solid #70C99E'>" + one[td] + "</td>"
                            } else if (td === 1) {
                                str += "<td class='td_font text_background table03_width_IssueID'><a href='" + one[td + 4] + "' style='color: black'> " + one[td] + "</a></td>"
                            } else if (td === 2) {
                                str += "<td class='td_font table03_width_ProjectName'>" + one[td] + "</td>"
                            } else if (td === 3) {
                                str += "<td class='td_font table03_width_DetectedVersion'>" + one[td] + "</td>"
                            } else if (td === 5) {
                                continue
                            } else {
                                str += "<td class='td_font table03_width_IssueType'>" + one[td] + "</td>"
                            }
                        }
                    }else{
                       for (td = 0; td < one.length; td++) {
                            if (td === 0) {
                                str += "<td class='th td_font table03_width_ID color' style='border-right: 1px solid #70C99E'>" + one[td] + "</td>"
                            } else if (td === 1) {
                                str += "<td class='td_font table03_width_IssueID'><a href='" + one[td + 4] + "' style='color: white'> " + one[td] + "</a></td>"
                            } else if (td === 2) {
                                str += "<td class='td_font table03_width_ProjectName'>" + one[td] + "</td>"
                            } else if (td === 3) {
                                str += "<td class='td_font table03_width_DetectedVersion'>" + one[td] + "</td>"
                            } else if (td === 5) {
                                continue
                            } else {
                                str += "<td class='td_font table03_width_IssueType'>" + one[td] + "</td>"
                            }
                        }
                    }
                }
                str += '</tr>'
                $("#data03").append(str)
            }
        }
    })
})