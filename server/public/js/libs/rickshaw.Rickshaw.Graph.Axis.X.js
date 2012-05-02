/*
 * @depends rickshaw.js
 */

Rickshaw.namespace('Rickshaw.Graph.Axis.X');

Rickshaw.Graph.Axis.X = function(args) {

	var self = this;

	this.graph = args.graph;
	this.elements = [];
	this.ticksTreatment = args.ticksTreatment || 'plain';
	this.fixedTimeUnit = args.timeUnit;
    this.labels = args.labels;

	this.render = function() {

		this.elements.forEach( function(e) {
			e.parentNode.removeChild(e);
		} );

		this.elements = [];

        var labels = this.labels;

        labels.forEach(function(label, iter){

            if (self.graph.x(iter) > self.graph.x.range()[1]) return;

			var element = document.createElement('div');
            element.style.left = self.graph.x(iter) + 'px';
			element.classList.add('x_tick');
			element.classList.add(self.ticksTreatment);

			var title = document.createElement('div');

            // We don't want the last label to appear outside the
            // graph, so we leave it out for now. Total hack.
            if ((iter + 1)  !== labels.length){
                title.classList.add('title');
			    title.innerHTML = label;
			    element.appendChild(title);
            }
			self.graph.element.appendChild(element);
			self.elements.push(element);

        });
	};

	this.graph.onUpdate( function() { self.render(); } );
};
