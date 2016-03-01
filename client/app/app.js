/* jshint esnext: true */
angular.module("web-config", ['ui.router', 'ui.bootstrap', 'ui.ace', 'prettyXml']);

angular.module("web-config").config(["$locationProvider", "$stateProvider", "$urlRouterProvider", "$urlMatcherFactoryProvider", function($locationProvider, $stateProvider, $urlRouterProvider, $urlMatcherFactoryProvider) {

    var gui_prefix = "/gui";
    // state urls: /app_base + ...
    // $urlRouterProvider.otherwise("/gui");
    $locationProvider.html5Mode(true);

    $urlMatcherFactoryProvider.type("raw", {
        encode: (val) => (val !== null ? val.toString() : val),
        decode: (val) => (val !== null ? val.toString() : val),
        is: (val) => true
    });

    $stateProvider
        .state("overview", {
            url: gui_prefix + "/",
            templateUrl: "templates/overview.html",
            controller: "OverviewCtrl as ctrl"
        })
        .state("editor", {
            url: gui_prefix + "/editor{path:raw}",
            templateUrl: "templates/editor.html",
            controller: "EditorCtrl as ctrl"
        });

}]);
