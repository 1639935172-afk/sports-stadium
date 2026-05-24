import 'package:dio/dio.dart';

/// App 端所有 HTTP 请求共用的客户端。
///
/// 答辩时可以这样讲：Flutter 不直接连接 MySQL，而是通过 Dio 访问
/// Django 暴露的 `/api/...` JSON 接口；Android 模拟器访问宿主机本地服务
/// 需要使用 `10.0.2.2`，所以这里统一配置 baseUrl。
class ApiClient {
  ApiClient()
    : dio = Dio(
        BaseOptions(
          baseUrl: 'http://10.0.2.2:8000/api',
          connectTimeout: const Duration(seconds: 8),
          receiveTimeout: const Duration(seconds: 8),
          headers: {'Accept': 'application/json'},
        ),
      );

  final Dio dio;

  /// 登录成功后把 JWT access token 放入 Authorization 请求头。
  ///
  /// 之后 StadiumApi、ReservationApi、CommentApi 等业务 API 复用同一个
  /// ApiClient，所以受保护接口会自动带上 `Bearer <token>`。
  void setAccessToken(String? token) {
    if (token == null || token.isEmpty) {
      dio.options.headers.remove('Authorization');
      return;
    }
    dio.options.headers['Authorization'] = 'Bearer $token';
  }
}
