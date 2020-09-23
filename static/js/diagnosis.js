$(document).ready(function() {

	$('#root_cause_div').height($('#root_cause_div').parent().height() - 44 - 30);
	$('#suggested_solution_div').height($('#suggested_solution_div').parent().height() - 44 - 30);
	
	$("#start_diagnosis_btn").click(function() {

        var $repo_name= $("#d_repo").val();
        var $repo_version= $("#d_version").val();
//        alert($repo_name)
//        alert($repo_version)
	    
        if ($repo_name=='') {
        	alert("Please enter the name of the project to be tested! :D");
        } else{
        	if ($repo_name=='') {
	        	alert("Please enter the version of the project to be tested! :D");
	        } else{
	        	alert('Start diagnosis!', $repo_name, $repo_version);
	        	json = {"repo_name":$repo_name,"repo_version":$repo_version}
	        	document.getElementById("d_wait").style.visibility="visible";
	        	showProblemDetails(json)
	        }
        	
        }


	});

	function showProblemDetails(json){
//	            type : "GET"
	    $.ajax({
            url : "/diagnosis",

			data : json,
            success : function (res) {
            	if (res.result == 1) {
            		alert('Please enter the correct name of the project! :D')
            	} else{
            		if (res.result == 2) {
            			alert('Please enter the correct version of the project! :D')
            		} else{
            			if (res.result ==0) {
                            document.getElementById("d_wait").style.visibility="hidden";
//                            alert(res.data)
                            $div = $('#dependency-model')
                            temp = '<span>' + res.dep_tree + '</span>'
                            $div.append(temp)
                            $rootcause_div = $('#root_cause_div')
                            temp = '<span>' + res.issues + '</span>'
                            $rootcause_div.append(temp)
                            // down_msg  suggested_solution_div
                            $solution_div = $('#root_cause_div')
                            temp = '<span>' + res.down_msg + '</span>'
                            $solution_div.append(temp)
            		    }
            		}
            	}
            	
            	

            }
        })
	}
	
});