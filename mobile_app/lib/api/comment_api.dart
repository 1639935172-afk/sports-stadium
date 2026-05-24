import '../models/comment.dart';
import 'api_client.dart';

class CommentApi {
  const CommentApi(this.client);

  final ApiClient client;

  /// GET `/stadiums/<id>/comments/`
  ///
  /// 场馆详情页展示评论时调用；后端只返回已审核通过的评论。
  Future<List<StadiumComment>> listForStadium(int stadiumId) async {
    final response = await client.dio.get<List<dynamic>>(
      '/stadiums/$stadiumId/comments/',
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => StadiumComment.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  /// POST /comments/
  ///
  /// 普通用户提交评论。后端根据 JWT 识别用户，评论初始为 pending，
  /// 需要系统管理员审核后才会出现在公开详情页。
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

  Future<List<StadiumComment>> mine() async {
    final response = await client.dio.get<List<dynamic>>('/comments/mine/');
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => StadiumComment.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<void> deleteMine({required int commentId}) async {
    await client.dio.delete<void>('/comments/mine/$commentId/');
  }

  Future<List<StadiumComment>> adminPending() async {
    final response = await client.dio.get<List<dynamic>>(
      '/comments/admin/pending/',
    );
    final data = response.data ?? <dynamic>[];
    return data
        .map((item) => StadiumComment.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<StadiumComment> approve({required int commentId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/comments/$commentId/approve/',
    );
    return StadiumComment.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<StadiumComment> reject({required int commentId}) async {
    final response = await client.dio.post<Map<String, dynamic>>(
      '/comments/$commentId/reject/',
    );
    return StadiumComment.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<void> delete({required int commentId}) async {
    await client.dio.delete<void>('/comments/$commentId/');
  }
}
