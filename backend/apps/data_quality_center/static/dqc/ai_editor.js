(function () {
  "use strict";
  var box=document.getElementById("ai-editor"),form=document.getElementById("edit-form");
  if(!box||!form||!document.getElementById("ai-run"))return;
  var fa=form.querySelector('[name="summary_fa"]'),en=form.querySelector('[name="summary_en"]');
  var preset=document.getElementById("ai-preset"),target=document.getElementById("ai-target"),instruction=document.getElementById("ai-instruction");
  var button=document.getElementById("ai-run"),status=document.getElementById("ai-status"),preview=document.getElementById("ai-preview"),candidate=null,snapshot=null;
  preset.addEventListener("change",function(){var action=preset.selectedOptions[0].dataset.action;target.disabled=action==="fa_to_en"||action==="en_to_fa";if(target.disabled)target.value=action==="fa_to_en"?"en":"fa";});
  button.addEventListener("click",async function(){
    if(button.disabled)return;
    var requestId=crypto.randomUUID();snapshot={fa:fa.value,en:en.value};candidate=null;preview.hidden=true;button.disabled=true;status.textContent="در حال آماده‌سازی پیشنهاد…";
    try{
      var response=await fetch(box.dataset.url,{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json","X-CSRFToken":form.querySelector('[name="csrfmiddlewaretoken"]').value},
        body:JSON.stringify({request_id:requestId,preset_id:preset.value||null,target:target.value,instruction:instruction.value,summary_fa:snapshot.fa,summary_en:snapshot.en})});
      if(!(response.headers.get('Content-Type')||'').includes('application/json'))throw Error("نشست ورود یا اتصال معتبر نیست؛ صفحه را تازه کنید.");
      var data=await response.json();if(!response.ok||!data.ok)throw Error(data.error||"ویرایش انجام نشد.");
      candidate=data;document.getElementById("ai-preview-fa").value=data.summary_fa;document.getElementById("ai-preview-en").value=data.summary_en;document.getElementById("ai-notes").textContent=data.notes;preview.hidden=false;status.textContent="پیشنهاد آمادهٔ بررسی است.";
    }catch(error){status.textContent=error.message||"ارتباط برقرار نشد؛ متن شما تغییر نکرد.";}finally{button.disabled=false;}
  });
  document.getElementById("ai-apply").addEventListener("click",function(){
    if(!candidate)return;
    if(fa.value!==snapshot.fa||en.value!==snapshot.en){status.textContent="متن پس از ارسال تغییر کرده؛ برای حفظ ویرایش جدید، دوباره پیشنهاد بگیرید.";return;}
    fa.value=candidate.summary_fa;en.value=candidate.summary_en;fa.dispatchEvent(new Event("input",{bubbles:true}));en.dispatchEvent(new Event("input",{bubbles:true}));
    preview.hidden=true;candidate=null;status.textContent="پیشنهاد در پیش‌نویس قرار گرفت؛ پیش از ارسال، بازبینی کنید.";
  });
  document.getElementById("ai-discard").addEventListener("click",function(){candidate=null;preview.hidden=true;status.textContent="پیشنهاد کنار گذاشته شد؛ متن تغییر نکرد.";});
  button.disabled=false;box.dataset.ready="true";
})();
