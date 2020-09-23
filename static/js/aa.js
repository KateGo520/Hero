$(document).ready(function() {
	$(".left_menu li").click(function() {
		$(".about_li li").removeClass("bb").eq($(this).index()).addClass("bb");
	});
})
