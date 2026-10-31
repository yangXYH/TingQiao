// Run before the stylesheet so a saved dark theme never flashes a light page.
(() => {
 const key='tingqiao-theme',root=document.documentElement;
 const system=window.matchMedia('(prefers-color-scheme: dark)');
 let saved=null;
 try{saved=localStorage.getItem(key);}catch{}
 let manual=saved==='dark'||saved==='light';
 function apply(theme){
  root.dataset.theme=theme;
  const meta=document.querySelector('meta[name="theme-color"]');
  if(meta)meta.content=theme==='dark'?'#0d0d0d':'#f6f5f1';
  document.dispatchEvent(new CustomEvent('tingqiao-theme-change'));
 }
 apply(manual?saved:system.matches?'dark':'light');
 window.TingqiaoTheme={
  current:()=>root.dataset.theme,
  toggle(){
   const theme=root.dataset.theme==='dark'?'light':'dark';
   manual=true;
   try{localStorage.setItem(key,theme);}catch{}
   apply(theme);
  }
 };
 system.addEventListener('change',e=>{if(!manual)apply(e.matches?'dark':'light');});
 window.addEventListener('storage',e=>{
  if(e.key!==key)return;
  manual=e.newValue==='dark'||e.newValue==='light';
  apply(manual?e.newValue:system.matches?'dark':'light');
 });
})();
