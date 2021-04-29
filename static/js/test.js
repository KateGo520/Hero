$(document).ready(function() {
	$("#start_diagnosis_btn").click(function() {
		var myChart = echarts.init(document.getElementById("dependency-model"));

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
				itemGap: 10,
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
				edgeSymbolSize: [1, 6],
				linkSymbol: 'arrow',
				lineStyle: {
					normal: {
						width: 1,
						color: '#3A478C',
						opacity: 0.6
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
						fontSize: '90%',
						color: '#424242'
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
				nodes: [{
					category: 0,
					name: 'spotahome/redis-operator',
					value: 'client repo',
					symbolSize: 16

				}, {
					category: 1,
					name: 'kubernetes/client-go',
					value: 'GOPATH repo',
					symbolSize: 10
				}, {
					category: 1,
					name: 'prometheus/client_golang',
					value: 'GOPATH repo',
					symbolSize: 10
				}, {
					category: 1,
					name: 'spotahome/kooper',
					value: 'GOPATH repo',
					symbolSize: 10
				}, {
					category: 1,
					name: 'sirupsen/logrus',
					value: 'GOPATH repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'stretchr/testify',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'kubernetes/apimachinery',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'kubernetes/api',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'go-redis/redis',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'golang/exp',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'golang/tools',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 1,
					name: 'teambition/gear',
					value: 'GOPATH repo',
					symbolSize: 10
				}, {
					category: 1,
					name: 'go-http-utils/cookie',
					value: 'GOPATH repo',
					symbolSize: 10
				}, {
					category: 1,
					name: 'pelletier/go-toml',
					value: 'GOPATH repo',
					symbolSize: 10
				}, {
					category: 1,
					name: 'teambition/compressible-go',
					value: 'GOPATH repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'teambition/trie-mux',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'vulcand/oxy',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'hajimehoshi/oto',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'cyberdelia/templates',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'deepmap/oapi-codegen',
					value: 'Go Modules repo',
					symbolSize: 10
				}, {
					category: 2,
					name: 'argoproj/argo-rollouts',
					value: 'Go Modules repo',
					symbolSize: 10
				}],
				links: [{
						source: 'spotahome/redis-operator',
						target: 'kubernetes/client-go',
						weight: 1
					}, {
						source: 'spotahome/redis-operator',
						target: 'prometheus/client_golang',
						weight: 1
					}, {
						source: 'spotahome/redis-operator',
						target: 'spotahome/kooper',
						weight: 1
					}, {
						source: 'spotahome/redis-operator',
						target: 'sirupsen/logrus',
						weight: 1
					}, {
						source: 'spotahome/redis-operator',
						target: 'stretchr/testify',
						weight: 1
					}, {
						source: 'spotahome/redis-operator',
						target: 'kubernetes/apimachinery',
						weight: 1
					}, {
						source: 'spotahome/redis-operator',
						target: 'kubernetes/api',
						weight: 1
					}, {
						source: 'spotahome/redis-operator',
						target: 'go-redis/redis',
						weight: 1
					}, {
						source: 'spotahome/redis-operator',
						target: 'golang/exp',
						weight: 1
					}, {
						source: 'spotahome/redis-operator',
						target: 'golang/tools',
						weight: 1
					},

					{
						source: 'kubernetes/client-go',
						target: 'teambition/gear',
						weight: 1
					}, {
						source: 'kubernetes/client-go',
						target: 'go-http-utils/cookie',
						weight: 1
					}, {
						source: 'kubernetes/client-go',
						target: 'pelletier/go-toml',
						weight: 1
					}, {
						source: 'kubernetes/client-go',
						target: 'teambition/compressible-go',
						weight: 1
					}, {
						source: 'kubernetes/client-go',
						target: 'teambition/trie-mux',
						weight: 1
					}, {
						source: 'kubernetes/client-go',
						target: 'vulcand/oxy',
						weight: 1
					}, {
						source: 'kubernetes/client-go',
						target: 'hajimehoshi/oto',
//						weight: 1
					}, {
						source: 'kubernetes/client-go',
						target: 'cyberdelia/templates',
//						weight: 1
					}, {
						source: 'kubernetes/client-go',
						target: 'deepmap/oapi-codegen',
//						weight: 1
					}, {
						source: 'kubernetes/client-go',
						target: 'argoproj/argo-rollouts',
//						weight: 1
					},
				]
			}],

		};
		myChart.setOption(option);
	});

});