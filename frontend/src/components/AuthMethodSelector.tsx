import React from "react";
import { Pressable, View } from "react-native";
import { AppText } from "@/components/primitives/AppText";
import { useLang } from "@/i18n/LanguageProvider";
import { useTheme } from "@/theme/ThemeProvider";

export function AuthMethodSelector({value,onChange}:{value:"mobile"|"email";onChange:(value:"mobile"|"email")=>void}) {
  const {isFa,row}=useLang();const {colors}=useTheme();
  return <View accessibilityRole="tablist" testID="auth-methods" style={{flexDirection:row,padding:4,borderRadius:14,backgroundColor:colors.leitnerActiveBg,marginBottom:20}}>
    {(["mobile","email"] as const).map(method => <Pressable key={method} accessibilityRole="tab" aria-selected={value===method} accessibilityState={{selected:value===method}}
      testID={method==="email"?"auth-email-otp":"auth-method-mobile"} onPress={()=>onChange(method)}
      style={{flex:1,minHeight:58,borderRadius:11,alignItems:"center",justifyContent:"center",gap:3,backgroundColor:value===method?colors.cardBg:"transparent"}}>
      <AppText size={17} color={value===method?colors.accent:colors.muted}>{method==="mobile"?"☎":"✉"}</AppText>
      <AppText size={13} weight="800" color={value===method?colors.accent:colors.muted}>{method==="mobile"?isFa?"شمارهٔ موبایل":"Mobile number":isFa?"ایمیل":"Email"}</AppText>
    </Pressable>)}
  </View>;
}
