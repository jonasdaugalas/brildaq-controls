/* jshint esnext: true */
angular.module("web-config", ['ui.router', 'ui.bootstrap', 'ui.ace', 'prettyXml']);

// CONST will be filled by main controller
angular.module("web-config").constant("CONST", {});

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

    $urlMatcherFactoryProvider.strictMode(false);

    $stateProvider
        .state("main", {
            url: gui_prefix + "/{profileName:string}",
            abstract: true,
            controller: "MainCtrl",
            resolve: {
                config: ["$http", function($http) {
                    return $http.get("const.json?" + APP_TIME);
                }]
            },
            template: '<h1 class="text-danger" ng-if="$root.globals.illegalProfile"> ' +
                'Unknown profile: {{$root.globals.profileName}}</h1>' +
                '<ui-view ng-if="!$root.globals.illegalProfile"/>'
        })
        .state("main.editor", {
            url: "/editor{path:raw}",
            templateUrl: "templates/editor.html?" + APP_TIME,
            controller: "EditorCtrl as ctrl"
        })
        .state("main.overview", {
            url: "",
            templateUrl: "templates/overview.html?" + APP_TIME,
            controller: "OverviewCtrl as ctrl"
        });

}]);
