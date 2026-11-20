type CalculatorColors = { cardBg: string; ink: string; muted: string; accent: string; onAccent: string; softBg: string; trackBg: string };

/** Keep the imported calculation and units intact, in an isolated document.
 * This document receives neither the app's JS bridge nor session credentials. */
export function referenceCalculatorPage(raw: string, colors: CalculatorColors): string {
  const body = raw.match(/<body\b[^>]*>([\s\S]*?)<\/body\s*>/i)?.[1] ?? raw;
  const content = body
    // The sheet already shows the complete source title above the form.
    .replace(/<table\b[^>]*class=["'][^"']*\bmedCalcTitleBox\b[^"']*["'][^>]*>[\s\S]*?<\/table>\s*(?:(?:<br\s*\/?>|&nbsp;)\s*)*/gi, "")
    .replace(/<script\b[^>]*\bsrc\s*=[^>]*>[\s\S]*?<\/script\s*>/gi, "")
    .replace(/<script\b[^>]*>\s*undefined\s*;?\s*<\/script\s*>/gi, "")
    .replace(/<(?:base|meta|link)\b[^>]*>/gi, "")
    .replace(/<(iframe|object|embed)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, "");
  const csp = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'; frame-src 'none'; object-src 'none'";
  return `<!doctype html><html lang="en" dir="ltr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="${csp}">
<style>
*{box-sizing:border-box}html,body{margin:0;padding:0;max-width:100%;background:${colors.cardBg};color:${colors.ink};font:14px/1.8 -apple-system,"Segoe UI",sans-serif;overflow-wrap:break-word}
body{padding:8px 4px 20px}body>div,#topicText,#mc3k,form{width:100%!important;max-width:100%!important}
table{width:100%;max-width:100%;border-collapse:collapse}td,th{padding:8px 4px;vertical-align:middle}table table{font-size:13px}
input,select,textarea,button{font:inherit;max-width:100%;min-height:44px;color:${colors.ink};background:${colors.cardBg};border:1px solid ${colors.trackBg};border-radius:10px;padding:8px}
input[type=radio],input[type=checkbox]{min-height:22px;width:22px;height:22px;vertical-align:middle;accent-color:${colors.accent};padding:0}
input[type=button],input[type=submit],button{cursor:pointer;background:${colors.accent};color:${colors.onAccent};border:0;padding:10px 14px}
input[type=reset]{background:${colors.softBg};color:${colors.ink};cursor:pointer}
input[readonly],textarea[readonly]{background:${colors.softBg};font-weight:600}
a{color:${colors.accent};cursor:pointer}p{margin:8px 0 14px}h1,h2,h3{font-size:17px;line-height:1.7}
:focus-visible{outline:3px solid ${colors.accent};outline-offset:2px}
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
</script></head><body>${content}</body></html>`;
}
