var app = angular.module('myApp', []);
app.controller('myCtrl', function($scope, $http, $interval, $timeout, $q){

	$scope.self_IP;
    $scope.mu = 0.8;
    $scope.max_ite=100;
    $scope.method = "SVRG";
    $scope.dist_style = "Diffusion"
    $scope.iter = 0;
    $scope.iter_per_call = 5;
    $scope.fetched = "Have not fetched data.";
    $scope.data_select = {0:false,  1:false,  2:false,  3:false,  4:false,
                          5:false, 6:false, 7:false, 8:false, 9:false}

	function askIP() {
        window.RTCPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;   //compatibility for firefox and chrome
            var pc = new RTCPeerConnection({iceServers:[]}), noop = function(){};
            pc.createDataChannel("");    //create a bogus data channel
            pc.createOffer(pc.setLocalDescription.bind(pc), noop);    // create offer and set local description
            pc.onicecandidate = function(ice){  //listen for candidate events
                if(!ice || !ice.candidate || !ice.candidate.candidate)  return;
                var myIP = /([0-9]{1,3}(\.[0-9]{1,3}){3}|[a-f0-9]{1,4}(:[a-f0-9]{1,4}){7})/.exec(ice.candidate.candidate)[1];
                $scope.self_IP= myIP;
                pc.onicecandidate = noop;
            };
    };
    askIP()

		var stop;

    $scope.search = function(){
        $http({
                method : 'GET',
                url: '/search',
        }).then(function mySuccess(response){
                $scope.ip_list = response.data['iplist'];
                console.log("Received the IP List.")
        });
    };
		$scope.start = function(){
				stop = $interval($scope.search,1000);

		};
		$scope.stop = function(){
				$interval.cancel(stop);
				stop = undefined;
				console.log("Canceled");
		};
    $scope.connect = function($index){
        $http({
                method: 'POST',
                url: '/connect',
                data: {'index': $index, 'self_IP': $scope.self_IP}
        }).then(function mySuccess(response){
                console.log("Connected");
        });
    };
    $scope.generateWeights = function() {
        $http({
                method : 'GET',
                url : '/generateWeights',
        }).then(function mySuccess(response) {
                console.log('Generated Weights.');
            });
    };
    $scope.get_data = function(){
        $http({
                method : 'POST',
                url : '/get_data',
                data : {'mask': $scope.data_select}
        }).then(function mySuccess(response){
               $scope.fetched="Data fetched!";
               console.log("Data fetched")
        });
    };
    $scope.run_alg = function(){
        $http({
                method : 'POST',
                url : '/run_alg',
                data : {'mu': parseFloat($scope.mu),
                   'max_ite': $scope.max_ite,
                   'method':  $scope.method,
                   'ite': $scope.iter,
                   'iter_per_call': $scope.iter_per_call,
                   'dist_style': $scope.dist_style}
        }).then(function mySuccess(response){
               console.log("Information passed to backend.")
        });
    };

});
app.config(function($interpolateProvider) {
	$interpolateProvider.startSymbol('{[{');
	$interpolateProvider.endSymbol('}]}');
});
