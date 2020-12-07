$(document).ready(function() {
	$(".d_buttion").click(function(){
		var $repo_name = $("#d_repo").val();
		var $repo_version = $("#d_version").val();
//		searchHistory($("#search").val());
		var $r_str = $repo_name + "@" + $repo_version;
		searchHistory($r_str);
		console.log(localStorage);
	});
	function searchHistory(search_value){
		var len=5;  //设定存储的历史记录个数
		if(search_value!=""&&
			!judgeRepeat(search_value))
		{
			insertToHistoryList(search_value,len);
			if(localStorage.length<len)//0 1 2 3 4
			{
				localStorage.setItem(localStorage.length,search_value);
			}else{
				for(var i=0;i<len;++i)
				{
					if(i==len-1)
					{
						localStorage.setItem(i,search_value);
						return;
					}
					var next_value=localStorage.getItem(i+1);
					localStorage.setItem(i,next_value);	
				}
			}
	 
		}
	}
	 
	/*如果搜索结果与本地存储相同，
	  则不行存储
	*/
	function judgeRepeat(search_value){
		var repeat_bool=false;
		for(var key in localStorage)
		{
			if(search_value==localStorage.getItem(key))
			{
				return true;
			}
		}
	}
	 
	/*将搜索结果插入到历史记录中*/
	function insertToHistoryList(search_value,len)
	{
		var str="<li>"+search_value+"</li>";
		if($(".search-history-list").children().length==0)
		{
			$(".search-history-list").append($(str));
		}else
		{
			if($(".search-history-list").children().length<len)
			{
				$(str).insertBefore($(".search-history-list li:eq(0)"));
			}else
			{
				$(".search-history-list li:last").remove();  //超过len个则移除最后一个
				$(str).insertBefore($(".search-history-list li:eq(0)"));
			}
		}
	}
	 
	 
	/*初始化历史记录列表*/
	function buildHistory(){
		for(var i=0;i<localStorage.length;++i)
		{
			
			var str="<li>"+localStorage.getItem(localStorage.length-1-i)+
				"</li>";
			$(str).appendTo($(".search-history-list"));
		}
	}
	 
	buildHistory();
	 
	/*清空历史搜索记录*/
	$(".clear-history").click(function(){
		localStorage.clear();
		$(".search-history-list").empty();
		console.log("History has been cleared");
	});

});
 
