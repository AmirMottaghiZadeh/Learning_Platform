import React, { forwardRef } from "react";
import { TextInput as NativeTextInput, TextInputProps } from "react-native";

import { useInputTypography } from "@/theme/useInputTypography";

export type TextInput = NativeTextInput;

export const TextInput = forwardRef<NativeTextInput, TextInputProps>(function TextInput(props, ref) {
  const typography = useInputTypography(props);
  return <NativeTextInput {...props} ref={ref} style={[props.style, typography]} />;
});
