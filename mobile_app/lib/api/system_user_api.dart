import '../models/app_user.dart';
import 'api_client.dart';

class SystemUserApi {
  const SystemUserApi(this.client);

  final ApiClient client;

  Future<List<AppUser>> list({String query = ''}) async {
    final response = await client.dio.get<List<dynamic>>(
      '/system/users/',
      queryParameters: query.trim().isEmpty ? null : {'q': query.trim()},
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => AppUser.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<AppUser> detail(int id) async {
    final response = await client.dio.get<Map<String, dynamic>>(
      '/system/users/$id/',
    );
    return AppUser.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<AppUser> update({
    required int id,
    required String nickname,
    required String role,
    required bool isActive,
    required bool isCancelled,
  }) async {
    final response = await client.dio.patch<Map<String, dynamic>>(
      '/system/users/$id/',
      data: {
        'nickname': nickname,
        'role': role,
        'is_active': isActive,
        'is_cancelled': isCancelled,
      },
    );
    return AppUser.fromJson(response.data ?? <String, dynamic>{});
  }
}
