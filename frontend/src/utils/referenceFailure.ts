/** Public search errors must describe the failure without guessing its cause. */
export function referenceFailure(code?: string, status?: number, isFa = true): string {
  if (!isFa) {
    if (code === "SEARCH_CANCELLED") return "The search was stopped.";
    if (code === "AI_CREDIT_INSUFFICIENT") return "Top up your smart search credits to continue.";
    if (code === "AI_LAB_DISABLED" || code === "PREMIUM_REQUIRED") return "Smart search is not available with your current access.";
    if (code === "QUOTA_EXCEEDED") return "Your usage allowance is exhausted. Try again next period.";
    if (code === "TOO_MANY_QUESTIONS") return "Ask one question per search.";
    if (code === "EXPERIMENT_TIMEOUT") return "The search timed out. You can try again.";
    return "The search could not be completed. Try again or contact support if the problem persists.";
  }
  if (code === "AI_CREDIT_INSUFFICIENT") return "اعتبار سرچ هوشمند کافی نیست؛ از بخش مدیریت اعتبار، حساب خود را شارژ کنید.";
  if (code === "PREMIUM_REQUIRED") return "پلن شما شامل دسترسی لازم برای این جست‌وجو نیست؛ امکانات پلن و دسترسی منابع را بررسی کنید.";
  if (code === "QUOTA_EXCEEDED") return "سهمیهٔ استفاده از این قابلیت یا منبع تمام شده است؛ پس از شروع دورهٔ بعد دوباره تلاش کنید.";
  if (code === "AI_LAB_DISABLED") return "سرچ هوشمند برای حساب شما فعال نیست.";
  if (code === "EXPERIMENT_TIMEOUT") return "مهلت این جست‌وجو تمام شد. می‌توانید دوباره تلاش کنید.";
  if (code === "SEARCH_REQUEST_LIMIT") return "این جست‌وجو به پاسخ کافی نرسید. می‌توانید دوباره تلاش کنید.";
  if (code === "TOO_MANY_QUESTIONS") return "لطفاً در هر جست‌وجو یک سؤال مطرح کنید.";
  if (code === "EXPERIMENT_EXPIRED") return "جست‌وجوی قبلی متوقف یا منقضی شد. می‌توانید دوباره سؤال بپرسید.";
  if (code === "PROVIDER_HTTP_ERROR" || code === "PROVIDER_UNAVAILABLE") return "ارتباط با سرویس جست‌وجو برقرار نشد. کمی بعد دوباره تلاش کنید.";
  if (code === "REFERENCE_INDEX_NOT_READY" || code === "REFERENCE_INDEX_STALE") return "منبع سرچ هوشمند باید در سرور آماده‌سازی شود. کمی بعد دوباره تلاش کنید.";
  if (code === "SOURCE_UNAVAILABLE") return "منبع UpToDate در سرور در دسترس نیست.";
  if (code === "HYBRID_INDEX_NOT_READY" || code === "HYBRID_INDEX_STALE" || code === "HYBRID_EMBEDDINGS_NOT_READY") return "نمایهٔ سرچ هوشمند هنوز آماده نیست. کمی بعد دوباره تلاش کنید.";
  if (["EMBEDDING_KEY_NOT_CONFIGURED", "EMBEDDING_KEY_PROVIDER_MISMATCH", "REMOTE_EMBEDDING_DISABLED", "EMBEDDING_PROFILE_CHANGED"].includes(code ?? "")) return "تنظیمات بازیابی منابع در سرور نیاز به بررسی دارد؛ به پشتیبانی اطلاع دهید.";
  if (code === "SEARCH_CANCELLED") return "جست‌وجو به درخواست شما متوقف شد.";
  if (["INVALID_MODEL_OUTPUT", "INVALID_SEARCH_TOOL_ARGUMENTS", "UNEXPECTED_SEARCH_TOOL", "MODEL_OUTPUT_TRUNCATED", "INVALID_PROVIDER_RESPONSE"].includes(code ?? "")) return "پاسخ سرویس قابل پردازش نبود. دوباره تلاش کنید؛ اگر تکرار شد، به پشتیبانی اطلاع دهید.";
  if (["MODEL_MISMATCH", "INVALID_RESPONSE_MODEL_CONFIGURATION", "INVALID_MODEL_CONFIGURATION", "INVALID_REASONING_EFFORT", "INVALID_PROVIDER_URL"].includes(code ?? "")) return "تنظیمات سرویس جست‌وجو در سرور نیاز به بررسی دارد؛ به پشتیبانی اطلاع دهید.";
  if (code === "SEARCH_JOB_STATE_UNAVAILABLE") return "اطلاعات این جست‌وجو قابل بازیابی نیست. سؤال را دوباره ارسال کنید؛ اگر تکرار شد، به پشتیبانی اطلاع دهید.";
  if (status === 401 || code === "KEY_NOT_CONFIGURED") return "سرویس سرچ هوشمند فعلاً در دسترس نیست.";
  if (code === "EXPERIMENT_FAILED") return "جست‌وجو به‌دلیل خطای پردازش کامل نشد. دوباره تلاش کنید؛ اگر تکرار شد، به پشتیبانی اطلاع دهید.";
  return "جست‌وجو کامل نشد. دوباره تلاش کنید؛ اگر تکرار شد، به پشتیبانی اطلاع دهید.";
}
