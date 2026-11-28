import React, { createContext, useContext } from "react";
import { ViewProps } from "react-native";

import { useTheme } from "@/theme/ThemeProvider";
import { radius, spacing } from "@/theme/tokens";
import { SquircleView } from "./SquircleView";

type Props = ViewProps & { padded?: boolean; raised?: boolean; soft?: boolean };
export const CardSurface = createContext(false);

export function Card({ padded = true, raised = true, soft, style, children, ...rest }: Props) {
  const { colors, shadows } = useTheme();
  const nested = useContext(CardSurface);
  return (
    <SquircleView
      {...rest}
      style={[
        {
          backgroundColor: soft || nested ? colors.softBg : colors.cardBg,
          borderRadius: radius.card,
          padding: padded ? spacing.lg : 0,
        },
        raised && !nested && shadows.surface,
        style,
        { borderWidth: 0 },
        nested && { boxShadow: "none", shadowOpacity: 0, elevation: 0 },
      ]}
    >
      <CardSurface.Provider value>{children}</CardSurface.Provider>
    </SquircleView>
  );
}
