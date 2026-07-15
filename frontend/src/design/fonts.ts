import {Text, TextInput} from "react-native";

export const appFontFamily = "PharmexaUIFont";

function injectWebFonts() {
  if (typeof document === "undefined") return;
  if (document.getElementById("pharmexa-fonts")) return;

  const style = document.createElement("style");
  style.id = "pharmexa-fonts";
  style.textContent = `
@font-face {
  font-family: "PharmexaUIFont";
  src: local("B Roya"), local("B Roya"), local("B Ferdosi"), local("B Nazanin"), local("B Mitra"), local("Nazanin"), local("Mitra");
  font-weight: 100 900;
  font-style: normal;
  unicode-range: U+0600-06FF, U+0750-077F, U+08A0-08FF, U+FB50-FDFF, U+FE70-FEFF;
}
@font-face {
  font-family: "PharmexaUIFont";
  src: local("Inter"), local("Manrope"), local("Aptos"), local("Calibri"), local("Carlito");
  font-weight: 100 900;
  font-style: normal;
  unicode-range: U+0000-00FF, U+0100-024F;
}
html,
body,
#root,
#root * {
  direction: rtl;
  text-align: right;
  font-family: "PharmexaUIFont", "B Roya", "B Ferdosi", Inter, Manrope, Aptos, Calibri, Carlito, "B Mitra", "B Nazanin", Arial, sans-serif !important;
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
