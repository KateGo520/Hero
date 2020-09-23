$(document).ready(function() {

	$('.about_module').off('click').on('click', function(){
		$('.about_module').removeClass('about_active');
		$(this).addClass('about_active');
	});
	
});