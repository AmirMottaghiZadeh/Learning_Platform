import React from "react";
import { View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useTheme } from "@/theme/ThemeProvider";
import { layout, radius } from "@/theme/tokens";
import { MeshBackground } from "./MeshBackground";

/**
 * The 430px framed shell from the design: a centred rounded card on a mesh
 * ground. On a phone it fills the screen; on wide web it shows the frame.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const { colors, shadows } = useTheme();

  return (
    <View style={{ flex: 1, backgroundColor: colors.meshBg }}>
      <MeshBackground />
      <SafeAreaView style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <View
          style={[
            {
              flex: 1,
              width: "100%",
              maxWidth: layout.appMaxWidth,
              backgroundColor: colors.appBg,
              borderRadius: radius.shell,
              overflow: "hidden",
            },
            shadows.shell,
          ]}
        >
          <View style={{ flex: 1 }}>{children}</View>
        </View>
      </SafeAreaView>
    </View>
  );
}
