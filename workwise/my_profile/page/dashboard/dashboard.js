frappe.pages['dashboard'].on_page_load = function(wrapper) {

	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Dashboard',
		single_column: true
	});

	
	wrapper.dashboard = new workwise.SalesFunnel(wrapper);
	
}

workwise.SalesFunnel = Class.extend({
	init: function(wrapper) {
		var me = this;
		$('<div class="row"> <div id="gender" class="col-sm-6"></div> <div id="department" class="col-sm-6"></div> <div id="performance" class="col-sm-12"></div></div>').appendTo($(wrapper).find('.layout-main-section'));
		setTimeout(function() {
			me.render();
		}, 0);

	},

	render: function() {
	
		frappe.call({
			method:"workwise.my_profile.page.dashboard.dashboard.get_test_data", 
			callback: function(r) {
				locations = r.message.split(",");
		 		gender = {
			    labels: locations,
			    datasets: [
			      {
			        title: "Male",
			        values: [30, 10, 4]
			      },
			      {
			        title: "Female",
			        values: [15, 87, 9]
			      },
			    ]
			  };
					
			  let gender_chart = new Chart({
			    parent: "#gender", // or a DOM element
			    title: "Gender by Location",
			    data: gender,
			    type: 'bar', // or 'line', 'scatter', 'pie', 'percentage'
			    height: 250,

			    colors: ['blue', 'pink'],
			    // hex-codes or these preset colors;
			    // defaults (in order):
			    // ['light-blue', 'blue', 'violet', 'red',
			    // 'orange', 'yellow', 'green', 'light-green',
			    // 'purple', 'magenta', 'grey', 'dark-grey']

			    format_tooltip_x: d => (d + '').toUpperCase(),
			    format_tooltip_y: d => d + ''
			  });

			}
		});

 




	let performance = {
	    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],

	    datasets: [
	      {
	        title: "Appraisal",
	        values: [0, -10, 50, 50, 35, 17, 90, -10]
	      },
	      {
	        title: "Attendance",
	        values: [-15, 87, 90, -20, 10, 50, 20, 30]
	      },
	    ]
	  };

	  let performance_chart = new Chart({
	    parent: "#performance", // or a DOM element
	    title: "2017 Performance",
	    data: performance,
	    type: 'line', // or 'line', 'scatter', 'pie', 'percentage'
	    height: 250,

	    colors: ['orange', 'yellow'],
	    // hex-codes or these preset colors;
	    // defaults (in order):
	    // ['light-blue', 'blue', 'violet', 'red',
	    // 'orange', 'yellow', 'green', 'light-green',
	    // 'purple', 'magenta', 'grey', 'dark-grey']

	    format_tooltip_x: d => (d + '').toUpperCase(),
	    format_tooltip_y: d => d + '%'
	  });


	let department = {
	    labels: ["ADM", "HR", "OPS", "SEC"],

	    datasets: [
	      {
	        title: "Employees",
	        values: [23, 5, 44, 20]
	      },
	    ]
	  };

	  let department_chart = new Chart({
	    parent: "#department", // or a DOM element
	    title: "Employees By Department",
	    data: department,
	    type: 'pie', // or 'line', 'scatter', 'pie', 'percentage'
	    height: 250,

	    colors: ['orange', 'yellow'],
	    // hex-codes or these preset colors;
	    // defaults (in order):
	    // ['light-blue', 'blue', 'violet', 'red',
	    // 'orange', 'yellow', 'green', 'light-green',
	    // 'purple', 'magenta', 'grey', 'dark-grey']

	    format_tooltip_x: d => (d + '').toUpperCase(),
	    format_tooltip_y: d => d + ''
	  });

	},

});