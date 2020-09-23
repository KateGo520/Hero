$(document).ready(function() {
	
	$('#main_div').height($(window).height() - 65);
	$('#body_div').particleground({
	  dotColor: '#657b7c',
	  lineColor: '#657b7c'
	});
	
	// $('#h2w_div').off('click').on('click', function(){
	// 	loadAbout();
	// });
	//
	// $('#diagnosis_div').off('click').on('click', function(){
	// 	loadDiagnosis();
	// })
	
	var timer = setInterval(function(){
	    loopClickUI();
	},80);
	
	$('.head_menu').off('click').on('click', function(){
		$('.head_menu').removeClass('active');
		$(this).addClass('active');

	// 	var moduleId = $(this).attr('id');
	// 	if ('About' == moduleId){
	// 		loadAbout();
	// 	} else if ('Demo' == moduleId){
	// 		loadDemo();
	// 	} else if ('Ecosystem' == moduleId){
	// 		loadEcosystem();
	// 	} else if ('BenchmarkDataset' == moduleId){
	// 		loadBenchmarkDataset();
	// 	} else if ('EmpiricalStudyDataset' == moduleId){
	// 		loadEmpiricalStudyDataset();
	// 	} else if ('Issuereport' == moduleId){
	// 		loadIssuereport();
	// 	} else if ('Diagnosis' == moduleId){
	// 		loadDiagnosis();
	// 	}
	});
	
	$('#logo_img').off('click').on('click', function(){
		
	});
	
	// function loadAbout(){
	// 	$('#main_div').append(str);
	// }
	//
	// function loadDemo(){
	// 	alert('load Demo!')
	// }
	//
	// function loadEcosystem(){
	// 	alert('load Ecosystem!')
	// }
	//
	// function loadBenchmarkDataset(){
	// 	alert('load Benchmark Dataset!')
	// }
	//
	// function loadEmpiricalStudyDataset(){
	// 	alert('load Empirical Study Dataset!')
	// }
	//
	// function loadIssuereport(){
	// 	alert('load Issue report!')
	// }
	//
	// function loadDiagnosis(){
	// 	$('#main_div').load('biz/diagnosis.html');
	// }
	
	function loopClickUI(){
		var thisImg = $('#click_div .click_active');
		var nextImg = thisImg.next();
		if (nextImg.length == 0){
			nextImg = $('#click_div img').first();
		}
		thisImg.removeClass('click_active');
		nextImg.addClass('click_active');
	}
});