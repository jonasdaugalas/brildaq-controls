angular.module("web-config").service("Alarm", ["$rootScope", function($rootScope) {

    var me = this;
    var alarm = new Audio('vendor/alarm.ogg');
    this.playing = false;
    this.mute = false;

    alarm.onended = function() {
        $rootScope.$apply(function() {
            me.playing = false;
        });
    };

    this.isPlaying = function() {
        return me.playing;
    };

    this.isMute = function() {
        return me.mute;
    };

    this.play = function(){
        if (!me.mute) {
            this.playing = true;
            alarm.play();
        }
    };

    this.toggleMute = function(){
        me.mute = !me.mute;
        alarm.muted = me.mute;
    };
}]);
