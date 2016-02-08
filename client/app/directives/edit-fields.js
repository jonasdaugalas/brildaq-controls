angular.module("web-config").directive("wcEditFields", function() {
    return {
        restrict: "E",
        templateUrl: "templates/edit-fields.html",
        bindToController: {
            fields: "="
        },
        scope: true,
        controller: function() {
            this.swap = function(arr, a, b) {
                var tmp = arr[a];
                arr[a] = arr[b];
                arr[b] = tmp;
            };
        },
        controllerAs: "ctrl"
    };
});
