import {fireEvent, screen, waitFor} from "@testing-library/react-native";
import React from "react";

import {useAuth} from "../store/auth";
import {renderWithQueryClient} from "../test/render";
import {AuthScreen} from "./AuthScreen";

jest.mock("../store/auth", () => ({
  useAuth: jest.fn(),
}));

const signIn = jest.fn();
const register = jest.fn();
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

function renderAuthScreen() {
  mockUseAuth.mockReturnValue({
    token: null,
    user: null,
    loading: false,
    error: null,
    signIn,
    register,
    signOut: jest.fn(),
  });
  return renderWithQueryClient(<AuthScreen />);
}

function submitLogin() {
  const loginButtons = screen.getAllByRole("button", {name: "ورود"});
  fireEvent.press(loginButtons[loginButtons.length - 1]);
}

describe("AuthScreen", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("blocks login submission when required credentials are empty", async () => {
    renderAuthScreen();

    submitLogin();

    expect(await screen.findByText("نام کاربری و رمز عبور الزامی است.")).toBeTruthy();
    expect(signIn).not.toHaveBeenCalled();
  });

  it("blocks registration when password confirmation does not match", async () => {
    renderAuthScreen();

    fireEvent.press(screen.getByRole("button", {name: "ثبت‌نام"}));
    fireEvent.changeText(screen.getByPlaceholderText("نام"), "علی");
    fireEvent.changeText(screen.getByPlaceholderText("نام خانوادگی"), "احمدی");
    fireEvent.changeText(screen.getByPlaceholderText("نام کاربری"), "learner");
    fireEvent.changeText(screen.getByPlaceholderText("ایمیل"), "learner@example.com");
    fireEvent.changeText(screen.getByPlaceholderText("کلمه عبور"), "secret");
    fireEvent.changeText(screen.getByPlaceholderText("تکرار کلمه عبور"), "different");
    fireEvent.press(screen.getByRole("button", {name: "ایجاد حساب"}));

    expect(await screen.findByText("کلمه عبور و تکرار آن یکسان نیست.")).toBeTruthy();
    expect(register).not.toHaveBeenCalled();
  });

  it("calls signIn with valid login credentials", async () => {
    signIn.mockResolvedValue(undefined);
    renderAuthScreen();

    fireEvent.changeText(screen.getByPlaceholderText("نام کاربری"), "learner");
    fireEvent.changeText(screen.getByPlaceholderText("کلمه عبور"), "secret");
    submitLogin();

    await waitFor(() => expect(signIn).toHaveBeenCalledWith("learner", "secret"));
  });
});
