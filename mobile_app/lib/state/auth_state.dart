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

  final ApiClient client;
  late final AuthApi api;

  AppUser? user;
  String? accessToken;
  String? refreshToken;
  bool isLoading = true;
  String? errorMessage;

  bool get isAuthenticated => user != null && accessToken != null;

  Future<void> restoreSession() async {
    final prefs = await SharedPreferences.getInstance();
    accessToken = prefs.getString(_accessKey);
    refreshToken = prefs.getString(_refreshKey);
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

  Future<bool> login(String phoneNumber, String password) async {
    errorMessage = null;
    notifyListeners();
    try {
      final result = await api.login(
        phoneNumber: phoneNumber.trim(),
        password: password,
      );
      accessToken = result.access;
      refreshToken = result.refresh;
      user = result.user;
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
