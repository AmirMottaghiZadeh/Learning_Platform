type CalculatorColors = { cardBg: string; ink: string; muted: string; accent: string; onAccent: string; softBg: string; trackBg: string };

/** The refresh call the source form runs on every keystroke, e.g.
 * `onkeyup="GuptaPostOpPneumonia_fx();"`. Every UpToDate calculator declares
 * its own `<name>_fx` this way and has no Calculate button at all -- values
 * are recomputed live. On a phone the keyboard hides the result and tapping
 * another field clears it (`onfocus` resets the output), so the sheet adds an
 * explicit button that calls this same function. */
export function calculatorRefreshCall(raw: string): string | null {
  const form = raw.match(/<form\b[^>]*>/i)?.[0];
  if (!form) return null;
  for (const attr of ["onkeyup", "onchange", "onsubmit"]) {
    const handler = form.match(new RegExp(`${attr}\\s*=\\s*["']([^"']*)["']`, "i"))?.[1];
    if (!handler) continue;
    const call = handler.match(/([A-Za-z_$][\w$]*)\s*\(/);
    if (call && !/^return$/i.test(call[1])) return call[1];
  }
  return null;
}

/** Keep the imported calculation and units intact, in an isolated document.
 * This document receives neither the app's JS bridge nor session credentials. */
export function referenceCalculatorPage(
  raw: string,
  colors: CalculatorColors,
  lang: "fa" | "en" = "en",
): string {
  const body = raw.match(/<body\b[^>]*>([\s\S]*?)<\/body\s*>/i)?.[1] ?? raw;
  const content = body
    // The sheet already shows the complete source title above the form.
    .replace(/<table\b[^>]*class=["'][^"']*\bmedCalcTitleBox\b[^"']*["'][^>]*>[\s\S]*?<\/table>\s*(?:(?:<br\s*\/?>|&nbsp;)\s*)*/gi, "")
    .replace(/<script\b[^>]*\bsrc\s*=[^>]*>[\s\S]*?<\/script\s*>/gi, "")
    .replace(/<script\b[^>]*>\s*undefined\s*;?\s*<\/script\s*>/gi, "")
    .replace(/<(?:base|meta|link)\b[^>]*>/gi, "")
    .replace(/<(iframe|object|embed)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, "");
  const csp = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'; frame-src 'none'; object-src 'none'";

  const refresh = calculatorRefreshCall(body);
  const label = lang === "fa" ? "محاسبه" : "Calculate";
  const resetLabel = lang === "fa" ? "پاک‌کردن" : "Reset";
  const hint = lang === "fa"
    ? "برای دیدن نتیجه، همهٔ مقادیر را کامل کنید."
    : "Fill in every field to see the result.";
  const emptyHint = lang === "fa"
    ? "نتیجه‌ای محاسبه نشد؛ ورودی‌ها را کامل کنید."
    : "Nothing was calculated yet; complete the inputs.";

  // The imported form is English and lays out label | input | unit in three
  // <td>s that rely on the source's own .ar/.al classes; flipping the document
  // to rtl reverses those columns and scatters the results. Only the bar we
  // add follows the app language.
  return `<!doctype html><html lang="en" dir="ltr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="${csp}">
<style>
*{box-sizing:border-box}html,body{margin:0;padding:0;max-width:100%;background:${colors.cardBg};color:${colors.ink};font:14px/1.8 -apple-system,"Segoe UI",sans-serif;overflow-wrap:break-word}
body{padding:8px 4px 92px}body>div,#topicText,#mc3k,form{width:100%!important;max-width:100%!important}
table{max-width:100%;border-collapse:collapse}td,th{padding:8px 4px;vertical-align:middle}table table{font-size:13px}
.ar,.ar42{text-align:right}.al,.alnw,.alnw5{text-align:left}.alnw,.alnw5{white-space:nowrap}.ac{text-align:center}
table[class*=Formuli]{width:100%}
input,select,textarea,button{font:inherit;max-width:100%;min-height:44px;color:${colors.ink};background:${colors.cardBg};border:1px solid ${colors.trackBg};border-radius:10px;padding:8px}
input[type=radio],input[type=checkbox]{min-height:22px;width:22px;height:22px;vertical-align:middle;accent-color:${colors.accent};padding:0}
input[type=button],input[type=submit],button{cursor:pointer;background:${colors.accent};color:${colors.onAccent};border:0;padding:10px 14px}
/* The imported forms carry their own "Reset form" button; the bar below is the
   control readers should use, so the duplicate is hidden. */
input[type=reset]{display:none}
input[readonly],textarea[readonly]{background:${colors.softBg};font-weight:600}
a{color:${colors.accent};cursor:pointer}p{margin:8px 0 14px}h1,h2,h3{font-size:17px;line-height:1.7}
:focus-visible{outline:3px solid ${colors.accent};outline-offset:2px}
.calcbar{position:fixed;inset-inline:0;bottom:0;z-index:50;display:flex;flex-direction:column;gap:6px;
  padding:10px 12px calc(10px + env(safe-area-inset-bottom,0px));background:${colors.cardBg};
  border-top:1px solid ${colors.trackBg};box-shadow:0 -6px 18px rgba(0,0,0,.08)}.calcbar .row{display:flex;gap:8px;width:100%}
.calcbar button{flex:1;min-height:46px;border:0;border-radius:12px;font-weight:700;font-size:15px;
  background:${colors.accent};color:${colors.onAccent};cursor:pointer}
.calcbar button.secondary{flex:0 0 auto;padding-inline:16px;background:${colors.softBg};color:${colors.ink};
  border:1px solid ${colors.trackBg};font-weight:600;font-size:13.5px}
.calcbar .hint{margin:0;font-size:11.5px;line-height:1.5;color:${colors.muted};display:none;
  unicode-bidi:plaintext;text-align:start}
.calcbar .hint.show{display:block}
.calcbar .hint.error{color:#B3261E}
</style>
<script>
function doOperation(op){
  var id=op&&String(op.contentId||"");
  if(!/^\\d+$/.test(id))return;
  var message=JSON.stringify({type:"reference-topic",id:id});
  if(window.ReactNativeWebView)window.ReactNativeWebView.postMessage(message);
  else window.parent.postMessage(message,"*");
}
document.addEventListener("click",function(e){
  var a=e.target.closest&&e.target.closest("a");if(!a)return;
  var id=a.getAttribute("data-topicid");if(id){e.preventDefault();doOperation({contentId:id});return;}
  var href=a.getAttribute("href")||"";
  if(href.charAt(0)==="#"){e.preventDefault();var target=document.getElementById(href.slice(1));if(target)target.scrollIntoView();return;}
  if(href)e.preventDefault();
});
</script></head><body>${content}
<div class="calcbar" id="calcbar" dir="${lang === "fa" ? "rtl" : "ltr"}">
  <p class="hint" id="calchint">${hint}</p>
  <div class="row">
    <button type="button" id="calculate">${label}</button>
    <button type="button" class="secondary" id="clear">${resetLabel}</button>
  </div>
</div>
<script>
(function(){
  var REFRESH=${refresh ? JSON.stringify(refresh) : "null"};
  var EMPTY=${JSON.stringify(emptyHint)};
  var hint=document.getElementById("calchint");

  function form(){ return document.querySelector("form"); }
  function showHint(text, isError){
    if(!hint)return;
    hint.textContent=text;
    hint.className="hint show"+(isError?" error":"");
  }
  function hideHint(){ if(hint) hint.className="hint"; }

  /** The source validates with alert() ("The minimum value for Height is
   * 100 cm."). Inside the sheet's sandboxed frame modal dialogs are blocked,
   * so those messages never reached the reader; showing them in the bar keeps
   * the validation usable. minMaxCheck defers its dialog by 100ms and can fire
   * while the browser restores old field values, so nothing is reported until
   * the reader has actually touched the form. */
  var touched=false;
  ["pointerdown","keydown","input","change"].forEach(function(type){
    document.addEventListener(type,function(){ touched=true; },true);
  });
  window.alert=function(message){
    if(touched) showHint(String(message==null?"":message),true);
  };
  window.confirm=function(){ return true; };
  // A validation message should not outlive the value that caused it. The
  // source listens on keyup/onchange, so clearing has to cover those too.
  ["input","change","keyup"].forEach(function(type){
    document.addEventListener(type,function(){ if(hint&&/ error$/.test(hint.className)) hideHint(); },true);
  });

  /** Every one of these forms writes its answer into a readonly "resultBold"
   * input (Terms_param, FIB4_param, PEF_param, ...). Only those count: the risk
   * tables next to them (rr1row*) carry fixed threshold labels even before
   * anything was computed, so reading them made an empty form look finished. */
  function resultSignature(){
    var parts=[];
    document.querySelectorAll("input[readonly], textarea[readonly]").forEach(function(el){
      var v=(el.value||"").trim(); if(v) parts.push(v);
    });
    return parts.join("|");
  }

  function run(){
    var f=form();
    // A focused number field has not fired onchange yet, and its onfocus had
    // cleared the output, so commit it before asking the calculator to run.
    var active=document.activeElement;
    if(active&&active.blur)active.blur();
    if(f){
      f.dispatchEvent(new Event("input",{bubbles:true}));
      f.dispatchEvent(new Event("change",{bubbles:true}));
    }
    try{
      if(REFRESH&&typeof window[REFRESH]==="function"){ window[REFRESH](); }
      else if(f){ f.dispatchEvent(new KeyboardEvent("keyup",{bubbles:true})); }
    }catch(err){ showHint(EMPTY,true); return; }
    var sig=resultSignature();
    if(!sig){ showHint(EMPTY,true); return; }
    hideHint();
    var target=document.querySelector("input[readonly]")||document.querySelector("[id^=rr]");
    if(target&&target.scrollIntoView){ target.scrollIntoView({block:"center",behavior:"smooth"}); }
  }

  document.getElementById("calculate").addEventListener("click",function(e){e.preventDefault();run();});
  document.getElementById("clear").addEventListener("click",function(e){
    e.preventDefault();
    var f=form(); if(f){ f.reset(); }
    hideHint();
  });
})();
</script>
</body></html>`;
}
