import React, { forwardRef } from "react";
import { TextInput as NativeTextInput, TextInputProps } from "react-native";
import { useInputTypography } from "@/theme/useInputTypography";
import { hasIosInputZoom, readableInputFontSize } from "@/utils/webInput";

export type TextInput = NativeTextInput;

/** Fix focus zoom before the first tap, without disabling user pinch zoom. */
export const TextInput = forwardRef<NativeTextInput, TextInputProps>(function TextInput(props, ref) {
  const needsFix = hasIosInputZoom(typeof navigator === "undefined" ? undefined : navigator);
  const typography = useInputTypography(props);
  const zoom = needsFix ? { fontSize: readableInputFontSize(typography.fontSize) } : undefined;
  return <NativeTextInput {...props} ref={ref} style={[props.style, typography, zoom]} />;
});
