angular.module("web-config").service("Modals", ["$rootScope", "$uibModal", function($rootScope, $uibModal) {

    var me = this;

    this.responseModal = function(requestPromise, insteadResolve, insteadReject) {
        console.log(requestPromise);
        var infoModal;
        var isolatedScope = $rootScope.$new(true); // true for isolated
        var modalOptions = {
            templateUrl: "templates/modals/info.html?" + APP_TIME,
            controller: "ResponseInfoModalCtrl as ctrl",
            scope: isolatedScope
        };
        isolatedScope.requestPromise = requestPromise;
        isolatedScope.insteadResolve = insteadResolve;
        isolatedScope.insteadReject = insteadReject;
        infoModal = $uibModal.open(modalOptions);
        return infoModal;
    };

    this.showXML = function(title, xml) {
        var modal = $uibModal.open({
            templateUrl: "templates/modals/view-xml.html?" + APP_TIME,
            controller: "ViewXmlModalCtrl as ctrl",
            size: "lg",
            resolve: {
                xml: function() {return xml;},
                title: function() {return title;}
            }
        });
    };

}]);
