angular.module("web-config").directive("wcExecutiveInfo", function() {
    return {
        restrict: "E",
        templateUrl: "templates/executive-info.html",
        bindToController: {
            executive: "=",
            editable: "="
        },
        scope: {},
        controller: function() {
            console.log(this.executive);
            this.e = this.executive;
        },
        controllerAs: "ctrl"
    };
});
