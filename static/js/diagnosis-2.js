$(document).ready(function() {
	

	$('#root_cause_div').height($('#root_cause_div').parent().height() - 44 - 30);
	$('#suggested_solution_div').height($('#suggested_solution_div').parent().height() - 44 - 30);
	
	$("#start_diagnosis_btn").click(function() {

        var $repo_name= $("#d_repo").val();
        var $repo_version= $("#d_version").val();
        alert($repo_name)
//        alert($repo_name)
//        alert($repo_version)
	    
        if ($repo_name=='') {
        	alert("Please enter the name of the project to be tested! :D");
        } else{
        	if ($repo_name=='') {
	        	alert("Please enter the version of the project to be tested! :D");
	        } else{
	        	alert('Start diagnosis!', $repo_name, $repo_version);
//	        	json = {"repo_name":$repo_name,"repo_version":$repo_version};
	        	document.getElementById("d_wait").style.visibility="visible";
	        	showProblemDetails({"repo_name":$repo_name,"repo_version":$repo_version})
	        }	
        }
	});
	
	function draw(data){
        var graph = data2Graph(data);
        drawGraph(graph);
    }

    function data2Graph(data) {
        alert(data[0])
        var categories = [{
        				id: 0,
            			name: 'Repo in GOPATH',
            		},
                    {
        				id: 1,
            			name: 'Repo in Go Modules',
            		}, 
            		{
            			id: 2,
            			name: 'Client repo',
            		}, 
            		{
            			id: 3,
            			name: 'Depending on',
            		}];
        var graph = {};
        var vertices = {};
        var links = [];
        for (var i = 0; i < data.length; i++) {
        	var dep_msg = eval("(" + data[i] + ")");
            var d = String(dep_msg['d_r']);
//          alert(d)
            vertices[d] = String(dep_msg['d_m']);
            var u = String(dep_msg['u_r']);
            vertices[u] = String(dep_msg['u_m']);
//          var v = data[i][2];
//          vertices[s] = s;
//          vertices[t] = t;
            links.push({'source' : d, 'target' : u});  
//          , 'value' : v
        }
//      alert(vertices)
        var nodes = [];
//  graph.nodes.forEach(function (node) {
//      node.itemStyle = null;
//      node.symbolSize = 10;
//      node.value = node.symbolSize;
//      node.category = node.attributes.modularity_class;
//      // Use random x, y
//      node.x = node.y = null;
//      node.draggable = true;
//  });
        $.each(vertices, function(k, v) {
//      	alert(k);
//      	alert(v);
        	var $color_json = {
				"0" : "#548235",
				"1" : "#ED7D31",
				"2" : "#c00000",
				"3" : "#c00000"
			};
			var $color = $color_json[v];
//      	alert($color_json[0]);
//      	alert(k)
//      	alert(v)
        	var $size = [7, 7];
        	var $name = k;
        	var $id = 0;
        	var $dm = 'GOPATH';
        	var $category = $id;
        	if (v == "1") {
        		$id = 1;
        		$size = [8.6, 8.6];
        		$dm = 'Go Modules';
        		$category = $id;
//      		$name = k + '[Go Modules]'
        	}
        	if (v == "2") {
        		$id = 2;
        		$size = [8.6, 8.6];
        		$category = $id;
//      		$name = k + '[GOPATH]'

        	}
        	if (v == "3") {
        		$id = 2;
        		$size = [8.6, 8.6];
        		$dm = 'Go Modules';
        		$category = $id;
//      		$name = k + '[Go Modules]'
        	}
        	
//      	alert('$category');
//      	alert($category);
            var $node = {id: $id,
            			name: $name,
            			value: $dm,
            			category: $category,
            			draggable: true,                // 节点是否可拖拽，只在使用力引导布局的时候有用。
	            		symbolSize: $size,         // 关系图节点标记的大小，可以设置成诸如 10 这样单一的数字，也可以用数组分开表示宽和高，例如 [20, 10] 表示标记宽为20，高为10。
	            		itemStyle: {
	            			color: $color				// 关系图节点标记的颜色
	            		},
	            		attributes: { 
	            			modularity_class: $id 
            			}
            };

		    if(nodes.indexOf($node)==-1){
		        nodes.push($node);
		    }
            
        });
        graph['links'] = links;
        graph['data'] = nodes;
        graph['categories'] = categories;
        return graph;
    }

    function drawGraph(graph) {
        var myChart = echarts.init(document.getElementById("dependency-model"));
//      var categories = graph.categories;
        var $legend = [{
        				id: 0,
            			name: 'Repo in GOPATH',
            			icon: 'circle',
            			color: '#548235'
            		},
                    {
        				id: 1,
            			name: 'Repo in Go Modules',
            			icon: 'circle',
            			color: '#ED7D31'
            		}, 
            		{
            			id: 2,
            			name: 'Client repo',
            			icon: 'circle',
            			color: '#c00000'
            		}, 
            		{
            			id: 3,
            			name: 'Depending on',
            			icon: 'arrow',
            			color: '#000000'
            		}];

        var option = {
            tooltip: {},
            legend: {
				    show:true,
					orient: 'vertical', 
					y: 'center',
                    right: 3,
//                  category: graph.categories,
                    backgroundColor: 'transparent',
                    data: $legend,
//          		data: graph.categories.map(function (a) {
//              		return a.name;
//          		}),
            		itemWidth: 10,  // 设置宽度
					itemHeight: 10, // 设置高度   itemGap: 40 // 设置间距	
					borderColor: 'rgba(102,102,102,0.88)',
				    borderWidth: 3,
				    padding: 8,    // [5, 10, 15, 20]
				    itemGap: 6,
				    textStyle: {
				        color: '#000000',
				        fontSize: 16
				    }
        	},
        	// 提示框
			tooltip: {
				    trigger: 'item',           // 触发类型，默认数据触发，见下图，可选为：'item' ¦ 'axis'
				    showDelay: 20,             // 显示延迟，添加显示延迟可以避免频繁切换，单位ms
				    hideDelay: 100,            // 隐藏延迟，单位ms
				    transitionDuration : 0.4,  // 动画变换时间，单位s
				    backgroundColor: 'rgba(0,0,0,0.7)',     // 提示背景颜色，默认为透明度为0.7的黑色
				    borderColor: '#333',       // 提示边框颜色
				    borderRadius: 4,           // 提示边框圆角，单位px，默认为4
				    borderWidth: 0,            // 提示边框线宽，单位px，默认为0（无边框）
				    padding: 5,                // 提示内边距，单位px，默认各方向内边距为5，接受数组分别设定上右下左边距，同css             
				    textStyle: {
				        color: '#fff'
				    }
			},
            label: {                // 关系对象上的标签
	            	normal: {
	                	show: true,                 // 是否显示标签
	                	position: "bottom",         // 标签位置:'top''left''right''bottom''inside''insideLeft''insideRight''insideTop''insideBottom''insideTopLeft''insideBottomLeft''insideTopRight''insideBottomRight'
	                	textStyle: {                // 文本样式
	                    	fontSize: 16
	                	}
//	                	formatter: '{b}'
	            	}	
	        },
            series : [{
     			type: 'graph',
                layout: 'force',
                symbol: 'circle',
                edgeSymbol: ['none', 'arrow'],
//              categories: graph.categories,
                data: graph.data,
                links: graph.links,
                roam: true,
                focusNodeAdjacency: true,   // 是否在鼠标移到节点上的时候突出显示节点以及节点的边和邻接节点。[ default: false ]	
        		animation: false,
        		
            }]
//          force: {
//                  edgeLength: 100,
//                  repulsion: 20,
//                  gravity: 0.2,
//                  // 数据map到圆的半径的最小值和最大值
////				    minRadius : 10,
////				    maxRadius : 20,
////				    density : 1.0,
////				    attractiveness : 1.0,
////  			    // 初始化的随机大小位置
////				    initSize : 30,
//				    // 向心力因子，越大向心力越大
//				    centripetal : 1,
//				    // 冷却因子
//				    coolDown : 0.99,
//				    // 分类里如果有样式会覆盖节点默认样式
////				    itemStyle: {
////				        normal: {
////				            color: 各异,
////				            label: {
////				                show: false
////				                textStyle: null      // 默认使用全局文本样式，详见TEXTSTYLE
////				            },
////				            nodeStyle : {
////				                brushType : 'both',
////				                color : '#f08c2e',
////				                strokeColor : '#5182ab'
////				            },
////				            linkStyle : {
////				                strokeColor : '#5182ab'
////				            }
////				        },
////				        emphasis: {
////				            // color: 各异,
////				            label: {
////				                show: false
////				                // textStyle: null      // 默认使用全局文本样式，详见TEXTSTYLE
////				            },
////				            nodeStyle : {},
////				            linkStyle : {}
////				        }
////				    }
//             }
        };
        myChart.setOption(option);
        
    }

	function showProblemDetails(json){
//	            type : "GET"
	    $.ajax({
            url: "/diagnosis",
			datatype: "json",
			data: json,
            success: function (res) {
//          	alert(res)
//          	var res = eval('(' + result + ')');
//          	var res = eval("("+resjson+")");
//          	alert(res.result)
            	if (res.result == 1) {
            		alert('Please enter the correct name of the project! :D')
            		document.getElementById("d_wait").style.visibility="hidden";
            	} else{
            		if (res.result == 2) {
            			alert('Please enter the correct version of the project! :D')
            			document.getElementById("d_wait").style.visibility="hidden";
            		} else{
            			if (res.result ==0) {
                            document.getElementById("d_wait").style.visibility="hidden";
//                          $div = $('#dependency-model')
//                          temp = '<span>' + res.dep_tree + '</span>'
//                          $div.append(temp)
							var dep = eval("(" + res.dep_tree + ")");
							alert(dep[3])
							draw(dep);
                            $rootcause_div = $('#root_cause_div');
                            temp = '<span>' + res.issues + '</span>';
                            $rootcause_div.append(temp);
                            // down_msg  suggested_solution_div
                            $solution_div = $('#suggested_solution_div');
                            temp = '<span>' + res.down_msg + '</span>';
                            $solution_div.append(temp);
            		    }
            		}
            	}
            }
        });
	}
	
});