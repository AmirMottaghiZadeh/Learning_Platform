import React from "react";
import { View, ViewProps } from "react-native";

import { useTheme } from "@/theme/ThemeProvider";
import { radius, spacing } from "@/theme/tokens";

type Props = ViewProps & { padded?: boolean; raised?: boolean; soft?: boolean };

export function Card({ padded = true, raised = true, soft, style, children, ...rest }: Props) {
  const { colors, shadows } = useTheme();
  return (
    <View
      {...rest}
      style={[
        {
          backgroundColor: soft ? colors.softBg : colors.cardBg,
          borderRadius: radius.card,
          borderWidth: 1,
          borderColor: colors.border,
          padding: padded ? spacing.lg : 0,
        },
        raised && shadows.raisedSm,
        style,
      ]}
    >
      {children}
    </View>
  );
}
