import React, { forwardRef } from "react";
import { StyleSheet, TextInput as NativeTextInput, TextInputProps } from "react-native";
import { hasIosInputZoom, readableInputFontSize } from "@/utils/webInput";

export type TextInput = NativeTextInput;

/** Fix focus zoom before the first tap, without disabling user pinch zoom. */
export const TextInput = forwardRef<NativeTextInput, TextInputProps>(function TextInput(props, ref) {
  const needsFix = hasIosInputZoom(typeof navigator === "undefined" ? undefined : navigator);
  const style = needsFix
    ? [props.style, { fontSize: readableInputFontSize(StyleSheet.flatten(props.style)?.fontSize) }]
    : props.style;
  return <NativeTextInput {...props} ref={ref} style={style} />;
});
