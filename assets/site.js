(function(){
var d=document;
var b=d.querySelector('.burger'),m=d.getElementById('mnav');
if(b&&m){
  b.setAttribute('role','button');b.setAttribute('aria-expanded','false');b.setAttribute('aria-controls','mnav');
  var set=function(open,kb){m.hidden=!open;b.setAttribute('aria-expanded',open?'true':'false');b.setAttribute('aria-label',open?'Close menu':'Open menu');d.body.classList.toggle('menu-open',open);if(open&&kb){var f=m.querySelector('a');if(f)f.focus();}};
  b.addEventListener('click',function(e){e.preventDefault();set(m.hidden,e.detail===0);});
  b.addEventListener('keydown',function(e){if(e.key===' '){e.preventDefault();set(m.hidden,true);}});
  d.addEventListener('keydown',function(e){if(e.key==='Escape'&&!m.hidden){set(false);b.focus();}});
  m.addEventListener('click',function(e){if(e.target.closest('a'))set(false);});
  window.addEventListener('resize',function(){if(window.innerWidth>900&&!m.hidden)set(false);});
}
var tools=d.querySelector('.mtools');
if(tools){
  tools.hidden=false;
  var q=d.getElementById('q'),veg=d.getElementById('veg'),cnt=d.getElementById('count'),none=d.getElementById('noresults');
  var items=[].slice.call(d.querySelectorAll('.items li')),secs=[].slice.call(d.querySelectorAll('.msec'));
  var run=function(){var t=q.value.trim().toLowerCase(),v=veg.checked,n=0;
    items.forEach(function(li){var ok=(!t||li.getAttribute('data-name').indexOf(t)>-1)&&(!v||li.getAttribute('data-veg')==='1');li.hidden=!ok;if(ok)n++;});
    secs.forEach(function(s){s.hidden=!s.querySelector('li:not([hidden])');});
    none.hidden=n>0;cnt.textContent=(t||v)?(n+(n===1?' dish':' dishes')):'';};
  q.addEventListener('input',run);veg.addEventListener('change',run);
}
var bar=d.querySelector('.chips'),chips=d.querySelectorAll('.chips a[href^="#"]');
if(bar&&chips.length&&'IntersectionObserver' in window){
  var map={};chips.forEach(function(a){map[a.getAttribute('href').slice(1)]=a;});
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;var a=map[e.target.id];if(!a)return;
    chips.forEach(function(c){c.removeAttribute('aria-current');});a.setAttribute('aria-current','true');
    bar.scrollTo({left:Math.max(0,a.offsetLeft-bar.offsetLeft-24),behavior:'smooth'});});},{rootMargin:'-40% 0px -55% 0px'});
  d.querySelectorAll('.msec').forEach(function(s){io.observe(s);});
}
var top=d.querySelector('.totop');
if(top){top.hidden=false;var ft=d.querySelector('footer');var onS=function(){var nearEnd=ft&&ft.getBoundingClientRect().top<window.innerHeight;top.classList.toggle('show',window.scrollY>900&&!nearEnd);};window.addEventListener('scroll',onS,{passive:true});onS();}
var app=(location.search.match(/[?&]app=(swiggy|zomato|ownly)\b/)||[])[1];
if(app){d.querySelectorAll('.obtn[data-app="'+app+'"]').forEach(function(a){a.classList.add('pick');});}
})();
