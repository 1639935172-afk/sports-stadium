import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/api_client.dart';
import '../api/auth_api.dart';
import '../models/app_user.dart';

class AuthState extends ChangeNotifier {
  AuthState({ApiClient? client}) : client = client ?? ApiClient() {
    api = AuthApi(this.client);
  }

  static const _accessKey = 'auth.access';
  static const _refreshKey = 'auth.refresh';
  static const _userKey = 'auth.user';
  static const _rememberedPhoneKey = 'auth.remembered_phone';
  static const _rememberedPasswordKey = 'auth.remembered_password';
  static const _rememberPasswordKey = 'auth.remember_password';

  final ApiClient client;
  late final AuthApi api;

  AppUser? user;
  String? accessToken;
  String? refreshToken;
  String rememberedPhoneNumber = '';
  String rememberedPassword = '';
  bool rememberPassword = false;
  bool isLoading = true;
  String? errorMessage;

  bool get isAuthenticated => user != null && accessToken != null;

  /// App 启动时恢复登录态。
  ///
  /// 流程：从 SharedPreferences 读取本地 token -> 写入 ApiClient 请求头 ->
  /// 调用 /profile/ 向后端确认 token 有效；如果后端拒绝，则清空本地登录态。
  Future<void> restoreSession() async {
    final prefs = await SharedPreferences.getInstance();
    accessToken = prefs.getString(_accessKey);
    refreshToken = prefs.getString(_refreshKey);
    rememberedPhoneNumber = prefs.getString(_rememberedPhoneKey) ?? '';
    rememberedPassword = prefs.getString(_rememberedPasswordKey) ?? '';
    rememberPassword = prefs.getBool(_rememberPasswordKey) ?? false;
    final userJson = prefs.getString(_userKey);
    if (userJson != null) {
      user = AppUser.fromJson(jsonDecode(userJson) as Map<String, dynamic>);
    }
    client.setAccessToken(accessToken);

    if (accessToken != null) {
      try {
        user = await api.profile();
        await _persist();
      } catch (_) {
        await logout();
      }
    }

    isLoading = false;
    notifyListeners();
  }

  /// 登录成功后的关键动作：
  /// 1. 调 AuthApi.login() 获取 JWT；
  /// 2. 保存 access/refresh token 和用户信息；
  /// 3. 设置 Authorization 头，让后续 API 请求自动带身份。
  Future<bool> login(
    String phoneNumber,
    String password, {
    required bool rememberPassword,
  }) async {
    errorMessage = null;
    notifyListeners();
    try {
      final trimmedPhoneNumber = phoneNumber.trim();
      final result = await api.login(
        phoneNumber: trimmedPhoneNumber,
        password: password,
      );
      accessToken = result.access;
      refreshToken = result.refresh;
      user = result.user;
      rememberedPhoneNumber = trimmedPhoneNumber;
      this.rememberPassword = rememberPassword;
      rememberedPassword = rememberPassword ? password : '';
      client.setAccessToken(accessToken);
      await _persist();
      notifyListeners();
      return true;
    } catch (error) {
      errorMessage = _readError(error);
      notifyListeners();
      return false;
    }
  }

  Future<bool> register({
    required String phoneNumber,
    required String nickname,
    required String password1,
    required String password2,
    required String verificationCode,
  }) async {
    errorMessage = null;
    notifyListeners();
    try {
      await api.register(
        phoneNumber: phoneNumber.trim(),
        nickname: nickname.trim(),
        password1: password1,
        password2: password2,
        verificationCode: verificationCode.trim(),
      );
      notifyListeners();
      return true;
    } catch (error) {
      errorMessage = _readError(error);
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessKey);
    await prefs.remove(_refreshKey);
    await prefs.remove(_userKey);
    accessToken = null;
    refreshToken = null;
    user = null;
    client.setAccessToken(null);
    notifyListeners();
  }

  Future<bool> updateProfile({required String nickname}) async {
    errorMessage = null;
    notifyListeners();
    try {
      user = await api.updateProfile(nickname: nickname.trim());
      await _persist();
      notifyListeners();
      return true;
    } catch (error) {
      errorMessage = _readError(error);
      notifyListeners();
      return false;
    }
  }

  Future<bool> changePassword({
    required String oldPassword,
    required String newPassword1,
    required String newPassword2,
  }) async {
    errorMessage = null;
    notifyListeners();
    try {
      user = await api.changePassword(
        oldPassword: oldPassword,
        newPassword1: newPassword1,
        newPassword2: newPassword2,
      );
      await _persist();
      notifyListeners();
      return true;
    } catch (error) {
      errorMessage = _readError(error);
      notifyListeners();
      return false;
    }
  }

  Future<bool> resetPassword({
    required String phoneNumber,
    required String verificationCode,
    required String newPassword1,
    required String newPassword2,
  }) async {
    errorMessage = null;
    notifyListeners();
    try {
      await api.resetPassword(
        phoneNumber: phoneNumber.trim(),
        verificationCode: verificationCode.trim(),
        newPassword1: newPassword1,
        newPassword2: newPassword2,
      );
      notifyListeners();
      return true;
    } catch (error) {
      errorMessage = _readError(error);
      notifyListeners();
      return false;
    }
  }

  Future<bool> cancelAccount({required String password}) async {
    errorMessage = null;
    notifyListeners();
    try {
      await api.cancelAccount(password: password);
      await logout();
      return true;
    } catch (error) {
      errorMessage = _readError(error);
      notifyListeners();
      return false;
    }
  }

  /// 把登录态持久化到本地。这里保存的是 App 会话数据，
  /// 真正的权限判断仍然由后端根据 JWT 和用户角色完成。
  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    if (accessToken != null) {
      await prefs.setString(_accessKey, accessToken!);
    }
    if (refreshToken != null) {
      await prefs.setString(_refreshKey, refreshToken!);
    }
    if (user != null) {
      await prefs.setString(_userKey, jsonEncode(user!.toJson()));
    }
    await prefs.setString(_rememberedPhoneKey, rememberedPhoneNumber);
    await prefs.setBool(_rememberPasswordKey, rememberPassword);
    if (rememberPassword && rememberedPassword.isNotEmpty) {
      await prefs.setString(_rememberedPasswordKey, rememberedPassword);
    } else {
      await prefs.remove(_rememberedPasswordKey);
    }
  }

  String _readError(Object error) {
    if (error is DioException) {
      final data = error.response?.data;
      if (data is Map) {
        return data.entries
            .map((entry) => '${entry.key}: ${_stringify(entry.value)}')
            .join('\n');
      }
      if (data is List) {
        return data.map(_stringify).join('\n');
      }
      if (data is String && data.isNotEmpty) {
        return data;
      }
      if (error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.receiveTimeout) {
        return '连接后端超时，请确认 Django 服务已启动。';
      }
      return '无法连接后端，请确认服务地址和网络。';
    }
    return '操作失败，请稍后重试。';
  }

  String _stringify(Object? value) {
    if (value is List) {
      return value.join('，');
    }
    return value?.toString() ?? '';
  }
}
