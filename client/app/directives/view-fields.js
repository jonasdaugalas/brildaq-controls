angular.module("web-config").directive("wcViewFields", function() {
    return {
        restrict: "E",
        templateUrl: "templates/view-fields.html",
        scope: {fields: "="}
    };
});
