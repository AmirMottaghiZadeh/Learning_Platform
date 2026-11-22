import React, { useState } from "react";
import { Image, Platform, Pressable, View } from "react-native";
import { WebView } from "react-native-webview";
import { useQuery } from "@tanstack/react-query";
import { ReferenceMedia, referenceMediaApi } from "@/api/referenceMedia";
import { ApiError } from "@/api/client";
import { AppText } from "@/components/primitives/AppText";
import { MediaViewer } from "@/components/article/MediaViewer";
import { mediaPage } from "@/components/article/mediaPage";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

function mediaId(item: ReferenceMedia) {
  return `${item.article_id}:${item.key}`;
}

export function ReferenceMediaCards({ items, onOpenSource }: { items: ReferenceMedia[]; onOpenSource?: (item: ReferenceMedia) => void }) {
  const { isFa,row }=useLang();const {colors,isDark}=useTheme();
  const [selected,setSelected]=useState("");const [full,setFull]=useState(false);
  const item=items.find(v => mediaId(v)===selected) ?? items[0];
  const query=useQuery({queryKey:["reference-media",item?.article_id,item?.key,item?.content_hash,item?.graphic_hash],
    queryFn:() => referenceMediaApi.get(item),enabled:!!item,staleTime:60000,retry:false});
  if(!item)return null;
  const data=query.data;
  const stale=query.error instanceof ApiError && query.error.status===409;
  const html=data?.kind==="table" ? mediaPage(data,{background:colors.softBg,ink:colors.ink,muted:colors.muted,
    headerBg:colors.trackBg,line:isDark?"#85998b":"#26382e",cellBg:colors.cardBg,firstColumnBg:isDark?"#303d34":"#d4dcd3"}) : "";
  return <View testID="reference-media" style={{gap:10}}>
    <View accessibilityRole="tablist" style={{flexDirection:row,flexWrap:"wrap",gap:5,padding:4,borderRadius:12,backgroundColor:colors.softBg}}>
      {items.map((entry,i) => {
        const id = mediaId(entry);
        const active = id === mediaId(item);
        return <Pressable key={id} accessibilityRole="tab" accessibilityState={{selected:active}} accessibilityLabel={entry.title}
          onPress={() => setSelected(id)} style={{flexGrow:1,minHeight:44,minWidth:60,alignItems:"center",justifyContent:"center",borderRadius:9,
            backgroundColor:active ? colors.cardBg : "transparent"}}>
          <AppText size={12} weight="800" color={active ? colors.accent : colors.muted}>{entry.kind==="table" ? isFa ? "جدول" : "Table" : isFa ? "شکل" : "Figure"}{items.length>1 ? ` ${i+1}` : ""}</AppText>
        </Pressable>;
      })}
    </View>
    <View style={{borderRadius:14,overflow:"hidden",backgroundColor:colors.softBg}}>
      {query.isLoading ? <View style={{height:150,justifyContent:"center",padding:16}}><AppText muted size={12}>{isFa ? "دریافت جدول یا تصویر منبع…" : "Loading original media…"}</AppText></View>
        : query.isError ? <Pressable disabled={stale} onPress={() => void query.refetch()} style={{padding:16}}><AppText color={colors.denyLabel} size={12}>{stale ? isFa ? "نسخهٔ منبع تغییر کرده؛ جست‌وجو را دوباره انجام دهید." : "The source changed. Please search again." : isFa ? "دریافت منبع انجام نشد؛ تلاش دوباره" : "Could not load media. Retry"}</AppText></Pressable>
          : data?.kind==="image" ? <Pressable onPress={() => setFull(true)} accessibilityRole="button"><Image source={{uri:data.src}} accessibilityLabel={data.alt||item.title} resizeMode="contain" style={{width:"100%",height:180}} /></Pressable>
            : data ? <View style={{height:180}}>{Platform.OS==="web" ? <iframe title={item.title} sandbox="allow-scripts" srcDoc={html} style={{width:"100%",height:"100%",border:0}} />
              : <WebView source={{html}} style={{flex:1,backgroundColor:colors.softBg}} originWhitelist={["*"]} />}</View> : null}
    </View>
    <AppText size={11} muted style={{writingDirection:"ltr",textAlign:"left"}}>{item.title}</AppText>
    <View style={{ flexDirection: row, flexWrap: "wrap", gap: 12 }}>
      {data ? <Pressable accessibilityRole="button" onPress={() => setFull(true)} style={{minHeight:44,justifyContent:"center"}}><AppText color={colors.accent} size={12} weight="700">{isFa ? "نمایش کامل و بزرگ‌نمایی" : "Open full size"}</AppText></Pressable> : null}
      {onOpenSource ? <Pressable testID="reference-media-source" accessibilityRole="link" onPress={() => onOpenSource(item)} style={{ minHeight: 44, justifyContent: "center" }}>
        <AppText size={12} weight="700" color={colors.accent}>{isFa ? "باز کردن در مقالهٔ اصلی" : "Open in the original article"}</AppText>
      </Pressable> : null}
    </View>
    <MediaViewer reference media={full ? data??null : null} onClose={() => setFull(false)} />
  </View>;
}
