jest.mock("@react-native-async-storage/async-storage", () => ({
  __esModule: true,
  default: {
    clear: jest.fn(() => Promise.resolve()),
    getAllKeys: jest.fn(() => Promise.resolve([])),
    getItem: jest.fn(() => Promise.resolve(null)),
    multiGet: jest.fn(() => Promise.resolve([])),
    multiRemove: jest.fn(() => Promise.resolve()),
    multiSet: jest.fn(() => Promise.resolve()),
    removeItem: jest.fn(() => Promise.resolve()),
    setItem: jest.fn(() => Promise.resolve()),
  },
}));
jest.mock("@react-native-community/slider", () => "Slider");

jest.mock("lucide-react-native", () => {
  const React = require("react");
  const {View} = require("react-native");
  const Icon = (props: object) => React.createElement(View, props);

  return new Proxy(
    {},
    {
      get: () => Icon,
    },
  );
});

jest.mock("react-native-svg", () => {
  const React = require("react");
  const {View} = require("react-native");
  const Svg = ({children, ...props}: {children?: React.ReactNode}) =>
    React.createElement(View, props, children);

  return {
    __esModule: true,
    default: Svg,
    Circle: View,
  };
});
