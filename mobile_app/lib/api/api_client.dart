import 'package:dio/dio.dart';

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

  void setAccessToken(String? token) {
    if (token == null || token.isEmpty) {
      dio.options.headers.remove('Authorization');
      return;
    }
    dio.options.headers['Authorization'] = 'Bearer $token';
  }
}
