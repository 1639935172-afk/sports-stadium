import '../models/app_user.dart';
import 'api_client.dart';

class SystemUserApi {
  const SystemUserApi(this.client);

  final ApiClient client;

  /// GET /system/users/?q=...
  ///
  /// 系统管理员用户管理列表使用。是否有权限由后端 IsSystemAdmin 判断，
  /// App 端只是根据角色显示入口，真正的安全边界在 Django API。
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

  /// 加载单个用户信息，用于编辑对话框/详情视图。
  Future<AppUser> detail(int id) async {
    final response = await client.dio.get<Map<String, dynamic>>(
      '/system/users/$id/',
    );
    return AppUser.fromJson(response.data ?? <String, dynamic>{});
  }

  /// 系统管理员更新接口。后端会阻止通过此路径编辑当前管理员账号，以避免自我锁定。
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