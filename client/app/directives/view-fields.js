angular.module("web-config").directive("wcViewFields", function() {
    return {
        restrict: "E",
        templateUrl: "templates/view-fields.html?" + APP_TIME,
        scope: {fields: "="}
    };
});
