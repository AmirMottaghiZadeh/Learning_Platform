import React, { useMemo, useState } from "react";
import { Pressable, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { ScreenChrome } from "@/components/ScreenChrome";
import { PediatricChoice } from "@/components/calculator/PediatricChoice";
import { Metric, PediatricDoseResult, PediatricNotice, PediatricSource } from "@/components/calculator/PediatricResult";
import { AppText } from "@/components/primitives/AppText";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { Input } from "@/components/primitives/Input";
import { LoadingState } from "@/components/primitives/LoadingState";
import { Screen } from "@/components/primitives/Screen";
import { useLang } from "@/i18n/LanguageProvider";
import { useBackInterceptor } from "@/navigation/back";
import { fetchPediatricDataset, PediatricDatasetVersionError } from "@/pediatricDose/api";
import Engine from "@/pediatricDose/engine";
import { PEDIATRIC_DOSE_NAME, PEDIATRIC_DOSE_NAME_FA } from "@/pediatricDose/catalog";
import { emptyDraft, errorText, needsFrequency, patientInput, selectedResults, validatePatient } from "@/pediatricDose/model";
import { DRUG_NAMES_FA } from "@/pediatricDose/names";
import type { AgeUnit, PediatricDraft, Source } from "@/pediatricDose/types";
import { useAuth } from "@/store/auth";
import { useNav } from "@/store/nav";
import { useTheme } from "@/theme/ThemeProvider";

export function PediatricDoseScreen() {
  const { isFa, row, n } = useLang();
  const text = (fa: string, en: string) => isFa ? fa : en;
  const { colors } = useTheme();
  const goBack = useNav(s => s.goBack);
  const navigate = useNav(s => s.navigate);
  const saved = useNav(s => s.params.pediatricDraft) as PediatricDraft | undefined;
  const [draft, setDraft] = useState<PediatricDraft>(() => saved ? { ...saved } : emptyDraft());
  const [search, setSearch] = useState("");
  const [choosing, setChoosing] = useState(!draft.drugId);
  const [showErrors, setShowErrors] = useState(false);
  const userId = useAuth(s => s.user?.id);
  const query = useQuery({
    queryKey: ["pediatric-dose", userId], queryFn: fetchPediatricDataset,
    staleTime: 0, refetchOnMount: "always", refetchOnWindowFocus: false, retry: false,
  });
  const drug = query.data?.drugs.find(d => d.id === draft.drugId);
  const patient = useMemo(() => validatePatient(draft), [draft]);
  const calculation = useMemo(() => drug ? Engine.calculate(drug, patientInput(draft)) : null, [drug, draft]);
  const regimen = calculation?.regimens.find(r => r.id === draft.regimenId);
  const rawRegimen = drug?.regimens.find(r => r.id === draft.regimenId);
  const results = selectedResults(rawRegimen, regimen, draft);
  const requireGA = !!drug && Engine.needsGA(drug, patient.ctx?.ageDays ?? null);
  const stepBack = () => { setShowErrors(false); setDraft(d => ({ ...d, step: d.step === 3 ? 2 : 1 })); };
  useBackInterceptor(draft.step > 1, stepBack);
  const back = draft.step > 1 ? stepBack : goBack;
  const canCalculate = !!drug && !!regimen && !!draft.productId && !calculation?.errors.length &&
    (!needsFrequency(rawRegimen, regimen) || !!draft.frequency) && results.length > 0;
  const setPatientField = (field: "age" | "weight" | "ga" | "ageUnit", value: string) => {
    setDraft(d => ({ ...d, [field]: value, regimenId: "", productId: "", frequency: "" }));
    setShowErrors(false);
  };
  const reset = () => {
    setDraft(emptyDraft()); setSearch(""); setChoosing(true); setShowErrors(false);
    const { pediatricDraft: _old, ...params } = useNav.getState().params;
    useNav.setState({ params });
  };
  const openSource = (source: Source) => {
    // Only ephemeral navigation memory, so back from the reader restores the
    // reviewed patient. Neither browser history nor persistent stores get PHI.
    useNav.setState({ params: { ...useNav.getState().params, pediatricDraft: { ...draft } } });
    navigate("uptodateArticle", { id: source.contentId, title: source.title });
  };
  const title = isFa ? PEDIATRIC_DOSE_NAME_FA : PEDIATRIC_DOSE_NAME;
  const chrome = <>
    <ScreenChrome title={title} onBack={back} />
    <AppText muted size={12} style={{ marginTop: -8, marginBottom: 14, writingDirection: isFa ? "ltr" : "rtl", textAlign: isFa ? "left" : "right" }}>
      {isFa ? PEDIATRIC_DOSE_NAME : PEDIATRIC_DOSE_NAME_FA}
    </AppText>
  </>;
  if (query.isPending || query.isFetching) return <Screen>{chrome}<LoadingState /></Screen>;
  if (query.isError || !query.data) {
    const error = query.error;
    const message = error instanceof PediatricDatasetVersionError
      ? text("نسخهٔ داده با موتور این نسخهٔ اپ سازگار نیست؛ اپ را به‌روز کنید.", "The dataset requires a different dose engine. Update the app to continue.")
      : error instanceof ApiError && error.status === 402
      ? text("پلن شما دسترسی یا سهمیهٔ کافی برای ماشین‌حساب‌ها ندارد.", "Your plan does not include this calculator or its allowance is exhausted.")
      : text("دریافت داده‌های تنظیم دوز ممکن نشد. اتصال را بررسی و دوباره تلاش کنید.", "Could not load pediatric dosing data. Check your connection and retry.");
    return <Screen>{chrome}<Card style={{ gap: 14 }}><PediatricNotice error>{message}</PediatricNotice>
      {error instanceof ApiError && error.status === 402 && <Button label={text("مشاهدهٔ پلن‌ها", "View plans")} onPress={() => navigate("plans")} />}
      <Button variant="secondary" label={text("تلاش دوباره", "Retry")} onPress={() => { void query.refetch(); }} />
    </Card></Screen>;
  }
  const name = drug ? (isFa ? DRUG_NAMES_FA[drug.id] || drug.name : drug.name) : "";
  const ageUnitLabel = ({ day: text("روز", "days"), month: text("ماه", "months"), year: text("سال", "years") })[draft.ageUnit];
  const errors = draft.step === 1 ? patient.errors : calculation?.errors ?? [];
  const gaInput = (requireGA || !!draft.ga.trim()) && <View style={{ gap: 7 }}>
    <AppText weight="700" size={13}>{text("سن حاملگی هنگام تولد · هفته", "Gestational age at birth · weeks")}</AppText>
    <Input accessibilityLabel={text("سن حاملگی هنگام تولد", "Gestational age at birth")} value={draft.ga} onChangeText={value => setPatientField("ga", value)} autoComplete="off" importantForAutofill="no" keyboardType="decimal-pad" style={{ writingDirection: "ltr", textAlign: "left" }} placeholder="22–44" />
    {requireGA && <AppText muted size={12}>{text("این ورودی برای رژیم‌های GA / PMA این دارو لازم است.", "This drug's GA / PMA regimens require this value.")}</AppText>}
  </View>;
  const patientSummary = <View style={{ backgroundColor: colors.leitnerActiveBg, padding: 13, borderRadius: 13, flexDirection: row, alignItems: "center", gap: 12 }}>
    <View style={{ flex: 1, gap: 3 }}>
      <AppText size={13}>{text("سن", "Age")}: {draft.age} {ageUnitLabel} · {text("وزن", "Weight")}: {draft.weight} kg</AppText>
      {draft.ga && <AppText muted size={12}>{text("سن حاملگی هنگام تولد", "Gestational age at birth")}: {draft.ga} {text("هفته", "weeks")}</AppText>}
    </View>
    <Pressable accessibilityRole="button" onPress={() => setDraft(d => ({ ...d, step: 1 }))} style={{ paddingVertical: 8 }}>
      <AppText weight="700" size={13} color={colors.accent}>{text("ویرایش", "Edit")}</AppText>
    </Pressable>
  </View>;
  return <Screen key={draft.step} contentStyle={{ gap: 14 }}>
    {chrome}
    <View style={{ flexDirection: row, justifyContent: "space-between", borderBottomWidth: 1, borderBottomColor: colors.trackBg, paddingBottom: 13 }}>
      {[text("کودک", "Patient"), text("دارو", "Drug"), text("نتیجه", "Result")].map((label, index) => <Pressable key={index} accessibilityRole="button" disabled={index + 1 > draft.step}
        onPress={() => { setShowErrors(false); setDraft(d => ({ ...d, step: index + 1 as 1 | 2 | 3 })); }}
        style={{ flexDirection: row, alignItems: "center", gap: 7, minHeight: 40 }}>
        <View style={{ width: 25, height: 25, borderRadius: 13, backgroundColor: index + 1 === draft.step ? colors.accent : colors.softBg, alignItems: "center", justifyContent: "center" }}>
          <AppText size={12} weight="800" color={index + 1 === draft.step ? colors.onAccent : colors.muted}>{n(index + 1)}</AppText>
        </View>
        <AppText size={13} weight="700" color={index + 1 === draft.step ? colors.accent : colors.muted}>{label}</AppText>
      </Pressable>)}
    </View>
    {draft.step === 1 ? <>
      <AppText weight="800" size={21}>{text("ابتدا مشخصات کودک", "Start with the patient")}</AppText>
      <AppText muted size={13}>{text("سن و وزن، مبنای انتخاب رژیم هستند.", "Age and weight determine applicable regimens.")}</AppText>
      <Card raised={false} style={{ gap: 14 }}>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
          <AppText weight="800" size={15}>{text("مشخصات کودک", "Patient details")}</AppText>
          <Pressable accessibilityRole="button" onPress={reset} style={{ paddingVertical: 8 }}><AppText weight="700" size={13} color={colors.accent}>{text("بیمار جدید", "New patient")}</AppText></Pressable>
        </View>
        <View style={{ flexDirection: row, gap: 12 }}>
          <View style={{ flex: 1, gap: 7 }}><AppText weight="700" size={13}>{text("وزن · کیلوگرم", "Weight · kg")}</AppText>
            <Input accessibilityLabel={text("وزن کودک", "Child weight")} value={draft.weight} onChangeText={value => setPatientField("weight", value)} autoComplete="off" importantForAutofill="no" keyboardType="decimal-pad" style={{ writingDirection: "ltr", textAlign: "left" }} placeholder="kg" />
          </View>
          <View style={{ flex: 1, gap: 7 }}><AppText weight="700" size={13}>{text("سن کودک", "Child age")}</AppText>
            <Input accessibilityLabel={text("سن کودک", "Child age")} value={draft.age} onChangeText={value => setPatientField("age", value)} autoComplete="off" importantForAutofill="no" keyboardType="decimal-pad" style={{ writingDirection: "ltr", textAlign: "left" }} placeholder={text("سن", "Age")} />
          </View>
        </View>
        <View style={{ flexDirection: row, borderRadius: 12, backgroundColor: colors.softBg, padding: 4 }}>
          {(["day", "month", "year"] as AgeUnit[]).map(unit => <Pressable key={unit} accessibilityRole="button" accessibilityState={{ selected: draft.ageUnit === unit }} onPress={() => setPatientField("ageUnit", unit)}
            style={{ flex: 1, minHeight: 40, alignItems: "center", justifyContent: "center", borderRadius: 10, backgroundColor: draft.ageUnit === unit ? colors.cardBg : "transparent" }}>
            <AppText weight="700" size={13} color={draft.ageUnit === unit ? colors.accent : colors.muted}>{({ day: text("روز", "Days"), month: text("ماه", "Months"), year: text("سال", "Years") })[unit]}</AppText>
          </Pressable>)}
        </View>
        {gaInput}
      </Card>
      <AppText muted size={13}>{text("این ابزار بر اساس سن، وزن و اندیکاسیون است؛ تنظیم دوز کلیوی یا کبدی را پوشش نمی‌دهد.", "This tool uses age, weight and indication; it does not cover renal or hepatic dose adjustment.")}</AppText>
      {showErrors && errors.map(error => <PediatricNotice key={error} error>{errorText(error, isFa)}</PediatricNotice>)}
      <Button label={text("ادامه · انتخاب دارو", "Continue · select a drug")} onPress={() => {
        if (patient.errors.length) setShowErrors(true);
        else { setShowErrors(false); setDraft(d => ({ ...d, step: 2 })); }
      }} />
    </> : draft.step === 2 ? <>
      {patientSummary}
      <Card raised={false} style={{ gap: 14 }}>
        <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between" }}>
          <AppText weight="800" size={15}>{text("دارو و اندیکاسیون", "Drug and indication")}</AppText>
          <AppText muted size={12}>{n(query.data.drugs.length)} {text("مدخل", "entries")}</AppText>
        </View>
        {drug && <View style={{ flexDirection: row, alignItems: "center", gap: 12 }}>
          <View style={{ flex: 1 }}><AppText weight="800" size={16}>{name}</AppText><AppText muted size={13} style={{ writingDirection: "ltr", textAlign: "left" }}>{drug.name}</AppText></View>
          <Pressable accessibilityRole="button" onPress={() => setChoosing(value => !value)} style={{ paddingVertical: 10 }}><AppText weight="700" size={13} color={colors.accent}>{text("تغییر دارو", "Change drug")}</AppText></Pressable>
        </View>}
        {(choosing || !drug) && <>
          <Input accessibilityLabel={text("جستجوی دارو", "Search drug")} value={search} onChangeText={setSearch} placeholder={text("نام فارسی یا انگلیسی دارو…", "Search drug name…")} />
          {query.data.drugs.filter(d => `${d.name} ${DRUG_NAMES_FA[d.id] || ""}`.toLowerCase().includes(search.trim().toLowerCase())).map(d => <Pressable key={d.id} accessibilityRole="button"
            onPress={() => { setDraft(value => ({ ...value, drugId: d.id, regimenId: "", productId: "", frequency: "" })); setChoosing(false); setSearch(""); setShowErrors(true); }}
            style={{ padding: 13, backgroundColor: colors.softBg, borderRadius: 12 }}>
            <AppText weight="700" size={14}>{isFa ? DRUG_NAMES_FA[d.id] || d.name : d.name}</AppText>
            {isFa && <AppText muted size={12} style={{ writingDirection: "ltr", textAlign: "left" }}>{d.name}</AppText>}
          </Pressable>)}
          {!query.data.drugs.some(d => `${d.name} ${DRUG_NAMES_FA[d.id] || ""}`.toLowerCase().includes(search.trim().toLowerCase())) && <AppText muted size={13}>{text("دارویی پیدا نشد.", "No drugs found.")}</AppText>}
        </>}
        {drug && <>
          {gaInput}
          {calculation?.errors.map(error => <PediatricNotice key={error} error>{errorText(error, isFa)}</PediatricNotice>)}
          {calculation && !calculation.errors.length && <>
            {calculation.messages.map((message, index) => <PediatricNotice key={index}>{message}</PediatricNotice>)}
            {!!calculation.regimens.length && <PediatricChoice label={text("اندیکاسیون و رژیم", "Indication and regimen")} value={draft.regimenId} placeholder={text("اندیکاسیون را انتخاب کنید", "Select an indication")}
              english options={calculation.regimens.map(r => ({ value: r.id, label: r.indication, detail: r.population }))}
              onChange={value => setDraft(d => ({ ...d, regimenId: value, productId: "", frequency: "" }))} />}
            {regimen && rawRegimen && <>
              <PediatricChoice label={text("فرآورده و قدرت", "Preparation and strength")} value={draft.productId} placeholder={text("فرآورده را انتخاب کنید", "Select a preparation")} english
                options={rawRegimen.products.map(id => ({ value: id, label: drug.products[id].label }))}
                onChange={value => setDraft(d => ({ ...d, productId: value }))} />
              {needsFrequency(rawRegimen, regimen) && <PediatricChoice label={text("گزینهٔ مصرف", "Administration option")} value={draft.frequency} placeholder={text("فاصلهٔ مصرف را انتخاب کنید", "Select a frequency")}
                options={regimen.results.map(result => ({ value: result.freq, label: isFa ? result.freqFa : result.freqEn }))}
                onChange={value => setDraft(d => ({ ...d, frequency: value }))} />}
              {regimen.limitedData && <PediatricNotice>{text("دادهٔ محدود برای این رژیم؛ متن منبع را بررسی کنید.", "Limited data for this regimen; review source text.")}</PediatricNotice>}
              {[...(calculation.drugNotes || []), ...regimen.warnings, ...regimen.notes].map((message, index) => <PediatricNotice key={index}>{message}</PediatricNotice>)}
            </>}
          </>}
        </>}
      </Card>
      <Button label={text("محاسبه و مشاهدهٔ نتیجه", "Calculate and review")} disabled={!canCalculate} onPress={() => setDraft(d => ({ ...d, step: 3 }))} />
    </> : <>
      {patientSummary}
      <View style={{ flexDirection: row, alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <AppText size={17} weight="800" style={{ flex: 1 }}>{name}</AppText>
        <Pressable accessibilityRole="button" onPress={() => setDraft(d => ({ ...d, step: 2 }))} style={{ paddingVertical: 10 }}><AppText weight="700" size={13} color={colors.accent}>{text("تغییر دارو / رژیم", "Change drug / regimen")}</AppText></Pressable>
      </View>
      {regimen && canCalculate ? <>
        <AppText muted size={13} style={{ writingDirection: "ltr", textAlign: "left" }}>{regimen.indication}</AppText>
        <AppText weight="800" size={15}>{text("نتیجهٔ تنظیم دوز", "Dose adjustment result")}</AppText>
        {regimen.limitedData && <PediatricNotice>{text("دادهٔ محدود؛ متن منبع را بررسی کنید.", "Limited data; review source text.")}</PediatricNotice>}
        {[...(calculation?.drugNotes || []), ...regimen.warnings, ...regimen.notes].map((message, index) => <PediatricNotice key={index}>{message}</PediatricNotice>)}
        {results.length > 1 && <AppText weight="700" size={14}>{text("گزینه‌ها / مراحل رژیم مطابق منبع", "Regimen options / stages as specified by the source")}</AppText>}
        {results.map((result, index) => <PediatricDoseResult key={`${result.stage}-${result.freq}-${index}`} result={result} product={result.products.find(p => p.productId === draft.productId)!}
          label={results.length > 1 ? `${result.stage || text("گزینهٔ مصرف", "Administration option")} · ${isFa ? result.freqFa : result.freqEn}` : undefined} />)}
        <Card raised={false} style={{ gap: 8 }}><Metric label={text("راه مصرف", "Route")} value={regimen.route} /><Metric label={text("جمعیت منبع", "Source population")} value={regimen.population} />
          {regimen.duration && <Metric label={text("مدت درمان", "Duration")} value={regimen.duration} />}
        </Card>
        <PediatricSource regimen={regimen} onOpen={openSource} />
      </> : <PediatricNotice error>{text("ورودی‌ها یا انتخاب رژیم نیاز به بررسی دوباره دارد.", "Review the patient inputs and regimen selection again.")}</PediatricNotice>}
      <Button label={text("بیمار جدید", "New patient")} variant="secondary" onPress={reset} />
    </>}
  </Screen>;
}
