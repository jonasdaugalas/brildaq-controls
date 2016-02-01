/* jshint esnext: true */
angular.module("web-config", ['ui.router', 'ui.bootstrap', 'ui.ace', 'prettyXml']);

angular.module("web-config").config(["$locationProvider", "$stateProvider", "$urlRouterProvider", function($locationProvider, $stateProvider, $urlRouterProvider) {

    // state urls: /app_base + ...
    $urlRouterProvider.otherwise("/gui");
    $locationProvider.html5Mode(true);

    $stateProvider
        .state("overview", {
            url: "/gui",
            templateUrl: "templates/overview.html",
            controller: "OverviewCtrl as ctrl"
        })
        .state("editor", {
            url: "/gui/editor{path:.*}",
            templateUrl: "templates/editor.html",
            controller: "EditorCtrl as ctrl"
        });
}]);
