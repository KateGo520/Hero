$(document).ready(function () {
    $.ajax({
        url: '/study',
        success: function (res) {
            datas = res.data
            for (tr = 0; tr < datas.length; tr++) {
                str =""
                one = datas[tr]
                if (tr == 0) {
                    continue;
                } else {
                    str += "<tr class='td td_font'>"
                    for (td = 0; td < one.length; td++) {
                        if (td === 0) {
                            str += "<td class='th td_font table04_width_ID color' style='border-right: 1px solid #70C99E'>" + one[td] + "</td>"
                        } else if (td === 1) {
                            str += "<td class='td_font table04_width_IssueID'><a href='" + one[td + 4] + "' style='color: white'> " + one[td] + "</a></td>"
                        }else if (td === 2) {
                            str += "<td class='td_font table04_width_ProjectName'>" + one[td] + "</td>"
                        }else if (td === 4) {
                            str += "<td class='td_font table04_width_IssueType'>" + one[td] + "</td>"
                        } else if (td === 5) {
                            continue;
                        } else {
                            str += "<td class='td_font table04_width_FixingStrategy'>" + one[td] + "</td>"
                        }
                    }
                }
                str += '</tr>'
                $("#data02").append(str)
            }
        }
    })
})