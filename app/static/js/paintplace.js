(function() {
    'use strict';
  
    angular
      .module('App')
      .directive('paintplace', paintplace);
  
    function paintplace(){
      let directive = {
        restrict:'E',
        scope:{
        },
        templateUrl: '/static/templates/paintplace.html',
        controller: Controller,
        link: Link
      };
  
      return directive;
    };
    
    
    Controller.$inject = ['$scope','$mdDialog'];
  
    function Controller($scope, $mdDialog){

      var showResult = (ev, class_text) => {
        let title = class_text != "" ? `That's what we found`: `We couldn't find any compatible classes.`;
        let content = class_text != ""? class_text: `Help to us, share the name of your scribble.`;
        $mdDialog.show(
          $mdDialog.alert()
            .parent(angular.element(document.body))
            .clickOutsideToClose(true)
            .title(title)
            .htmlContent(content)          
            .ariaLabel('Prediction results')
            .ok('Cool!')
            .targetEvent(ev)
        );
      }

      $scope.predict = (ev) => {
        let canvas = document.querySelector("#myCanvas")
        let t = canvas.toDataURL()
        $.post("/q", {"imagedata":t})
        .then( result => {
          $scope.result = result;
          $scope.imagedata = t;

          $scope.class_info = result.classes;
          $scope.class_info.sort( (l, r) =>{
            let lk = Object.keys(l)[0];
            let rk = Object.keys(r)[0];
            return l[lk] - r[rk]
          });

          $scope.class_text = "";
          for(var c in $scope.class_info){
            let key = Object.keys($scope.class_info[c])[0];
            $scope.class_text += `<div class="class_level_${c}"><b>${key}</b> ${$scope.class_info[c][key].toFixed(3)} <br />\n`;
          };

          showResult(ev, $scope.class_text);
        })
      };
    
      $scope.earse = (ev) => {
        let canvas = document.querySelector("#myCanvas");
        let context = canvas.getContext('2d');
        context.clearRect(0,0, canvas.width, canvas.height);
        $scope.result = undefined;
        $scope.imagedata = undefined;
      };

      $scope.save = (ev) => {
        
        let best_class = $scope.class_info[0];
        let content = `<p>Type the name for scribble for share it in the our database.</p>`;
        
        if (best_class){
          let key = Object.keys(best_class)[0];
          content += `<p class="class_level_2">The best predicted class: <strong>${key}</strong> with ${best_class[key].toFixed(3)} distance.</p>`
        }

        var confirm = $mdDialog.prompt()
          .title('Share your scribble in the our database.')
          //.textContent('Type the name for scribble for share it in the our database.')
          .htmlContent(content)
          .placeholder('Scribble name')
          .ariaLabel('Scribble name')
          //.initialValue('clrcle')
          .targetEvent(ev)
          .required(true)
          .ok('Save!')
          .cancel('Skip');
    
        $mdDialog.show(confirm).then(function(result) {
          $scope.class_name = result;
          $.post("/save", {"data":{
            "class_name": $scope.class_name, 
            "res": $scope.result.result,
            "image": $scope.imagedata,
          }})
          .then( res => {
            console.log(res);
          })
          .catch( err => {
            console.log(err);
          })
        }, function() {
          //Nothing to do
        });
      };

      $scope.download = ($event) => {
        let canvas = document.querySelector("#myCanvas")
        
        var link = document.createElement('a');
        link.href = canvas.toDataURL();
        link.download = 'scribble.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

      }
    }

    Link.$inject = ['$scope','$element']

    function Link($scope, $element){
      var canvas = document.getElementById('myCanvas');
      var ctx = canvas.getContext('2d');
      
      var mouse = {x: 0, y: 0};
      
      ctx.lineWidth = 3;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.strokeStyle = 'rebeccapurple';
      var paint = false;

      var el = angular.element('canvas')[0];
      var rect = 0;

      var useragent = navigator.userAgent;
      
      //TODO: Rewrite desctop part as the mobile part style

      if(/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|mobile|CriOS/i.test(useragent)){
        // MOBILE Browsers
        canvas.addEventListener('touchmove', (e) => {
          e.preventDefault();
          
          if (paint){
            var touches = e.changedTouches;

            for (let t of touches){
              ctx.lineTo(t.pageX - rect.left, t.pageY - rect.top);
              ctx.stroke();
            }
          }         
          
        }, false);

        canvas.addEventListener('touchstart', (e) => {
            paint = true;
            //rect is zeroes after initialization
            rect = el.getBoundingClientRect();

            var touches = e.changedTouches;
            for (let t of touches){
              ctx.beginPath();
              ctx.moveTo(t.pageX - rect.left, t.pageY - rect.top);              
            }
        
        }, false);
        
        canvas.addEventListener('touchend', (e) => {
          paint = false;
          ctx.stroke();
        }, false);

      }
      else{
        // DESCTOP
        canvas.addEventListener('mousemove', (e) => {
          let el = angular.element('canvas')[0];
          let rect = el.getBoundingClientRect();
          
          mouse.x = e.pageX - rect.left;
          mouse.y = e.pageY - rect.top;
        }, false);

        canvas.addEventListener('mousedown', function(e) {
            ctx.beginPath();
            ctx.moveTo(mouse.x, mouse.y);
        
            canvas.addEventListener('mousemove', onPaint, false);
        }, false);
        
        canvas.addEventListener('mouseup', function() {
            canvas.removeEventListener('mousemove', onPaint, false);
        }, false);
        
        var onPaint = function() {
            ctx.lineTo(mouse.x, mouse.y);
            ctx.stroke();
        };

      }

    }
  
  })();	