
      let progress = document.getElementById('progressbar');
      let zeeshan = document.body.scrollHeight - window.innerHeight;
      window.onscroll = function(){
           let progressHeight = (window.pageYOffset / zeeshan) * 104 + "%";
          progress.style.height = progressHeight;
  
      }