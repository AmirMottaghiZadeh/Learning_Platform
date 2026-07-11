import {Text, TextInput} from "react-native";

export const appFontFamily = "KGameUIFont";

function injectWebFonts() {
  if (typeof document === "undefined") return;
  if (document.getElementById("k-game-fonts")) return;

  const style = document.createElement("style");
  style.id = "k-game-fonts";
  style.textContent = `
@font-face {
  font-family: "KGameUIFont";
  src: local("B Nazanin"), local("B Mitra"), local("Nazanin"), local("Mitra");
  font-weight: 100 900;
  font-style: normal;
  unicode-range: U+0600-06FF, U+0750-077F, U+08A0-08FF, U+FB50-FDFF, U+FE70-FEFF;
}
@font-face {
  font-family: "KGameUIFont";
  src: local("Inter"), local("Manrope"), local("Aptos"), local("Calibri"), local("Carlito");
  font-weight: 100 900;
  font-style: normal;
  unicode-range: U+0000-00FF, U+0100-024F;
}
html,
body,
#root,
#root * {
  font-family: "KGameUIFont", Inter, Manrope, Aptos, Calibri, Carlito, "B Mitra", "B Nazanin", Arial, sans-serif !important;
  font-synthesis: weight;
}
`;
  document.head.appendChild(style);
}

function appendDefaultFont(component: typeof Text | typeof TextInput) {
  const target = component as unknown as {
    defaultProps?: {style?: unknown};
  };
  target.defaultProps = target.defaultProps ?? {};
  const existingStyle = target.defaultProps.style;
  target.defaultProps.style = existingStyle
    ? [existingStyle, {fontFamily: appFontFamily}]
    : {fontFamily: appFontFamily};
}

export function configureAppFonts() {
  injectWebFonts();
  appendDefaultFont(Text);
  appendDefaultFont(TextInput);
}
