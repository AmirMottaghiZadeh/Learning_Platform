"""Offline, private clinical-review worksheet. No automatic human approval."""
from html import escape
import json

from . import evaluation


def worksheet(reports):
    rows, seen = [], set()
    for report in reports:
        for row in report.get("runs", []):
            key = (row.get("case_id"), row.get("response_digest"))
            if row.get("response_digest_schema") != 2 or not isinstance(key[0], str) or not isinstance(key[1], str):
                raise evaluation.EvaluationError("UNBOUND_REVIEW_RESPONSE")
            if key not in seen:
                seen.add(key)
                rows.append(row)
    cards = []
    for number, row in enumerate(rows):
        items = [item for part in row.get("result", {}).get("parts", []) for item in part.get("items", [])]
        expected = row.get("expect") == "abstain" or row.get("assessment", {}).get("expected_sources_matched", False)
        parts = row.get("result", {}).get("parts", [])
        explanations = ''.join('<section><h3>' + escape(str(part.get("question_fa", "")))
            + '</h3><p class="meta">' + escape(str(part.get("status", ""))) + '</p><p>'
            + escape(str(part.get("overview_fa") or part.get("clarification_fa") or "بدون توضیح فارسی"))
            + '</p></section>' for part in parts)
        expected_sources = ''.join('<li dir="auto">' + escape(str(source.get("title", source.get("article_id", ""))))
            + ' — ' + escape(' / '.join(source.get("headings", []))) + '</li>'
            for source in row.get("expected_sources", []))
        sources = []
        for item in items:
            sources.append('<section class="source"><h3 dir="auto">' + escape(str(item.get("title", "")))
                + '</h3><p dir="auto">' + escape(str(item.get("section", ""))) + '</p><p>'
                + escape(str(item.get("summary_fa", ""))) + '</p><blockquote dir="ltr" lang="en">'
                + escape(str(item.get("quote", ""))) + '</blockquote><details><summary>شناسه و مقصد منبع</summary><pre dir="ltr">'
                + escape(json.dumps(item.get("target", {}), ensure_ascii=False, indent=2)) + '</pre></details></section>')
        cards.append(f'<article data-case="{escape(row["case_id"], quote=True)}" data-digest="{escape(row["response_digest"], quote=True)}" data-match="{str(bool(expected)).lower()}">'
            + f'<h2>{number + 1}. ' + escape(str(row.get("question", row["case_id"]))) + '</h2><p class="meta">'
            + escape(row["case_id"]) + ' · ' + escape(str(row.get("status"))) + '</p>'
            + '<p class="meta">کفایت ساختاری ماشینی: '
            + ('کامل' if row.get("assessment", {}).get("machine_complete") else 'کامل نیست / امتناع') + '</p>'
            + ('<details><summary>مقاله و بخش مرجع آزمون</summary><ul>' + expected_sources + '</ul></details>' if expected_sources else '')
            + ('<p class="notice">بخش انتخاب‌شده با فهرست مرجع آزمون تطبیق ندارد؛ پذیرش منبع جایگزین باید مستدل باشد.</p>' if not expected else '')
            + explanations
            + (''.join(sources) or '<p>ارجاعی ثبت نشده است. کد: ' + escape(str(row.get("error_code", "بدون خطای ثبت‌شده"))) + '</p>')
            + '<fieldset><legend>نظر مستقل شما</legend>'
            + f'<label><input type="radio" name="r{number}" value="" checked>هنوز بررسی نکرده‌ام</label>'
            + f'<label><input type="radio" name="r{number}" value="yes">کافی و درست</label>'
            + f'<label><input type="radio" name="r{number}" value="no">نیازمند اصلاح / پاسخ ناکافی</label></fieldset>'
            + '<label><input type="checkbox" class="alternative">منبع جایگزین را با وجود اختلاف فهرست مرجع می‌پذیرم</label>'
            + '<label>دلیل پذیرش منبع جایگزین / یادداشت بازبینی<textarea rows="3"></textarea></label></article>')
    return '''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; img-src data:">
<title>بازبینی مستقل سرچ هوشمند</title><style>
body{margin:0;background:#f3f6f4;color:#19382f;font:16px/1.9 Tahoma,sans-serif}main,header{max-width:980px;margin:auto;padding:24px}
header{background:#fff;position:sticky;top:0;border-bottom:1px solid #d8e3de}h1{font-size:23px;margin:0}h2{font-size:19px}
article{background:#fff;border:1px solid #d8e3de;border-radius:16px;padding:24px;margin:20px 0}.source{border-top:1px solid #d8e3de;margin-top:18px;padding-top:12px}
blockquote{background:#f2f5f7;color:#172b3a;margin:16px 0;padding:18px;white-space:pre-wrap;font:16px/1.7 Georgia,serif}
label{display:block;margin:10px 0}textarea{display:block;width:95%;font:inherit;padding:10px}button{background:#145747;color:#fff;padding:10px 18px;border:0;border-radius:8px;font:inherit;cursor:pointer}
fieldset{border:1px solid #d8e3de}.notice{color:#8b3521;background:#fff1eb;padding:12px}.meta{font-size:13px;color:#526b61}pre{white-space:pre-wrap;overflow-wrap:anywhere}
</style><header><h1>بازبینی مستقل پاسخ‌های سرچ هوشمند</h1><p>متن فارسی، کفایت پاسخ، جمعیت، دوز و قیدهای متن اصلی را بررسی کنید. بررسی ماشینی به معنی تأیید بالینی نیست.</p>
<label>نام بازبین <input id="reviewer" autocomplete="name"></label><button id="export">دریافت فایل نظرها</button>
<label>ادامه از فایل نظرهای قبلی <input id="import" type="file" accept="application/json"></label><p id="status"></p></header><main>''' + ''.join(cards) + '''</main><script>
const cards=[...document.querySelectorAll('article')];
document.querySelector('#export').onclick=()=>{
 const reviewer=document.querySelector('#reviewer').value.trim();if(!reviewer){alert('نام بازبین را وارد کنید.');return;}
 const reviews=[];for(const card of cards){const value=card.querySelector('input[type=radio]:checked').value;if(!value)continue;
 const yes=value==='yes',alternative=yes&&card.querySelector('.alternative').checked,reason=card.querySelector('textarea').value.trim();
 if(yes&&card.dataset.match==='false'&&!alternative){alert('برای پذیرش پاسخ با منبع متفاوت، گزینهٔ منبع جایگزین را مشخص کنید.');return;}
 if(alternative&&reason.length<15){alert('دلیل پذیرش منبع جایگزین را کامل بنویسید.');return;}
 reviews.push({case_id:card.dataset.case,response_digest:card.dataset.digest,reviewer,correct_and_sufficient:yes,accept_alternative_sources:alternative,source_review_reason:reason});}
 const url=URL.createObjectURL(new Blob([JSON.stringify({schema:1,reviews},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='reference-reviews.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 document.querySelector('#status').textContent=`${reviews.length} نظر صریح ذخیره شد. موارد بررسی‌نشده تأیید نشده‌اند.`;
};
document.querySelector('#import').onchange=async event=>{try{const data=JSON.parse(await event.target.files[0].text());if(data.schema!==1||!Array.isArray(data.reviews))throw Error();
for(const review of data.reviews){const card=cards.find(c=>c.dataset.case===review.case_id&&c.dataset.digest===review.response_digest);if(!card||typeof review.correct_and_sufficient!=='boolean')continue;
card.querySelector(`input[value=${review.correct_and_sufficient?'yes':'no'}]`).checked=true;card.querySelector('.alternative').checked=review.accept_alternative_sources===true;
card.querySelector('textarea').value=review.source_review_reason||'';document.querySelector('#reviewer').value=review.reviewer||'';}}catch{alert('فایل نظرها معتبر نیست.');}};
</script></html>'''
