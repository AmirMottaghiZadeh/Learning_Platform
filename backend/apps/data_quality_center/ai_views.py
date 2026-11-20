import json
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.decorators.debug import sensitive_post_parameters,sensitive_variables
from apps.accounts.access import platform_admin
from apps.accounts.services import record_security_event
from . import ai_assist,access
from .ai_forms import AISettingsForm,AIPresetFormSet
from .models import AISettings,AIPromptPreset
from .views import capability_required,operator_required,_render,_section_or_404


@sensitive_post_parameters("api_key","config-api_key")
@capability_required(platform_admin)
@sensitive_variables()
def settings_view(request):
    config,_=AISettings.objects.get_or_create(pk=1)
    form=AISettingsForm(request.POST or None,instance=config,prefix="config")
    presets=AIPresetFormSet(request.POST or None,queryset=AIPromptPreset.objects.all(),prefix="prompts")
    if request.method=="POST" and form.is_valid() and presets.is_valid():
        with transaction.atomic():
            saved=form.save(commit=False)
            if form.cleaned_data["api_key"]:saved.encrypted_api_key=ai_assist.encrypt_key(form.cleaned_data["api_key"])
            elif form.cleaned_data["clear_api_key"]:saved.encrypted_api_key=""
            saved.updated_by=request.user;saved.save();presets.save()
            record_security_event("data_quality_ai_settings_changed",user=request.user,actor=request.user,request=request,
                metadata={"model":saved.model,"key_configured":bool(saved.encrypted_api_key)})
        messages.success(request,"تنظیمات و دستورهای ویرایش با AI ذخیره شدند.")
        return redirect("data_quality_center:ai_settings")
    return _render(request,"ai_settings.html","ai_settings",{"form":form,"presets":presets,"key_configured":bool(config.encrypted_api_key)})


@require_POST
@operator_required
@sensitive_variables()
def suggest_view(request,slug,field):
    if not access.can_edit(request.user):return JsonResponse({"ok":False,"error":"مجوز ویرایش ندارید."},status=403)
    section=_section_or_404(slug,field)
    try:
        if len(request.body)>200000:raise ai_assist.AIError("درخواست بیش از حد بزرگ است.")
        body=json.loads(request.body)
        if not isinstance(body,dict):raise ValueError
        run=ai_assist.suggest(request.user,section,body)
    except (ValueError,TypeError) as error:
        if not isinstance(error,ai_assist.AIError):error=ai_assist.AIError("درخواست معتبر نیست.")
        return JsonResponse({"ok":False,"error":str(error),"code":error.code},status=error.status)
    response=JsonResponse({"ok":True,"id":str(run.pk),"target":run.target,"summary_fa":run.summary_fa,
        "summary_en":run.summary_en,"notes":run.notes,"input_digest":run.input_digest})
    response["Cache-Control"]="private, no-store"
    return response
