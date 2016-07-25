/* jshint esnext: true */
angular.module("web-config", ['ui.router', 'ui.bootstrap', 'ui.ace', 'prettyXml']);

angular.module("web-config").value("CONSTS", {});

angular.module("web-config").config(["$httpProvider", "$locationProvider", "$stateProvider", "$urlRouterProvider", "$urlMatcherFactoryProvider", function($httpProvider, $locationProvider, $stateProvider, $urlRouterProvider, $urlMatcherFactoryProvider) {

    var gui_prefix = "";
    // state urls: /app_base + ...
    // $urlRouterProvider.otherwise("/gui");
    $locationProvider.html5Mode(true);
    $httpProvider.defaults.withCredentials = true;

    $urlMatcherFactoryProvider.type("raw", {
        encode: (val) => (val !== null ? val.toString() : val),
        decode: (val) => (val !== null ? val.toString() : val),
        is: (val) => true
    });

    $stateProvider
        .state("overview", {
            url: gui_prefix + "/",
            templateUrl: "templates/overview.html?" + APP_TIME,
            controller: "OverviewCtrl as ctrl"
        })
        .state("editor", {
            url: gui_prefix + "/editor{path:raw}",
            templateUrl: "templates/editor.html?" + APP_TIME,
            controller: "EditorCtrl as ctrl"
        });

}]);
