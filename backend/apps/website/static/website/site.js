(function(){
  var root=document.documentElement;
  var still=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.querySelectorAll("[data-resend-wait]").forEach(function(button){
    var remaining=Number(button.dataset.resendWait)||0;
    if(remaining<=0)return;
    button.disabled=true;
    button.textContent="ارسال دوباره تا "+remaining.toLocaleString("fa-IR")+" ثانیه";
    var timer=setInterval(function(){
      remaining-=1;
      if(remaining<=0){clearInterval(timer);button.disabled=false;button.textContent="ارسال دوبارهٔ کد"}
      else button.textContent="ارسال دوباره تا "+remaining.toLocaleString("fa-IR")+" ثانیه";
    },1000);
  });

  // theme toggle
  var theme=document.getElementById("theme");
  if(theme)theme.addEventListener("click",function(){
    var dark=root.getAttribute("data-theme")==="dark";
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

  // the Leitner deck: turn the card, answer, and the card travels to its box
  var CARDS=[
    ["لوزارتان","Losartan","مکانیسم اثر؟","مهار گیرندهٔ آنژیوتانسین II (ARB)",1],
    ["متفورمین","Metformin","مکانیسم اثر؟","کاهش تولید گلوکز در کبد",2],
    ["وارفارین","Warfarin","مکانیسم اثر؟","آنتاگونیست ویتامین K",1],
    ["سالبوتامول","Salbutamol","گروه دارویی؟","آگونیست کوتاه‌اثر گیرندهٔ β2",3],
    ["امپرازول","Omeprazole","مکانیسم اثر؟","مهار پمپ پروتون",1],
    ["آتورواستاتین","Atorvastatin","مکانیسم اثر؟","مهار آنزیم HMG-CoA ردوکتاز",4],
    ["سیتالوپرام","Citalopram","گروه دارویی؟","مهارکنندهٔ انتخابی بازجذب سروتونین (SSRI)",2]
  ];
  document.querySelectorAll("[data-leitner]").forEach(function(box){
    var card=box.querySelector(".lt-card"),bins=[].slice.call(box.querySelectorAll(".bin")),hint=box.querySelector(".lt-hint");
    var counts=[3,2,1,1,0],i=0,busy=false;
    function f(k){return card.querySelector('[data-f="'+k+'"]')}
    function show(){
      var c=CARDS[i%CARDS.length];card.setAttribute("aria-pressed","false");
      f("box").textContent="جعبهٔ "+toFa(c[4])+" از ۵";f("name").textContent=c[0];f("en").textContent=c[1];f("q").textContent=c[2];f("a").textContent=c[3];
      bins.forEach(function(b,k){b.classList.toggle("hot",k===c[4]-1)});
    }
    function paint(){bins.forEach(function(b,k){b.querySelector("b").textContent=toFa(counts[k])})}
    card.addEventListener("click",function(){card.setAttribute("aria-pressed",card.getAttribute("aria-pressed")==="true"?"false":"true")});
    function next(){i++;show();if(!still&&card.animate)card.animate([{opacity:0,transform:"translateY(-24px) rotate(3deg)"},{opacity:1,transform:"none"}],{duration:420,easing:"cubic-bezier(.16,1,.3,1)"})}
    function answer(ok){
      if(busy)return;busy=true;
      var c=CARDS[i%CARDS.length],from=c[4]-1,to=ok?Math.min(4,from+1):0;
      hint.textContent=ok?(to===from?"این کارت در جعبهٔ آخر می‌ماند.":"کارت به جعبهٔ "+toFa(to+1)+" رفت و دیرتر برمی‌گردد."):"کارت به جعبهٔ ۱ برگشت و فردا دوباره می‌آید.";
      counts[from]--;counts[to]++;c[4]=to+1;
      if(still||!document.body.animate){paint();next();busy=false;return}
      var a=card.getBoundingClientRect(),b=bins[to].getBoundingClientRect(),fly=document.createElement("div");
      fly.className="lt-fly";fly.textContent=c[0];
      fly.style.cssText="left:"+a.left+"px;top:"+a.top+"px;width:"+a.width+"px;height:"+a.height+"px;font-size:22px";
      document.body.appendChild(fly);card.style.opacity="0";
      var dx=b.left+b.width/2-(a.left+a.width/2),dy=b.top+b.height/2-(a.top+a.height/2),sc=Math.max(b.width/a.width,.15);
      fly.animate([{transform:"none"},{transform:"translate("+dx+"px,"+dy+"px) scale("+sc+") rotate("+(ok?-8:8)+"deg)",opacity:.6}],{duration:650,easing:"cubic-bezier(.5,0,.2,1)"}).onfinish=function(){
        fly.remove();paint();card.style.opacity="";
        bins[to].animate([{transform:"scale(1)"},{transform:"scale(1.14)"},{transform:"scale(1)"}],{duration:380,easing:"cubic-bezier(.3,1.5,.5,1)"});
        next();busy=false;
      };
    }
    box.querySelectorAll("[data-ans]").forEach(function(btn){btn.addEventListener("click",function(){answer(btn.dataset.ans==="1")})});
    show();paint();
  });
})();
