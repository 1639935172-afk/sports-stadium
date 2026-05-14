import '../models/comment.dart';
import 'api_client.dart';

class CommentApi {
  const CommentApi(this.client);

  final ApiClient client;

  Future<List<StadiumComment>> listForStadium(int stadiumId) async {
    final response = await client.dio.get<List<dynamic>>(
      '/stadiums/$stadiumId/comments/',
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => StadiumComment.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<CommentCreateResult> create({
    required int stadiumId,
    required String content,
  }) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/comments/',
      data: {'stadium': stadiumId, 'content': content},
    );
    return CommentCreateResult.fromJson(response.data ?? <String, dynamic>{});
  }
}
