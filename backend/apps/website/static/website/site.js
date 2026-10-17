(function(){
  var root=document.documentElement;
  var still=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;

  // theme toggle
  var theme=document.getElementById("theme");
  if(theme)theme.addEventListener("click",function(){
    var dark=root.getAttribute("data-theme")==="dark"||(!root.getAttribute("data-theme")&&matchMedia("(prefers-color-scheme: dark)").matches);
    var next=dark?"light":"dark";root.setAttribute("data-theme",next);
    try{localStorage.setItem("theme",next)}catch(e){}
  });

  // mobile menu
  var menu=document.getElementById("menu"),nav=document.getElementById("nav");
  if(menu&&nav)menu.addEventListener("click",function(){
    var open=nav.classList.toggle("open");menu.setAttribute("aria-expanded",String(open));
  });

  // header gains its edge once the page scrolls
  var hdr=document.getElementById("hdr");
  if(hdr){var onScroll=function(){hdr.classList.toggle("scrolled",window.scrollY>8)};onScroll();window.addEventListener("scroll",onScroll,{passive:true})}

  // plan cards: switching the subscription length updates price and buy link
  document.querySelectorAll("[data-plan]").forEach(function(card){
    var opts=card.querySelectorAll("[data-opt]"),price=card.querySelector("[data-price]"),buy=card.querySelector("[data-buy]");
    opts.forEach(function(o){o.addEventListener("click",function(e){
      e.preventDefault();
      opts.forEach(function(x){x.classList.toggle("on",x===o)});
      if(price)price.innerHTML=o.dataset.amount+' <small>تومان / '+o.dataset.label+'</small>';
      if(buy)buy.setAttribute("href",o.getAttribute("href"));
    })});
  });

  // numbers count up from zero the first time they come into view; the
  // digits and separators are read from (and written back as) Persian text
  var FA="۰۱۲۳۴۵۶۷۸۹",AR="٠١٢٣٤٥٦٧٨٩";
  function toLatin(s){return s.replace(/[۰-۹]/g,function(d){return FA.indexOf(d)}).replace(/[٠-٩]/g,function(d){return AR.indexOf(d)})}
  function toFa(n,group){var s=String(n);if(group)s=s.replace(/\B(?=(\d{3})+(?!\d))/g,"٬");return s.replace(/\d/g,function(d){return FA[d]})}
  function countUp(el){
    var raw=el.textContent,m=toLatin(raw).match(/^(\D*)([\d٬,]+)(\D*)$/);
    if(!m)return;
    var target=parseInt(m[2].replace(/[٬,]/g,""),10);
    if(!isFinite(target)||target<2)return;
    var group=/[٬,]/.test(m[2])||target>=1000,start=null;
    function frame(t){
      if(start===null)start=t;
      var k=Math.min(1,(t-start)/1500),v=Math.round(target*(1-Math.pow(1-k,3)));
      el.textContent=m[1]+toFa(v,group)+m[3];
      if(k<1)requestAnimationFrame(frame);else el.textContent=raw;
    }
    requestAnimationFrame(frame);
  }

  // scroll reveal (+ count-up) as elements enter the viewport
  var revealed=document.querySelectorAll(".rv"),counters=document.querySelectorAll("[data-count]");
  if(!("IntersectionObserver" in window)||still){
    revealed.forEach(function(el){el.classList.add("in")});
  }else{
    var io=new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if(!e.isIntersecting)return;
        e.target.classList.add("in");
        io.unobserve(e.target);
      });
    },{rootMargin:"0px 0px -8% 0px",threshold:.08});
    revealed.forEach(function(el){io.observe(el)});
    var co=new IntersectionObserver(function(entries){
      entries.forEach(function(e){if(e.isIntersecting){countUp(e.target);co.unobserve(e.target)}});
    },{threshold:.6});
    counters.forEach(function(el){co.observe(el)});
  }

  // the hero phone leans toward the pointer (mouse only)
  var fine=window.matchMedia&&matchMedia("(hover: hover) and (pointer: fine)").matches;
  document.querySelectorAll("[data-tilt]").forEach(function(area){
    var tilt=area.querySelector(".tilt");
    if(!tilt||still||!fine)return;
    var section=area.closest("section")||area;
    section.addEventListener("mousemove",function(e){
      var r=section.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;
      tilt.style.setProperty("--ry",(x*-16).toFixed(2)+"deg");tilt.style.setProperty("--rx",(y*10).toFixed(2)+"deg");
    });
    section.addEventListener("mouseleave",function(){tilt.style.setProperty("--ry","0deg");tilt.style.setProperty("--rx","0deg")});
  });

  // tabs: one panel at a time; arrow keys move between tabs (right/left
  // swapped for the right-to-left page), Home/End jump to the ends
  document.querySelectorAll("[data-tabs]").forEach(function(box){
    var tabs=[].slice.call(box.querySelectorAll('[role="tab"]'));
    var panels=tabs.map(function(t){return document.getElementById(t.getAttribute("aria-controls"))});
    function select(i,focus){
      tabs.forEach(function(t,j){
        var on=i===j;t.setAttribute("aria-selected",String(on));t.tabIndex=on?0:-1;
        if(panels[j])panels[j].hidden=!on;
      });
      if(focus)tabs[i].focus();
    }
    tabs.forEach(function(t,i){
      t.addEventListener("click",function(){select(i)});
      t.addEventListener("keydown",function(e){
        var n=tabs.length,k=e.key,to=null;
        if(k==="ArrowLeft")to=(i+1)%n;else if(k==="ArrowRight")to=(i-1+n)%n;
        else if(k==="Home")to=0;else if(k==="End")to=n-1;
        if(to!==null){e.preventDefault();select(to,true)}
      });
    });
    if(tabs.length)select(0);
  });

  // flashcards turn over on press
  document.querySelectorAll(".flipc").forEach(function(card){
    card.addEventListener("click",function(){card.setAttribute("aria-pressed",card.getAttribute("aria-pressed")==="true"?"false":"true")});
  });
})();
