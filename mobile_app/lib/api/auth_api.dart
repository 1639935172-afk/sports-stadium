import '../models/app_user.dart';
import 'api_client.dart';

class LoginResult {
  const LoginResult({
    required this.access,
    required this.refresh,
    required this.user,
  });

  final String access;
  final String refresh;
  final AppUser user;
}

class AuthApi {
  const AuthApi(this.client);

  final ApiClient client;

  Future<LoginResult> login({
    required String phoneNumber,
    required String password,
  }) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/auth/login/',
      data: {'phone_number': phoneNumber, 'password': password},
    );
    final data = response.data ?? <String, dynamic>{};
    return LoginResult(
      access: data['access'] as String,
      refresh: data['refresh'] as String,
      user: AppUser.fromJson(data['user'] as Map<String, dynamic>),
    );
  }

  Future<AppUser> register({
    required String phoneNumber,
    required String nickname,
    required String password1,
    required String password2,
    required String verificationCode,
  }) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/auth/register/',
      data: {
        'phone_number': phoneNumber,
        'nickname': nickname,
        'password1': password1,
        'password2': password2,
        'verification_code': verificationCode,
      },
    );
    final data = response.data ?? <String, dynamic>{};
    return AppUser.fromJson(data['user'] as Map<String, dynamic>);
  }

  Future<AppUser> profile() async {
    final response = await client.dio.get<Map<String, dynamic>>('/profile/');
    return AppUser.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<AppUser> updateProfile({required String nickname}) async {
    final response = await client.dio.patch<Map<String, dynamic>>(
      '/profile/',
      data: {'nickname': nickname},
    );
    return AppUser.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<AppUser> changePassword({
    required String oldPassword,
    required String newPassword1,
    required String newPassword2,
  }) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/password/change/',
      data: {
        'old_password': oldPassword,
        'new_password1': newPassword1,
        'new_password2': newPassword2,
      },
    );
    return AppUser.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<AppUser> resetPassword({
    required String phoneNumber,
    required String verificationCode,
    required String newPassword1,
    required String newPassword2,
  }) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/password/reset/',
      data: {
        'phone_number': phoneNumber,
        'verification_code': verificationCode,
        'new_password1': newPassword1,
        'new_password2': newPassword2,
      },
    );
    return AppUser.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<AppUser> cancelAccount({required String password}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/account/cancel/',
      data: {'password': password},
    );
    return AppUser.fromJson(response.data ?? <String, dynamic>{});
  }
}
