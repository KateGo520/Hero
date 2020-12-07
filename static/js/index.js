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
	//table页显示后，调用下方js (table页面高度，主要方法就是页面内容加载后，使用计算tbody高度)
	$('#main_div').children('ul').css('height','100%');
	$('#main_div').children('ul').find('li.aa').css('height','100%');
	$('#main_div').children('ul').find('li.aa').find('table').css('height','0');
	$('#main_div').children('ul').find('li.aa').find('table').each(function(){
		var that = this;
		var captionHeight = 0;
		if ($(this).find('caption').length > 0){
			$(this).find('caption').each(function(){
				captionHeight += $(this).outerHeight();
			});
		}
		$(that).find('tbody').height(0.9*(($(that).parent().height() - $(that).find('thead').height() - captionHeight)));
	});
});