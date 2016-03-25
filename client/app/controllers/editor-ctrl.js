/* jshint esnext: true */
angular.module("web-config").controller("EditorCtrl", ["$scope", "$http", "$stateParams", "$filter", "$uibModal", "CONSTS", "Modals", function($scope, $http, $stateParams, $filter, $uibModal, CONSTS, Modals) {

    var me = this;
    this.configPath = $stateParams.path;
    this.versions = [];
    this.selectedVersion = null;
    // oldest loaded version number
    this.oldestVersion = null;
    this.config = {xml: ""};
    this.configExecutiveCopy = {};
    this.expertMode = false;

    var srvendp = CONSTS.server_endpoint;
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

    this.getConfigVersions = function(older) {
        var requestURL = srvendp + "/history" + me.configPath;
        if (older) {
            if (me.oldestVersion > 1) {
                requestURL += '/limit=20/bellow=' + me.oldestVersion;
            } else {
                return Promise.reject(
                    "Not querying history, oldest version <= 1");
            }
        } else {
            requestURL += '/limit=20';
        }
        return $http.get(requestURL).then(function(response) {
            var d = response.data;
            if (older) {
                me.versions = me.versions.concat(d);
                console.log(me.versions);
                console.log(d);
            } else {
                me.versions = d;
            }
            me.oldestVersion = d[d.length - 1][0];
        }, function(response) {
            console.log("Failed to get versions for" + me.configPath);
        });
    };

    this.selectVersion = function(version) {
        me.selectedVersion = version;
        return $http.get(srvendp + "/config" + me.configPath + "/v=" + me.selectedVersion)
            .then(function(response) {
                console.log(response);
                me.config = response.data;
                me.configExecutiveCopy = angular.copy(response.data.executive);
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
        Modals.showXML(title, me.config.xml);
    };

    this.previewFinalXML = function() {
        //show if success, else default message
        var modal = Modals.responseModal(me.buildFinalXML(), true, false);
        modal.result.then(function(response) {
            Modals.showXML("Generated final XML", response.data);
        });
    };

    this.previewModifications = function() {
        //show if success, else default message
        var modal = Modals.responseModal(me.buildXML(), true, false);
        modal.result.then(function(response) {
            Modals.showXML("Parsed modifications", response.data);
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
            srvendp + "/buildfinalxml", {
                path: me.configPath,
                version: me.selectedVersion,
                xml: editor.getValue(),
                executive: me.config.executive});
    };

    this.buildXML = function() {
        return $http.post(
            srvendp + "/buildxml", {
                path: me.configPath,
                version: me.selectedVersion,
                fields: me.config.fields});
    };

    this.submit = function() {
        var submitModal = $uibModal.open({
            templateUrl: "templates/modals/submit.html",
            controller: "SubmitModalCtrl as ctrl"
        });

        submitModal.result.then(function(comment) {
            var infoModal;
            if (me.expertMode) {
                infoModal = Modals.responseModal(
                    submitExpertXML(comment));
            } else {
                infoModal = Modals.responseModal(
                    submitChanges(comment));
            }
            infoModal.result.then(function(response) {
                me.getConfigVersions().then(function() {
                    if (me.versions.length > 0) {
                        me.selectVersion(me.versions[0][0]);
                    }
                });
            });
        }).catch(function() {
            console.log("Submit canceled");
            return Promise.reject();
        });
    };

    function submitExpertXML(comment) {
        return $http.post(
            srvendp + "/submitxml", {
                path: me.configPath,
                version: me.selectedVersion,
                xml: editor.getValue(),
                executive: me.config.executive,
                comment: comment});
    }

    function submitChanges(comment) {
        return $http.post(
            srvendp + "/submitfields", {
                path: me.configPath,
                version: me.selectedVersion,
                fields: me.config.fields,
                comment: comment});
    }

    me.init();

}]);
