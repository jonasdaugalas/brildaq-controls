/* jshint esnext: true */
angular.module("web-config").controller("EditorCtrl", ["$scope", "$http", "$stateParams", "$filter", "$uibModal", function($scope, $http, $stateParams, $filter, $uibModal) {

    var me = this;
    this.configPath = $stateParams.path;
    this.versions = [];
    this.selectedVersion = null;
    this.config = {xml: ""};
    this.configExecutiveCopy = {};
    this.expertMode = false;

    var initPromise = Promise.resolve();
    var editor = null;

    this.init = function() {
        return me.getConfigVersions().then(function() {
            if (me.versions.length > 0) {
                return me.selectVersion(me.versions[0][0]);
            }
            return Promise.resolve();
        });
    };

    this.switchEditingMode = function() {
        me.expertMode = !me.expertMode;
        if (me.expertMode) {
            editor.renderer.updateFull();
        }
    };

    this.getConfigVersions = function() {
        return $http.get("/history" + me.configPath).then(function(response) {
            me.versions = response.data;
        }, function(response) {
            console.log("Failed to get versions for" + me.configPath);
        });
    };

    this.selectVersion = function(version) {
        me.selectedVersion = version;
        return $http.get("/config" + me.configPath + "/v=" + me.selectedVersion)
            .then(function(response) {
                me.config = response.data;
                me.configExecutiveCopy = angular.copy(response.data.executive);
                console.log(editor);
                if (editor) {
                    console.log("setting xml");
                    editor.setValue(me.config.xml);
                }
            }, function(response) {
                console.log("Failed to get config");
            });
    };

    this.showOrigXML = function() {
        var title = ("Original configuration: " + me.configPath +
                     " v" + me.selectedVersion);
        showXML(title, me.config.xml);
    };

    this.showFinalXML = function() {
        me.buildFinalXML().then(function(response) {
            showXML("Generated final XML", response.data);
        });
    };

    this.editorLoaded = function(_editor) {
        editor = _editor;
        editor.getSession().setUseWorker(false);
        editor.$blockScrolling = Infinity;
        editor.getSession().setUseSoftTabs(true);
        editor.setReadOnly(false);
        // editor.setKeyboardHandler("ace/keyboard/emacs");
        editor.setValue(me.config.xml);
        ace.config.loadModule("ace/ext/keybinding_menu", function(module) {
            module.init(editor);
        });
    };

    this.showEditorBindings = function() {
        editor.showKeyboardShortcuts();
    };

    this.beautify = function() {
        var text = editor.getValue();
        text = $filter("prettyXml")(text);
        editor.setValue(text);
    };

    this.buildFinalXML = function() {
        return $http.post(
            "/buildfinalxml", {
                path: me.configPath,
                version: me.selectedVersion,
                xml: editor.getValue(),
                executive: me.config.executive})
            .then(function(response) {
                return response;
            }, function(response) {
                console.log(response);
                return Promise.reject();
            });
    };

    this.submit = function() {
        var submitModal = $uibModal.open({
            templateUrl: "templates/modals/submit.html",
            controller: "SubmitModalCtrl as ctrl"
        });

        submitModal.result.then(function(comment) {
            var infoModal;
            var isolatedScope = $scope.$new(true); // true for isolated
            var modalOptions = {
                templateUrl: "templates/modals/info.html",
                controller: "ResponseInfoModalCtrl as ctrl",
                scope: isolatedScope
            };
            infoModal = $uibModal.open(modalOptions);
            if (me.expertMode) {
                isolatedScope.request = submitExpertXML(comment);
            } else {
                isolatedScope.request = submitChanges(comment);
            }
            return infoModal.closed.then(function() {
                me.getConfigVersions();
            });
        }).catch(function() {
            console.log("Submit canceled");
            return Promise.reject();
        });
    };

    function showXML(title, xml) {
        var modal = $uibModal.open({
            templateUrl: "templates/modals/view-xml.html",
            controller: "ViewXmlModalCtrl as ctrl",
            size: "lg",
            resolve: {
                xml: function() {return xml;},
                title: function() {return title;}
            }
        });
    }

    function submitExpertXML(comment) {
        return $http.post(
            "/submitxml", {
                path: me.configPath, version:
                me.selectedVersion,
                xml: editor.getValue(),
                executive: me.config.executive,
                comment: comment});
    }

    function submitChanges(comment) {
        return;
    }

    me.init();

}]);
