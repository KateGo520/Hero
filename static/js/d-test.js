$(document).ready(function() {
	var help = document.getElementById("d-help-win");
	$("#d-help").click(function() {
		help.style.display = "block";
	});
	$("#d-help-colse").click(function() {
		help.style.display = "none";
	});
	// 拖拽
	help.onmousedown = function(ev) {
		var maxLeft = document.documentElement.clientWidth - help.offsetWidth;
		var maxTop = document.documentElement.clientHeight - help.offsetHeight;
		var e = ev || window.event;
		var X = e.clientX - help.offsetLeft;
		var Y = e.clientY - help.offsetTop;

		//只针对IE浏览器
		if (help.setCapture) {
			help.setCapture();
		}
		document.onmousemove = function(ev) {
			var e = ev || window.event;

			var left = e.clientX - X;
			var top = e.clientY - Y;

			//限定范围
			if (left < 0) {
				left = 0;
			}
			if (top < 0) {
				top = 0;
			}
			if (top > maxTop) {
				top = maxTop;
			}
			if (left > maxLeft) {
				left = maxLeft;
			}
			help.style.left = left + 'px';
			help.style.top = top + 'px';
		};
		document.onmouseup = function() {
			document.onmousemove = null;
			document.onmouseup = null;
			//取消捕获事件
			if (help.releaseCapture) {
				help.releaseCapture();
			}
		};
	};
	
//	$(".search-btn").click(function(){
//		searchHistory($("#search").val());
//		console.log(localStorage);
//	});
});