(function(){
  var root=document.documentElement;
  var theme=document.getElementById("theme");
  if(theme)theme.addEventListener("click",function(){
    var dark=root.getAttribute("data-theme")==="dark"||(!root.getAttribute("data-theme")&&matchMedia("(prefers-color-scheme: dark)").matches);
    var next=dark?"light":"dark";root.setAttribute("data-theme",next);
    try{localStorage.setItem("theme",next)}catch(e){}
  });
  var menu=document.getElementById("menu"),nav=document.getElementById("nav");
  if(menu&&nav)menu.addEventListener("click",function(){
    var open=nav.classList.toggle("open");menu.setAttribute("aria-expanded",String(open));
  });
  document.querySelectorAll("[data-plan]").forEach(function(card){
    var opts=card.querySelectorAll("[data-opt]"),price=card.querySelector("[data-price]"),buy=card.querySelector("[data-buy]");
    opts.forEach(function(o){o.addEventListener("click",function(e){
      e.preventDefault();
      opts.forEach(function(x){x.classList.toggle("on",x===o)});
      if(price)price.innerHTML=o.dataset.amount+' <small>تومان / '+o.dataset.label+'</small>';
      if(buy)buy.setAttribute("href",o.getAttribute("href"));
    })});
  });
})();
