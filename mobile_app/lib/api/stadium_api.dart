import '../models/stadium.dart';
import 'api_client.dart';

class StadiumApi {
  const StadiumApi(this.client);

  final ApiClient client;

  Future<List<Stadium>> list({String query = ''}) async {
    final response = await client.dio.get<List<dynamic>>(
      '/stadiums/',
      queryParameters: query.trim().isEmpty ? null : {'q': query.trim()},
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => Stadium.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<StadiumDetail> detail(int id) async {
    final response = await client.dio.get<Map<String, dynamic>>(
      '/stadiums/$id/',
    );
    return StadiumDetail.fromJson(response.data ?? <String, dynamic>{});
  }
}
