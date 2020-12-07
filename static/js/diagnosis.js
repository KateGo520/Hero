$(document).ready(function() {
//	$('#root_cause_div').height($('#root_cause_div').parent().height() - 44 - 30);
//	$('#suggested_solution_div').height($('#suggested_solution_div').parent().height() - 44 - 30);

//	$("#d-input").mousemove(function(){
//		$("#help-img").src="../static/img/demo/demo-1.png";
//	});
//	$("#d-input").mouseout(function(){
//		$("#help-img").css("height","160px");
//		$("#help-img").src="../static/img/demo/demo-l2.png";
//	});
    var dinput = document.getElementById('d-input');
    var dhelp = document.getElementById('help-img');
    dinput.onmouseover = function () {
        dhelp.src="../static/img/demo/demo-1.png";
    }
    
    
	$("#start_diagnosis_btn").click(function() {

		var $repo_name = $("#d_repo").val();
		var $repo_version = $("#d_version").val();
//		searchHistory($("#search").val());
		
			//        alert($repo_name)
			//        alert($repo_version)

		if ($repo_name == '') {
			alert("Please input the name of project to be analyzed! :D");
		} else {
			if ($repo_version == '') {
				alert("Please input the version of project to be analyzed! :D");
			} else {
				alert('Start diagnosis!');
				$("#root_cause_div").empty();
				$("#suggested_solution_div").empty();
				//	        	json = {"repo_name":$repo_name,"repo_version":$repo_version};
				document.getElementById("d_wait").style.visibility = "visible";
				document.getElementById("dependency-model").style.visibility = "hidden";
				showProblemDetails({
					"repo_name": $repo_name,
					"repo_version": $repo_version
				});
			}
		}
	});

	function draw(data) {
		var graph = data2Graph(data);
		drawGraph(graph);
	}
	
	function draw_test() {
		var graph = showEcharts();
		drawGraph(graph);
	}

	function data2Graph(data) {
//		alert(data[0])
		var categories = [{
					name: 'Client repo',
					itemStyle: {
						normal: {
							icon: 'circle',
							color: '#c00000'
						}
					}
				}, {
					name: 'Repo in GOPATH',
					itemStyle: {
						normal: {
							icon: 'circle',
							color: '#548235'
						}
					}
				}, {
					name: 'Repo in Go Modules',
					itemStyle: {
						normal: {
							icon: 'circle',
							color: '#ED7D31'
						}
					}

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
			links.push({
				'source': d,
				'target': u
			});
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
				"0": "#548235",
				"1": "#ED7D31",
				"2": "#c00000",
				"3": "#c00000"
			};
			var $color = $color_json[v];
			//      	alert($color_json[0]);
			//      	alert(k)
			//      	alert(v)
			var $size = 10;
			var $name = k;
			var $dm = 'GOPATH';
			var $category = 1;
			if (v == "1") {
				$dm = 'Go Modules';
				$category = 2;
				//      		$name = k + '[Go Modules]'
			}
			if (v == "2") {
				$size = 16;
				$dm = 'client repo in GOPATH';
				$category = 0;
				//      		$name = k + '[GOPATH]'

			}
			if (v == "3") {
				$size = 16;
				$dm = 'client repo in Go Modules';
				$category = 0;
				//      		$name = k + '[Go Modules]'
			}

			//      	alert('$category');
			//      	alert($category);
			var $node = {
				name: $name,
				value: $dm,
				category: $category,
				symbolSize: $size, // 关系图节点标记的大小，可以设置成诸如 10 这样单一的数字，也可以用数组分开表示宽和高，例如 [20, 10] 表示标记宽为20，高为10。
//				itemStyle: {
//					color: $color // 关系图节点标记的颜色
//				},
			};

			if (nodes.indexOf($node) == -1) {
				nodes.push($node);
			}

		});
		graph['links'] = links;
		graph['nodes'] = nodes;
		graph['categories'] = categories;
		return graph;
	}

	function drawGraph(graph) {
		var myChart = echarts.init(document.getElementById("dependency-model"));
		//      var categories = graph.categories;
		var option = {
			legend: {
				show: true,
				orient: 'horizontal',
				icon: 'circle',
				//					y: 'center',
				//                  right: 3,
				x: 'left',
				y: 'bottom',
				itemWidth: 10, // 设置宽度
				itemHeight: 10, // 设置高度   itemGap: 40 // 设置间距	
				borderColor: '#548235',
				borderType: 'dashed',
				backgroundColor: '#F2F4F7',
				opacity: 0.8,
				borderWidth: 3,
				padding: 8, // [5, 10, 15, 20]
				itemGap: 6,
				categories: [{
					name: 'Client repo',
					itemStyle: {
						normal: {
							icon: 'circle',
							color: '#c00000'
						}
					}
				}, {
					name: 'Repo in GOPATH',
					itemStyle: {
						normal: {
							icon: 'circle',
							color: '#548235'
						}
					}
				}, {
					name: 'Repo in Go Modules',
					itemStyle: {
						normal: {
							icon: 'circle',
							color: '#ED7D31'
						}
					}

				}],
				//          		data: graph.categories.map(function (a) {
				//              		return a.name;
				//          		}),
				//          		itemWidth: 10,  // 设置宽度
				//					itemHeight: 10, // 设置高度   itemGap: 40 // 设置间距	
				//					borderColor: 'rgba(102,102,102,0.88)',
				//				    borderWidth: 3,
				//				    padding: 8,    // [5, 10, 15, 20]
				//				    itemGap: 6,
				textStyle: {
					color: '#000000',
					fontSize: 13
				},
				selected: {
					'Repo in GOPATH': true,
					'Repo in Go Modules': true,
					'Client repo': true
				},
				data: ['Client repo', 'Repo in GOPATH', 'Repo in Go Modules']
			},
			// 提示框
			tooltip: {
				trigger: 'item', // 触发类型，默认数据触发，见下图，可选为：'item' ¦ 'axis'
				formatter: '{b} : {c}',
				showDelay: 20, // 显示延迟，添加显示延迟可以避免频繁切换，单位ms
				hideDelay: 100, // 隐藏延迟，单位ms
				transitionDuration: 0.4, // 动画变换时间，单位s
				backgroundColor: 'rgba(0,0,0,0.7)', // 提示背景颜色，默认为透明度为0.7的黑色
				borderColor: '#333', // 提示边框颜色
				borderRadius: 4, // 提示边框圆角，单位px，默认为4
				borderWidth: 0, // 提示边框线宽，单位px，默认为0（无边框）
				padding: 5, // 提示内边距，单位px，默认各方向内边距为5，接受数组分别设定上右下左边距，同css             
				textStyle: {
					color: '#fff'
				}
			},

			series: [{
				type: 'graph',
				layout: 'force',
				//				animation: true,
				//		type: 'force',
				symbol: 'circle',
				roam: true,
				edgeSymbol: ['none', 'arrow'],
				edgeSymbolSize: [1, 7],
				linkSymbol: 'arrow',
				lineStyle: {
					normal: {
						width: 1,
						color: '#3A478C',
						opacity: 0.8
					}
				},
				draggable: true,
				legendHoverLink: true,
				hoverOffset: 3, //选中高出的部分 数值越大越高
				hoverAnimation: true, //鼠标悬浮是否有区域弹出动画，false:无  true:有
				emphasis: {
					itemStyle: {
						borderColor: '#F2F400',
						borderWidth: 3

					},
					label: {
						show: true, // 是否显示标签
						position: "bottom", // 标签位置:'top''left''right''bottom''inside''insideLeft''insideRight''insideTop''insideBottom''insideTopLeft''insideBottomLeft''insideTopRight''insideBottomRight'
						textStyle: { // 文本样式
							fontSize: '110%',
							color: 'black'
								//							opacity: 1
						}
					}
				},
				avoidLabelOverlap: false,
				label: { // 关系对象上的标签
					show: true, // 是否显示标签
					position: "bottom", // 标签位置:'top''left''right''bottom''inside''insideLeft''insideRight''insideTop''insideBottom''insideTopLeft''insideBottomLeft''insideTopRight''insideBottomRight'
					textStyle: { // 文本样式
						fontSize: '30%',
						color: '#424242',
						opacity: 0.6,
							//						opacity: 0.6
					}
					//				formatter: '{b}'
				},
				//focusNodeAdjacency: true, // 是否在鼠标移到节点上的时候突出显示节点以及节点的边和邻接节点。[ default: false ]	
				//				animation: false,
				categories: [{
					name: 'Client repo',
					itemStyle: {
						normal: {
							icon: 'circle',
							color: '#c00000'
						}
					}
				}, {
					name: 'Repo in GOPATH',
					itemStyle: {
						normal: {
							icon: 'circle',
							color: '#548235'
						}
					}
				}, {
					name: 'Repo in Go Modules',
					itemStyle: {
						normal: {
							icon: 'circle',
							color: '#ED7D31'
						}
					}
				}],
				//				minRadius: 8,
				//				maxRadius: 10,
				//				density: 0.8,
				//				attractiveness: 0.8,
				nodes: graph.nodes,
				links: graph.links,
//				force: {
//		            edgeLength: [300,600],//线的长度，这个距离也会受 repulsion，支持设置成数组表达边长的范围
//		            repulsion: 100//节点之间的斥力因子。值越大则斥力越大
//              }
			}]

		};
		myChart.setOption(option);

	}

	function showEcharts() {
		var graph = {};
//		var myChart = echarts.init(document.getElementById("dependency-model"));
		nodes = [
					{category: 0,name: 'spotahome/redis-operator',value: 10,symbolSize: 10},
				    {category: 1,name: 'kubernetes/client-go',value: 3,symbolSize: 3},
				    {category: 1,name: 'prometheus/client_golang',value: 3},
				    {category: 1,name: 'spotahome/kooper',value: 3},
				    {category: 1,name: 'sirupsen/logrus',value: 3},
				    {category: 2,name: 'stretchr/testify',value: 3},
				    {category: 2,name: 'kubernetes/apimachinery',value: 3},
				    {category: 2,name: 'kubernetes/api',value: 3},
				    {category: 2,name: 'go-redis/redis',value: 3},
				    {category: 2,name: 'golang/exp',value: 3},
				    {category: 2,name: 'golang/tools',value: 3},
				    {category: 1,name: 'teambition/gear',value: 3},
				    {category: 1,name: 'go-http-utils/cookie',value: 3},
				    {category: 1,name: 'pelletier/go-toml',value: 3},
				    {category: 1,name: 'teambition/compressible-go',value: 3},
				    {category: 2,name: 'teambition/trie-mux',value: 3},
				    {category: 2,name: 'vulcand/oxy',value: 3},
				    {category: 2,name: 'hajimehoshi/oto',value: 3},
				    {category: 2,name: 'cyberdelia/templates',value: 3},
                    {category: 2,name: 'deepmap/oapi-codegen',value: 3},
					{category: 2,name: 'argoproj/argo-rollouts',value: 3}
				],

		links = [
					{source: 'spotahome/redis-operator',target: 'kubernetes/client-go',weight: 1},
					{source: 'spotahome/redis-operator',target: 'prometheus/client_golang',weight: 1},
					{source: 'spotahome/redis-operator',target: 'spotahome/kooper',weight: 1},
					{source: 'spotahome/redis-operator',target: 'sirupsen/logrus',weight: 1},
					{source: 'spotahome/redis-operator',target: 'stretchr/testify',weight: 1},
					{source: 'spotahome/redis-operator',target: 'kubernetes/apimachinery',weight: 1},
					{source: 'spotahome/redis-operator',target: 'kubernetes/api',weight: 1},
					{source: 'spotahome/redis-operator',target: 'go-redis/redis',weight: 1},
					{source: 'spotahome/redis-operator',target: 'golang/exp',weight: 1},
					{source: 'spotahome/redis-operator',target: 'golang/tools',weight: 1},
					
					{source: 'kubernetes/client-go',target: 'teambition/gear',weight: 1},
					{source: 'kubernetes/client-go',target: 'go-http-utils/cookie',weight: 1},
					{source: 'kubernetes/client-go',target: 'pelletier/go-toml',weight: 1},
					{source: 'kubernetes/client-go',target: 'teambition/compressible-go',weight: 1},
					{source: 'kubernetes/client-go',target: 'teambition/trie-mux',weight: 1},
					{source: 'kubernetes/client-go',target: 'vulcand/oxy',weight: 1},
					{source: 'kubernetes/client-go',target: 'hajimehoshi/oto',weight: 1},
					{source: 'kubernetes/client-go',target: 'cyberdelia/templates',weight: 1},
					{source: 'kubernetes/client-go',target: 'deepmap/oapi-codegen',weight: 1},
					{source: 'kubernetes/client-go',target: 'argoproj/argo-rollouts',weight: 1},
				]
		graph['links'] = links;
		graph['data'] = nodes;
		return graph;
//		myChart.setOption(option);

	}

	function showProblemDetails(json) {
		//	            type : "GET"
		$.ajax({
			url: "/diagnosis",
			datatype: "json",
			data: json,
			success: function(res) {
				//          	alert(res)
				//          	var res = eval('(' + result + ')');
				//          	var res = eval("("+resjson+")");
				//          	alert(res.result)
				if (res.result == 1) {
					alert('Please enter the correct name of the project! :D')
					document.getElementById("d_wait").style.visibility = "hidden";
				} else {
					if (res.result == 2) {
						alert('Please enter the correct version of the project! :D')
						document.getElementById("d_wait").style.visibility = "hidden";
					} else {
						if (res.result == 0) {
							document.getElementById("dependency-model").style.visibility = "visible";
							document.getElementById("d_wait").style.visibility = "hidden";
							alert('Finished!')
							$('#root_span').remove()
							$('#solution_span').remove()
							//                          $div = $('#dependency-model')
							//                          temp = '<span>' + res.dep_tree + '</span>'
							//                          $div.append(temp)
							var dep = eval("(" + res.dep_tree + ")");
//							alert(dep[3])
							draw(dep);
							$rootcause_div = $('#root_cause_div');
							temp = '<span id="root_span" style="font-family: PingFangSC-Semibold;font-size: 15px;font-weight: normal;font-stretch: normal;color: #ffffff;">' + res.root_cause + '</span>';
							$rootcause_div.append(temp);
							// down_msg  suggested_solution_div
							$solution_div = $('#suggested_solution_div');
							temp = '<span id="solution_span" style="font-family: PingFangSC-Semibold;font-size: 15px;font-weight: normal;font-stretch: normal;color: #ffffff;">' + res.solution + '</span>';
							$solution_div.append(temp);
						}
					}
				}
			}
		});
	}

});